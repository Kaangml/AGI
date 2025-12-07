"""
EVO-TR: Preference Learning System

Direct Preference Optimization (DPO) yaklaşımı ile tercih öğrenimi.
Kullanıcı tercihlerinden model davranışını iyileştirir.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum


class PreferenceSource(Enum):
    """Tercih kaynağı."""
    USER_FEEDBACK = "user_feedback"      # Kullanıcı 👍/👎
    USER_EDIT = "user_edit"               # Kullanıcı düzeltmesi
    A_B_TEST = "ab_test"                  # A/B test sonucu
    HUMAN_ANNOTATION = "human_annotation" # İnsan etiketlemesi
    AUTOMATED = "automated"               # Otomatik değerlendirme


@dataclass
class PreferencePair:
    """
    Tercih çifti - DPO eğitimi için.
    
    chosen: Tercih edilen yanıt
    rejected: Tercih edilmeyen yanıt
    """
    id: str
    prompt: str
    chosen: str           # Tercih edilen yanıt
    rejected: str         # Tercih edilmeyen yanıt
    source: str           # PreferenceSource value
    margin: float         # Tercih marjı (ne kadar daha iyi)
    adapter: str          # Hangi adapter için
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dpo_format(self) -> Dict[str, Any]:
        """DPO eğitim formatına çevir."""
        return {
            "prompt": self.prompt,
            "chosen": self.chosen,
            "rejected": self.rejected
        }


class PreferenceCollector:
    """
    Tercih verisi toplama.
    
    Feedback'lerden ve düzeltmelerden tercih çiftleri oluşturur.
    """
    
    def __init__(self, storage_path: str = "./data/preferences"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.preferences: List[PreferencePair] = []
        
        print(f"✅ PreferenceCollector hazır | Storage: {self.storage_path}")
    
    def create_from_feedback(
        self,
        prompt: str,
        response: str,
        feedback_type: str,
        adapter: str,
        corrected_response: Optional[str] = None
    ) -> Optional[PreferencePair]:
        """
        Feedback'den tercih çifti oluştur.
        
        thumbs_up: response = chosen (rejected yok, atlayabiliriz veya base ile karşılaştır)
        thumbs_down: response = rejected (chosen = corrected_response veya atlayabiliriz)
        edit: original = rejected, corrected = chosen
        """
        if feedback_type == "edit" and corrected_response:
            # En değerli: Kullanıcı düzeltmesi var
            pair = PreferencePair(
                id=self._generate_id(),
                prompt=prompt,
                chosen=corrected_response,
                rejected=response,
                source=PreferenceSource.USER_EDIT.value,
                margin=1.0,  # Kullanıcı düzeltmesi en güçlü sinyal
                adapter=adapter,
                timestamp=datetime.now().isoformat(),
                metadata={"original_feedback_type": feedback_type}
            )
            self.preferences.append(pair)
            return pair
        
        elif feedback_type == "thumbs_down":
            # Negatif feedback - rejected yanıtı var ama chosen yok
            # Bu durumda eğer düzeltme yoksa sadece kaydet, eğitim için kullanamayız
            # Ama gelecekte karşılaştırma için kullanılabilir
            if corrected_response:
                pair = PreferencePair(
                    id=self._generate_id(),
                    prompt=prompt,
                    chosen=corrected_response,
                    rejected=response,
                    source=PreferenceSource.USER_FEEDBACK.value,
                    margin=0.8,
                    adapter=adapter,
                    timestamp=datetime.now().isoformat()
                )
                self.preferences.append(pair)
                return pair
        
        # thumbs_up durumunda sadece pozitif örnek var, DPO için yeterli değil
        return None
    
    def create_from_ab_test(
        self,
        prompt: str,
        response_a: str,
        response_b: str,
        preferred: str,  # "a" veya "b"
        adapter: str
    ) -> PreferencePair:
        """A/B test sonucundan tercih çifti oluştur."""
        if preferred == "a":
            chosen, rejected = response_a, response_b
        else:
            chosen, rejected = response_b, response_a
        
        pair = PreferencePair(
            id=self._generate_id(),
            prompt=prompt,
            chosen=chosen,
            rejected=rejected,
            source=PreferenceSource.A_B_TEST.value,
            margin=0.7,
            adapter=adapter,
            timestamp=datetime.now().isoformat()
        )
        self.preferences.append(pair)
        return pair
    
    def create_from_multiple_responses(
        self,
        prompt: str,
        responses: List[str],
        scores: List[float],
        adapter: str
    ) -> List[PreferencePair]:
        """
        Birden fazla yanıt ve skorlarından tercih çiftleri oluştur.
        En iyi vs geri kalan hepsi için çiftler.
        """
        if len(responses) < 2:
            return []
        
        # Score'a göre sırala
        sorted_pairs = sorted(zip(responses, scores), key=lambda x: x[1], reverse=True)
        pairs = []
        
        best_response, best_score = sorted_pairs[0]
        
        for resp, score in sorted_pairs[1:]:
            margin = (best_score - score) / best_score if best_score > 0 else 0.5
            
            pair = PreferencePair(
                id=self._generate_id(),
                prompt=prompt,
                chosen=best_response,
                rejected=resp,
                source=PreferenceSource.AUTOMATED.value,
                margin=margin,
                adapter=adapter,
                timestamp=datetime.now().isoformat()
            )
            self.preferences.append(pair)
            pairs.append(pair)
        
        return pairs
    
    def _generate_id(self) -> str:
        """Unique ID oluştur."""
        return f"pref_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.preferences):04d}"
    
    def get_preferences_by_adapter(self, adapter: str) -> List[PreferencePair]:
        """Adapter'a göre tercih çiftlerini al."""
        return [p for p in self.preferences if p.adapter == adapter]
    
    def export_for_dpo(
        self,
        adapter: Optional[str] = None,
        min_pairs: int = 10
    ) -> Optional[Path]:
        """DPO eğitimi için dışa aktar."""
        pairs = self.preferences if adapter is None else self.get_preferences_by_adapter(adapter)
        
        if len(pairs) < min_pairs:
            print(f"⚠️ Yeterli tercih çifti yok: {len(pairs)}/{min_pairs}")
            return None
        
        filename = f"dpo_{adapter or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        filepath = self.storage_path / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            for pair in pairs:
                f.write(json.dumps(pair.to_dpo_format(), ensure_ascii=False) + "\n")
        
        print(f"✅ DPO verisi dışa aktarıldı: {len(pairs)} çift -> {filepath}")
        return filepath
    
    def get_statistics(self) -> Dict[str, Any]:
        """İstatistikler."""
        total = len(self.preferences)
        if total == 0:
            return {"total": 0, "message": "Henüz tercih verisi yok"}
        
        # Kaynak dağılımı
        by_source = {}
        for p in self.preferences:
            by_source[p.source] = by_source.get(p.source, 0) + 1
        
        # Adapter dağılımı
        by_adapter = {}
        for p in self.preferences:
            by_adapter[p.adapter] = by_adapter.get(p.adapter, 0) + 1
        
        # Ortalama marj
        avg_margin = sum(p.margin for p in self.preferences) / total
        
        return {
            "total": total,
            "by_source": by_source,
            "by_adapter": by_adapter,
            "avg_margin": round(avg_margin, 3),
            "ready_for_dpo": total >= 10
        }


class DPOTrainer:
    """
    Direct Preference Optimization Trainer.
    
    NOT: Gerçek DPO eğitimi için özel bir kütüphane gerekir.
    Bu sınıf eğitim sürecini yönetir ve MLX ile entegre olur.
    """
    
    def __init__(
        self,
        base_model_path: str = "./models/base/qwen-2.5-3b-instruct",
        adapters_dir: str = "./adapters",
        output_dir: str = "./adapters/dpo_trained"
    ):
        self.base_model_path = Path(base_model_path)
        self.adapters_dir = Path(adapters_dir)
        self.output_dir = Path(output_dir)
        
        self.training_history: List[Dict[str, Any]] = []
        
        print(f"✅ DPOTrainer hazır")
        print(f"   Base model: {self.base_model_path}")
        print(f"   Output: {self.output_dir}")
    
    def prepare_dpo_config(
        self,
        adapter_name: str,
        training_data_path: Path,
        beta: float = 0.1,
        learning_rate: float = 5e-6,
        epochs: int = 1
    ) -> Dict[str, Any]:
        """DPO eğitim konfigürasyonu hazırla."""
        config = {
            "model": str(self.base_model_path),
            "adapter_path": str(self.adapters_dir / adapter_name),
            "data": str(training_data_path),
            "method": "dpo",
            "beta": beta,  # DPO beta parametresi (tercih gücü)
            "learning_rate": learning_rate,
            "epochs": epochs,
            "lora_layers": 8,
            "batch_size": 1,
            "output_dir": str(self.output_dir / adapter_name)
        }
        return config
    
    def estimate_training_time(
        self,
        num_pairs: int,
        epochs: int = 1
    ) -> Dict[str, Any]:
        """Eğitim süresini tahmin et."""
        # Tahmini: ~2 saniye/örnek (Apple Silicon M4 için)
        seconds_per_pair = 2
        total_seconds = num_pairs * epochs * seconds_per_pair
        
        return {
            "pairs": num_pairs,
            "epochs": epochs,
            "estimated_seconds": total_seconds,
            "estimated_minutes": round(total_seconds / 60, 1),
            "note": "Tahmini süre, gerçek süre donanıma göre değişebilir"
        }
    
    def run_dpo_training(
        self,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        DPO eğitimi çalıştır.
        
        NOT: Gerçek implementasyonda mlx_lm veya özel DPO kütüphanesi kullanılır.
        Bu simülasyon eğitim sürecini gösterir.
        """
        result = {
            "success": False,
            "adapter": config.get("adapter_path", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            print(f"🔄 DPO Training başlıyor...")
            print(f"   Config: {json.dumps(config, indent=2)}")
            
            # Simülasyon: Gerçek eğitim burada yapılır
            # mlx_lm şu an doğrudan DPO desteklemiyor
            # Alternatif: TRL kütüphanesi veya custom implementation
            
            result["success"] = True
            result["metrics"] = {
                "preference_accuracy": 0.85,  # Simüle
                "loss": 0.3,
                "epochs_completed": config.get("epochs", 1)
            }
            
            self.training_history.append(result)
            print(f"✅ DPO Training tamamlandı (simülasyon)")
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ DPO Training başarısız: {e}")
        
        return result
    
    def get_training_history(self) -> List[Dict[str, Any]]:
        """Eğitim geçmişi."""
        return self.training_history


class PreferenceLearningPipeline:
    """
    End-to-end Preference Learning Pipeline.
    
    Feedback toplama -> Tercih çifti oluşturma -> DPO eğitimi
    """
    
    def __init__(
        self,
        min_pairs_for_training: int = 10,
        auto_train: bool = False
    ):
        self.collector = PreferenceCollector()
        self.trainer = DPOTrainer()
        
        self.min_pairs = min_pairs_for_training
        self.auto_train = auto_train
        
        print(f"✅ PreferenceLearningPipeline hazır")
        print(f"   Min pairs: {min_pairs_for_training}")
        print(f"   Auto train: {auto_train}")
    
    def process_feedback(
        self,
        prompt: str,
        response: str,
        feedback_type: str,
        adapter: str,
        corrected_response: Optional[str] = None
    ) -> Optional[PreferencePair]:
        """Feedback'i işle ve tercih çifti oluştur."""
        pair = self.collector.create_from_feedback(
            prompt=prompt,
            response=response,
            feedback_type=feedback_type,
            adapter=adapter,
            corrected_response=corrected_response
        )
        
        # Otomatik eğitim kontrolü
        if self.auto_train and pair:
            self._check_and_trigger_training(adapter)
        
        return pair
    
    def _check_and_trigger_training(self, adapter: str):
        """Eğitim tetiklenmeli mi kontrol et."""
        pairs = self.collector.get_preferences_by_adapter(adapter)
        if len(pairs) >= self.min_pairs:
            print(f"🎯 Otomatik DPO eğitimi tetiklendi: {adapter} ({len(pairs)} çift)")
            # self.run_training(adapter)  # Aktif değil
    
    def run_training(self, adapter: str) -> Dict[str, Any]:
        """DPO eğitimi çalıştır."""
        # Veri dışa aktar
        data_path = self.collector.export_for_dpo(
            adapter=adapter,
            min_pairs=self.min_pairs
        )
        
        if not data_path:
            return {"success": False, "error": "Yeterli veri yok"}
        
        # Config oluştur
        config = self.trainer.prepare_dpo_config(
            adapter_name=adapter,
            training_data_path=data_path
        )
        
        # Eğitimi çalıştır
        result = self.trainer.run_dpo_training(config)
        return result
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Pipeline durumu."""
        collector_stats = self.collector.get_statistics()
        
        return {
            "preference_stats": collector_stats,
            "training_history": len(self.trainer.get_training_history()),
            "auto_train_enabled": self.auto_train,
            "min_pairs_threshold": self.min_pairs
        }


# Test
if __name__ == "__main__":
    print("=" * 50)
    print("Preference Learning Test")
    print("=" * 50)
    
    # Collector test
    collector = PreferenceCollector(storage_path="./data/test_preferences")
    
    # Test 1: Edit feedback'den tercih çifti
    print("\n1. Edit feedback'den tercih çifti:")
    pair = collector.create_from_feedback(
        prompt="Python'da liste nasıl oluşturulur?",
        response="list = []",
        feedback_type="edit",
        adapter="python_coder",
        corrected_response="Python'da liste oluşturmak için köşeli parantez kullanılır:\n\nmy_list = []  # Boş liste\nmy_list = [1, 2, 3]  # Değerlerle"
    )
    print(f"   Çift oluşturuldu: {pair is not None}")
    if pair:
        print(f"   Kaynak: {pair.source}")
        print(f"   Marj: {pair.margin}")
    
    # Test 2: A/B test
    print("\n2. A/B test'den tercih çifti:")
    pair = collector.create_from_ab_test(
        prompt="Döngü nasıl yazılır?",
        response_a="for i in range(10): print(i)",
        response_b="for döngüsü kullanabilirsin",
        preferred="a",
        adapter="python_coder"
    )
    print(f"   Çift oluşturuldu: {pair is not None}")
    
    # Test 3: Çoklu yanıt skorlaması
    print("\n3. Çoklu yanıt skorlamasından tercih çiftleri:")
    pairs = collector.create_from_multiple_responses(
        prompt="Fonksiyon nedir?",
        responses=[
            "Fonksiyon, kod bloğudur.",
            "def my_func(): pass",
            "Fonksiyon, belirli bir görevi yerine getiren, tekrar kullanılabilir kod bloğudur. Python'da def anahtar kelimesiyle tanımlanır."
        ],
        scores=[0.3, 0.5, 0.95],
        adapter="python_coder"
    )
    print(f"   Oluşturulan çift sayısı: {len(pairs)}")
    
    # İstatistikler
    print("\n📊 İstatistikler:")
    stats = collector.get_statistics()
    print(f"   Toplam: {stats['total']}")
    print(f"   Kaynak dağılımı: {stats['by_source']}")
    print(f"   DPO için hazır: {stats['ready_for_dpo']}")
    
    # Pipeline test
    print("\n" + "=" * 50)
    print("Preference Learning Pipeline Test")
    print("=" * 50)
    
    pipeline = PreferenceLearningPipeline(min_pairs_for_training=3)
    
    # Feedback işle
    pipeline.process_feedback(
        prompt="Test prompt",
        response="Kötü yanıt",
        feedback_type="edit",
        adapter="tr_chat",
        corrected_response="İyi yanıt"
    )
    
    # Durum
    print("\nPipeline durumu:")
    status = pipeline.get_pipeline_status()
    print(f"   Tercih sayısı: {status['preference_stats']['total']}")
    print(f"   Eğitim geçmişi: {status['training_history']}")
    
    # DPO Trainer test
    print("\n" + "=" * 50)
    print("DPO Trainer Test")
    print("=" * 50)
    
    trainer = DPOTrainer()
    
    # Süre tahmini
    print("\nEğitim süresi tahmini:")
    estimate = trainer.estimate_training_time(num_pairs=50, epochs=2)
    print(f"   50 çift, 2 epoch: ~{estimate['estimated_minutes']} dakika")
    
    print("\n✅ Test tamamlandı!")
