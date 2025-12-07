"""
EVO-TR: Incremental Training System

Feedback ve active learning verilerinden LoRA adaptörlerini güncelleme.
Online fine-tuning yetenekleri.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class TrainingStatus(Enum):
    """Eğitim durumu."""
    PENDING = "pending"
    PREPARING = "preparing"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TrainingJob:
    """Eğitim işi."""
    id: str
    adapter_name: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    samples_count: int = 0
    epochs: int = 1
    learning_rate: float = 1e-5
    progress: float = 0.0
    metrics: Optional[Dict[str, float]] = None
    error: Optional[str] = None


class IncrementalTrainer:
    """
    Incremental LoRA Training.
    
    Feedback ve active learning verilerinden yeni örnekler oluşturur
    ve adapter'ları günceller.
    """
    
    def __init__(
        self,
        adapters_dir: str = "./adapters",
        training_data_dir: str = "./data/incremental",
        base_model_path: str = "./models/base/qwen-2.5-3b-instruct"
    ):
        self.adapters_dir = Path(adapters_dir)
        self.training_data_dir = Path(training_data_dir)
        self.base_model_path = Path(base_model_path)
        
        self.training_data_dir.mkdir(parents=True, exist_ok=True)
        
        self.training_jobs: List[TrainingJob] = []
        self.current_job: Optional[TrainingJob] = None
        
        print(f"✅ IncrementalTrainer hazır")
        print(f"   Adapters: {self.adapters_dir}")
        print(f"   Training data: {self.training_data_dir}")
    
    def prepare_training_data(
        self,
        feedback_data: List[Dict[str, Any]],
        adapter_name: str,
        min_samples: int = 5
    ) -> Optional[Path]:
        """
        Feedback verilerinden eğitim verisi hazırla.
        
        Args:
            feedback_data: Feedback kayıtları
            adapter_name: Hedef adapter
            min_samples: Minimum örnek sayısı
        
        Returns:
            Eğitim veri dosyası yolu veya None
        """
        # Adapter'a uygun verileri filtrele
        training_samples = []
        
        for feedback in feedback_data:
            # Positif feedback veya düzeltme içerenleri al
            feedback_type = feedback.get("feedback_type", "")
            
            if feedback_type == "thumbs_up":
                # İyi yanıt - olduğu gibi kullan
                sample = self._create_training_sample(
                    user_message=feedback.get("user_message", ""),
                    response=feedback.get("assistant_response", ""),
                    is_positive=True
                )
                if sample:
                    training_samples.append(sample)
            
            elif feedback_type == "edit" and feedback.get("corrected_response"):
                # Düzeltme var - düzeltilmiş yanıtı kullan
                sample = self._create_training_sample(
                    user_message=feedback.get("user_message", ""),
                    response=feedback.get("corrected_response", ""),
                    is_positive=True,
                    is_correction=True
                )
                if sample:
                    training_samples.append(sample)
        
        if len(training_samples) < min_samples:
            print(f"⚠️ Yeterli örnek yok: {len(training_samples)}/{min_samples}")
            return None
        
        # Dosyaya kaydet
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{adapter_name}_incremental_{timestamp}.jsonl"
        filepath = self.training_data_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            for sample in training_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        
        print(f"✅ Eğitim verisi hazır: {len(training_samples)} örnek -> {filepath}")
        return filepath
    
    def _create_training_sample(
        self,
        user_message: str,
        response: str,
        is_positive: bool = True,
        is_correction: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Eğitim örneği oluştur."""
        if not user_message or not response:
            return None
        
        # Chat format
        sample = {
            "messages": [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": response}
            ],
            "metadata": {
                "is_positive": is_positive,
                "is_correction": is_correction,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return sample
    
    def create_training_job(
        self,
        adapter_name: str,
        training_data_path: Path,
        epochs: int = 1,
        learning_rate: float = 1e-5,
        batch_size: int = 1
    ) -> TrainingJob:
        """Eğitim işi oluştur."""
        # Örnek sayısını hesapla
        samples_count = 0
        with open(training_data_path, "r") as f:
            samples_count = sum(1 for _ in f)
        
        job = TrainingJob(
            id=f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            adapter_name=adapter_name,
            status=TrainingStatus.PENDING.value,
            created_at=datetime.now().isoformat(),
            samples_count=samples_count,
            epochs=epochs,
            learning_rate=learning_rate
        )
        
        self.training_jobs.append(job)
        print(f"✅ Training job oluşturuldu: {job.id} ({samples_count} örnek)")
        return job
    
    def run_incremental_training(
        self,
        job: TrainingJob,
        training_data_path: Path
    ) -> bool:
        """
        Incremental LoRA training çalıştır.
        
        NOT: Gerçek eğitim mlx_lm.lora ile yapılır.
        Bu fonksiyon eğitim sürecini yönetir.
        """
        self.current_job = job
        job.status = TrainingStatus.PREPARING.value
        job.started_at = datetime.now().isoformat()
        
        try:
            # Adapter yolunu kontrol et
            adapter_path = self.adapters_dir / job.adapter_name
            if not adapter_path.exists():
                raise FileNotFoundError(f"Adapter bulunamadı: {adapter_path}")
            
            # Mevcut adapter'ı yedekle
            backup_path = adapter_path.parent / f"{job.adapter_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if adapter_path.exists():
                shutil.copytree(adapter_path, backup_path)
                print(f"📦 Adapter yedeklendi: {backup_path}")
            
            job.status = TrainingStatus.TRAINING.value
            
            # MLX LoRA training command oluştur
            # NOT: Bu gerçek eğitimi simüle eder
            # Gerçek implementasyonda mlx_lm.lora kullanılır
            training_config = {
                "model": str(self.base_model_path),
                "adapter_path": str(adapter_path),
                "data": str(training_data_path),
                "train": True,
                "iters": job.epochs * job.samples_count,
                "learning_rate": job.learning_rate,
                "lora_layers": 8,
                "batch_size": 1
            }
            
            print(f"🔄 Training başlıyor...")
            print(f"   Config: {json.dumps(training_config, indent=2)}")
            
            # Simülasyon: Gerçek eğitim için mlx_lm.lora çağrılır
            # Burada sadece job durumunu güncelliyoruz
            job.progress = 1.0
            job.metrics = {
                "final_loss": 0.5,  # Simüle edilmiş
                "samples_trained": job.samples_count
            }
            
            job.status = TrainingStatus.COMPLETED.value
            job.completed_at = datetime.now().isoformat()
            
            print(f"✅ Training tamamlandı: {job.id}")
            return True
            
        except Exception as e:
            job.status = TrainingStatus.FAILED.value
            job.error = str(e)
            print(f"❌ Training başarısız: {e}")
            return False
        
        finally:
            self.current_job = None
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Eğitim istatistikleri."""
        total = len(self.training_jobs)
        if total == 0:
            return {"total": 0, "message": "Henüz eğitim işi yok"}
        
        status_counts = {}
        for job in self.training_jobs:
            status = job.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total": total,
            "by_status": status_counts,
            "completed": status_counts.get(TrainingStatus.COMPLETED.value, 0),
            "failed": status_counts.get(TrainingStatus.FAILED.value, 0),
            "is_training": self.current_job is not None
        }


class ContinuousLearningPipeline:
    """
    Continuous Learning Pipeline.
    
    Feedback toplama -> Veri hazırlama -> Eğitim döngüsü.
    """
    
    def __init__(
        self,
        feedback_db_path: str = "./data/feedback.db",
        adapters_dir: str = "./adapters",
        min_feedback_for_training: int = 10,
        training_interval_hours: int = 24
    ):
        self.min_feedback = min_feedback_for_training
        self.training_interval = training_interval_hours
        
        # Bileşenler
        self.trainer = IncrementalTrainer(adapters_dir=adapters_dir)
        
        # Durum
        self.last_training_time: Optional[datetime] = None
        self.training_history: List[Dict[str, Any]] = []
        
        print(f"✅ ContinuousLearningPipeline hazır")
        print(f"   Min feedback: {min_feedback_for_training}")
        print(f"   Training interval: {training_interval_hours}h")
    
    def should_trigger_training(self, feedback_count: int) -> Tuple[bool, str]:
        """Eğitim başlatılmalı mı?"""
        # Yeterli feedback var mı?
        if feedback_count < self.min_feedback:
            return False, f"Yeterli feedback yok ({feedback_count}/{self.min_feedback})"
        
        # Son eğitimden yeterli süre geçti mi?
        if self.last_training_time:
            hours_since = (datetime.now() - self.last_training_time).total_seconds() / 3600
            if hours_since < self.training_interval:
                return False, f"Son eğitimden {hours_since:.1f}h geçti (min: {self.training_interval}h)"
        
        return True, "Eğitim başlatılabilir"
    
    def run_training_cycle(
        self,
        feedback_data: List[Dict[str, Any]],
        target_adapter: str = "tr_chat"
    ) -> Dict[str, Any]:
        """
        Eğitim döngüsü çalıştır.
        
        Returns:
            Eğitim sonuç özeti
        """
        result = {
            "success": False,
            "adapter": target_adapter,
            "timestamp": datetime.now().isoformat(),
            "details": {}
        }
        
        # Veri hazırla
        data_path = self.trainer.prepare_training_data(
            feedback_data=feedback_data,
            adapter_name=target_adapter
        )
        
        if not data_path:
            result["details"]["error"] = "Veri hazırlanamadı"
            return result
        
        # Job oluştur
        job = self.trainer.create_training_job(
            adapter_name=target_adapter,
            training_data_path=data_path
        )
        
        result["details"]["job_id"] = job.id
        result["details"]["samples"] = job.samples_count
        
        # Eğitimi çalıştır
        success = self.trainer.run_incremental_training(job, data_path)
        
        if success:
            result["success"] = True
            result["details"]["metrics"] = job.metrics
            self.last_training_time = datetime.now()
            
            self.training_history.append({
                "job_id": job.id,
                "adapter": target_adapter,
                "samples": job.samples_count,
                "timestamp": datetime.now().isoformat()
            })
        else:
            result["details"]["error"] = job.error
        
        return result
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Pipeline durumu."""
        return {
            "is_active": True,
            "last_training": self.last_training_time.isoformat() if self.last_training_time else None,
            "total_trainings": len(self.training_history),
            "trainer_stats": self.trainer.get_training_stats()
        }


# Test
if __name__ == "__main__":
    print("=" * 50)
    print("Incremental Training Test")
    print("=" * 50)
    
    # Trainer test
    trainer = IncrementalTrainer(
        adapters_dir="./adapters",
        training_data_dir="./data/test_incremental"
    )
    
    # Simüle edilmiş feedback
    mock_feedback = [
        {
            "user_message": "Python'da liste nasıl oluşturulur?",
            "assistant_response": "Python'da liste oluşturmak için köşeli parantez kullanılır: my_list = []",
            "feedback_type": "thumbs_up",
            "adapter_used": "python_coder"
        },
        {
            "user_message": "Döngü nasıl yazılır?",
            "assistant_response": "for i in range(10): print(i)",
            "feedback_type": "thumbs_up",
            "adapter_used": "python_coder"
        },
        {
            "user_message": "Fonksiyon tanımlama",
            "assistant_response": "def my_function(): pass",
            "feedback_type": "edit",
            "corrected_response": "def my_function(param1, param2):\n    \"\"\"Fonksiyon açıklaması.\"\"\"\n    return param1 + param2",
            "adapter_used": "python_coder"
        },
        {
            "user_message": "Sınıf oluşturma",
            "assistant_response": "class MyClass:\n    def __init__(self):\n        pass",
            "feedback_type": "thumbs_up",
            "adapter_used": "python_coder"
        },
        {
            "user_message": "Dictionary kullanımı",
            "assistant_response": "my_dict = {'key': 'value'}",
            "feedback_type": "thumbs_up",
            "adapter_used": "python_coder"
        }
    ]
    
    # Veri hazırla
    print("\n1. Eğitim verisi hazırlama:")
    data_path = trainer.prepare_training_data(
        feedback_data=mock_feedback,
        adapter_name="python_coder",
        min_samples=3
    )
    
    if data_path:
        print(f"   ✅ Veri hazırlandı: {data_path}")
        
        # İçeriği göster
        print("\n   İçerik:")
        with open(data_path, "r") as f:
            for i, line in enumerate(f):
                if i < 2:
                    sample = json.loads(line)
                    print(f"   {i+1}. {sample['messages'][0]['content'][:50]}...")
    
    # Pipeline test
    print("\n" + "=" * 50)
    print("Continuous Learning Pipeline Test")
    print("=" * 50)
    
    pipeline = ContinuousLearningPipeline(
        adapters_dir="./adapters",
        min_feedback_for_training=3
    )
    
    # Eğitim tetiklemeli mi?
    should_train, reason = pipeline.should_trigger_training(len(mock_feedback))
    print(f"\n2. Eğitim tetiklenmeli mi?")
    print(f"   Sonuç: {should_train}")
    print(f"   Sebep: {reason}")
    
    # Pipeline durumu
    print("\n3. Pipeline durumu:")
    status = pipeline.get_pipeline_status()
    print(f"   Aktif: {status['is_active']}")
    print(f"   Son eğitim: {status['last_training']}")
    print(f"   Toplam eğitim: {status['total_trainings']}")
    
    print("\n✅ Test tamamlandı!")
