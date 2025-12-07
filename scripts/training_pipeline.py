#!/usr/bin/env python3
"""
EVO-TR: Unified Training Pipeline

İki ayrı eğitim stratejisi:
1. SFT (Supervised Fine-Tuning) - Düzeltmelerden öğrenme
2. DPO (Direct Preference Optimization) - Tercihlerden öğrenme

SFT: Correction (✏️) → Doğru cevabı öğren
DPO: 👍/👎 pairs → Tercih edilen vs reddedilen cevapları karşılaştır

Kullanım:
    python scripts/training_pipeline.py status      # Durum
    python scripts/training_pipeline.py prepare     # Veri hazırla
    python scripts/training_pipeline.py train-sft   # SFT eğitimi
    python scripts/training_pipeline.py train-dpo   # DPO eğitimi
    python scripts/training_pipeline.py train-all   # Her ikisi
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

sys.path.insert(0, ".")

from src.lifecycle.feedback import FeedbackDatabase, FeedbackEntry


@dataclass
class TrainingCandidate:
    """Eğitim adayı."""
    type: str  # "sft" veya "dpo"
    prompt: str
    chosen: str
    rejected: Optional[str] = None
    adapter: str = ""
    source_ids: List[str] = None


class TrainingPipeline:
    """Unified Training Pipeline."""
    
    def __init__(self, db_path: str = "./data/feedback.db"):
        self.db = FeedbackDatabase(db_path)
        self.output_dir = Path("./data/training/pipeline")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Eşikler
        self.sft_threshold = 5   # Minimum correction sayısı
        self.dpo_threshold = 10  # Minimum DPO pair sayısı
    
    def get_status(self) -> Dict[str, Any]:
        """Mevcut durumu analiz et."""
        import sqlite3
        conn = sqlite3.connect(str(self.db.db_path))
        cursor = conn.cursor()
        
        # Genel istatistikler
        cursor.execute("SELECT COUNT(*) FROM feedback")
        total = cursor.fetchone()[0]
        
        # Türe göre
        cursor.execute("""
            SELECT feedback_type, COUNT(*) 
            FROM feedback 
            GROUP BY feedback_type
        """)
        by_type = dict(cursor.fetchall())
        
        # Correction olanlar (SFT için)
        cursor.execute("""
            SELECT COUNT(*) FROM feedback 
            WHERE corrected_response IS NOT NULL 
            AND corrected_response != ''
            AND used_for_training = 0
        """)
        sft_candidates = cursor.fetchone()[0]
        
        # Thumbs up/down (DPO için)
        cursor.execute("""
            SELECT COUNT(*) FROM feedback 
            WHERE feedback_type IN ('thumbs_up', 'thumbs_down')
            AND used_for_training = 0
        """)
        preference_count = cursor.fetchone()[0]
        
        # DPO pair potansiyeli - aynı intent için + ve - var mı?
        cursor.execute("""
            SELECT intent, 
                   SUM(CASE WHEN feedback_type = 'thumbs_up' THEN 1 ELSE 0 END) as pos,
                   SUM(CASE WHEN feedback_type = 'thumbs_down' THEN 1 ELSE 0 END) as neg
            FROM feedback 
            WHERE feedback_type IN ('thumbs_up', 'thumbs_down')
            AND used_for_training = 0
            GROUP BY intent
            HAVING pos > 0 AND neg > 0
        """)
        dpo_intents = cursor.fetchall()
        
        conn.close()
        
        return {
            "total_feedback": total,
            "by_type": by_type,
            "sft": {
                "candidates": sft_candidates,
                "threshold": self.sft_threshold,
                "ready": sft_candidates >= self.sft_threshold
            },
            "dpo": {
                "preference_count": preference_count,
                "intents_with_pairs": len(dpo_intents),
                "threshold": self.dpo_threshold,
                "ready": preference_count >= self.dpo_threshold and len(dpo_intents) > 0
            }
        }
    
    def prepare_sft_data(self) -> Optional[Path]:
        """
        SFT için eğitim verisi hazırla.
        Düzeltmelerden öğrenme - doğru cevapları kullan.
        """
        corrections = self.db.get_corrected_responses(limit=100)
        
        if len(corrections) < self.sft_threshold:
            print(f"⚠️ SFT için yeterli düzeltme yok: {len(corrections)}/{self.sft_threshold}")
            return None
        
        samples = []
        source_ids = []
        
        for entry in corrections:
            if not entry.corrected_response or not entry.user_message:
                continue
            
            # MLX chat format
            sample = {
                "messages": [
                    {"role": "user", "content": entry.user_message},
                    {"role": "assistant", "content": entry.corrected_response}
                ]
            }
            samples.append(sample)
            source_ids.append(entry.id)
        
        if not samples:
            print("⚠️ Geçerli SFT örneği bulunamadı")
            return None
        
        # Kaydet
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"sft_corrections_{timestamp}.jsonl"
        
        with open(output_file, "w", encoding="utf-8") as f:
            for sample in samples:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        
        # Train/valid split için valid.jsonl oluştur
        valid_file = self.output_dir / "valid.jsonl"
        if len(samples) > 5:
            valid_samples = samples[-2:]  # Son 2 örnek validation
            train_samples = samples[:-2]
            
            with open(self.output_dir / "train.jsonl", "w", encoding="utf-8") as f:
                for sample in train_samples:
                    f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            
            with open(valid_file, "w", encoding="utf-8") as f:
                for sample in valid_samples:
                    f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        
        print(f"✅ SFT verisi hazır: {len(samples)} örnek")
        print(f"   Dosya: {output_file}")
        
        return output_file
    
    def prepare_dpo_data(self) -> Optional[Path]:
        """
        DPO için preference pair'ler hazırla.
        👍 = chosen, 👎 = rejected
        
        Strateji:
        1. Aynı intent için + ve - feedback varsa pair oluştur
        2. Correction varsa: original=rejected, corrected=chosen
        """
        import sqlite3
        conn = sqlite3.connect(str(self.db.db_path))
        cursor = conn.cursor()
        
        pairs = []
        
        # 1. Correction'lardan DPO pair oluştur
        cursor.execute("""
            SELECT id, user_message, assistant_response, corrected_response, adapter_used
            FROM feedback 
            WHERE corrected_response IS NOT NULL 
            AND corrected_response != ''
            AND used_for_training = 0
        """)
        corrections = cursor.fetchall()
        
        for row in corrections:
            fb_id, prompt, rejected, chosen, adapter = row
            if prompt and chosen and rejected:
                pairs.append({
                    "prompt": prompt,
                    "chosen": chosen,
                    "rejected": rejected,
                    "source": "correction",
                    "adapter": adapter or ""
                })
        
        # 2. Intent bazlı 👍/👎 pair'leri
        # Aynı intent için pozitif ve negatif örnekleri eşleştir
        cursor.execute("""
            SELECT intent FROM feedback 
            WHERE feedback_type IN ('thumbs_up', 'thumbs_down')
            AND used_for_training = 0
            GROUP BY intent
            HAVING COUNT(DISTINCT feedback_type) = 2
        """)
        intents_with_both = [row[0] for row in cursor.fetchall()]
        
        for intent in intents_with_both:
            # Bu intent için pozitif örnekler
            cursor.execute("""
                SELECT user_message, assistant_response, adapter_used
                FROM feedback 
                WHERE intent = ? AND feedback_type = 'thumbs_up' AND used_for_training = 0
                LIMIT 5
            """, (intent,))
            positives = cursor.fetchall()
            
            # Bu intent için negatif örnekler
            cursor.execute("""
                SELECT user_message, assistant_response, adapter_used
                FROM feedback 
                WHERE intent = ? AND feedback_type = 'thumbs_down' AND used_for_training = 0
                LIMIT 5
            """, (intent,))
            negatives = cursor.fetchall()
            
            # Pair oluştur (en basit: karşılıklı eşleştir)
            for pos, neg in zip(positives, negatives):
                # Pozitif örneğin cevabı chosen, negatifin rejected
                pairs.append({
                    "prompt": pos[0],  # Pozitif soruyu kullan
                    "chosen": pos[1],
                    "rejected": neg[1],
                    "source": "preference",
                    "adapter": pos[2] or ""
                })
        
        conn.close()
        
        if len(pairs) < 3:
            print(f"⚠️ DPO için yeterli pair yok: {len(pairs)}")
            return None
        
        # Kaydet
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"dpo_pairs_{timestamp}.jsonl"
        
        with open(output_file, "w", encoding="utf-8") as f:
            for pair in pairs:
                # DPO format
                dpo_sample = {
                    "prompt": pair["prompt"],
                    "chosen": pair["chosen"],
                    "rejected": pair["rejected"]
                }
                f.write(json.dumps(dpo_sample, ensure_ascii=False) + "\n")
        
        print(f"✅ DPO verisi hazır: {len(pairs)} pair")
        print(f"   - Correction'dan: {len([p for p in pairs if p['source'] == 'correction'])}")
        print(f"   - Preference'dan: {len([p for p in pairs if p['source'] == 'preference'])}")
        print(f"   Dosya: {output_file}")
        
        return output_file
    
    def run_sft_training(self, data_path: Path, adapter_name: str = "incremental") -> bool:
        """
        SFT eğitimi çalıştır (mlx_lm.lora).
        """
        print(f"\n🚀 SFT Eğitimi Başlıyor...")
        print(f"   Veri: {data_path}")
        print(f"   Adapter: {adapter_name}")
        
        output_adapter = Path(f"./adapters/{adapter_name}_sft_{datetime.now().strftime('%Y%m%d')}")
        
        cmd = [
            sys.executable, "-m", "mlx_lm.lora",
            "--model", "./models/base/qwen-2.5-3b-instruct",
            "--data", str(data_path.parent),
            "--train",
            "--iters", "100",
            "--batch-size", "1",
            "--lora-layers", "8",
            "--adapter-path", str(output_adapter)
        ]
        
        print(f"   Komut: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            
            if result.returncode == 0:
                print(f"✅ SFT eğitimi tamamlandı!")
                print(f"   Adapter: {output_adapter}")
                return True
            else:
                print(f"❌ SFT eğitimi başarısız:")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Eğitim zaman aşımına uğradı (30 dk)")
            return False
        except Exception as e:
            print(f"❌ Hata: {e}")
            return False
    
    def run_dpo_training(self, data_path: Path, adapter_name: str = "incremental") -> bool:
        """
        DPO eğitimi çalıştır.
        
        NOT: mlx_lm doğrudan DPO desteklemiyor.
        Alternatif olarak SFT-style eğitim yapıyoruz (chosen cevaplarla).
        Gerçek DPO için TRL veya custom implementation gerekir.
        """
        print(f"\n🚀 DPO-Style Eğitimi Başlıyor...")
        print(f"   Veri: {data_path}")
        
        # DPO verisini SFT formatına çevir (sadece chosen kullan)
        sft_data = []
        with open(data_path, "r") as f:
            for line in f:
                pair = json.loads(line)
                sft_sample = {
                    "messages": [
                        {"role": "user", "content": pair["prompt"]},
                        {"role": "assistant", "content": pair["chosen"]}
                    ]
                }
                sft_data.append(sft_sample)
        
        # Geçici SFT dosyası oluştur
        sft_path = data_path.parent / "dpo_as_sft_train.jsonl"
        with open(sft_path, "w") as f:
            for sample in sft_data:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
        
        # Validation için
        valid_path = data_path.parent / "valid.jsonl"
        if not valid_path.exists() and len(sft_data) > 2:
            with open(valid_path, "w") as f:
                f.write(json.dumps(sft_data[-1], ensure_ascii=False) + "\n")
        
        output_adapter = Path(f"./adapters/{adapter_name}_dpo_{datetime.now().strftime('%Y%m%d')}")
        
        cmd = [
            sys.executable, "-m", "mlx_lm.lora",
            "--model", "./models/base/qwen-2.5-3b-instruct",
            "--data", str(data_path.parent),
            "--train",
            "--iters", "50",  # DPO için daha az iterasyon
            "--batch-size", "1",
            "--lora-layers", "8",
            "--learning-rate", "5e-6",  # Daha düşük lr
            "--adapter-path", str(output_adapter)
        ]
        
        print(f"   Komut: {' '.join(cmd)}")
        print(f"   NOT: Gerçek DPO yerine chosen cevaplarla SFT yapılıyor")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
            
            if result.returncode == 0:
                print(f"✅ DPO-style eğitimi tamamlandı!")
                print(f"   Adapter: {output_adapter}")
                return True
            else:
                print(f"❌ Eğitim başarısız:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Hata: {e}")
            return False
    
    def mark_as_trained(self, feedback_type: str = "all"):
        """Feedback'leri eğitimde kullanıldı olarak işaretle."""
        import sqlite3
        conn = sqlite3.connect(str(self.db.db_path))
        cursor = conn.cursor()
        
        if feedback_type == "sft":
            cursor.execute("""
                UPDATE feedback SET used_for_training = 1
                WHERE corrected_response IS NOT NULL 
                AND corrected_response != ''
                AND used_for_training = 0
            """)
        elif feedback_type == "dpo":
            cursor.execute("""
                UPDATE feedback SET used_for_training = 1
                WHERE feedback_type IN ('thumbs_up', 'thumbs_down', 'correction', 'edit')
                AND used_for_training = 0
            """)
        else:
            cursor.execute("UPDATE feedback SET used_for_training = 1 WHERE used_for_training = 0")
        
        count = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"✅ {count} feedback eğitimde kullanıldı olarak işaretlendi")


def print_status(status: Dict[str, Any]):
    """Durumu güzel yazdır."""
    print("\n" + "="*50)
    print("📊 EVO-TR Training Pipeline Status")
    print("="*50)
    
    print(f"\n📋 Toplam Feedback: {status['total_feedback']}")
    print("   Türe Göre:")
    for ftype, count in status['by_type'].items():
        icon = "👍" if ftype == "thumbs_up" else "👎" if ftype == "thumbs_down" else "✏️"
        print(f"     {icon} {ftype}: {count}")
    
    print(f"\n🎯 SFT (Supervised Fine-Tuning):")
    sft = status['sft']
    print(f"   Düzeltme sayısı: {sft['candidates']}/{sft['threshold']}")
    if sft['ready']:
        print("   ✅ Eğitime HAZIR")
    else:
        print(f"   ⏳ {sft['threshold'] - sft['candidates']} düzeltme daha gerekli")
    
    print(f"\n🔄 DPO (Direct Preference Optimization):")
    dpo = status['dpo']
    print(f"   Tercih sayısı: {dpo['preference_count']}")
    print(f"   Pair oluşturulabilir intent: {dpo['intents_with_pairs']}")
    if dpo['ready']:
        print("   ✅ Eğitime HAZIR")
    else:
        if dpo['intents_with_pairs'] == 0:
            print("   ⏳ Aynı intent için hem 👍 hem 👎 gerekli")
        else:
            print(f"   ⏳ Daha fazla tercih gerekli")
    
    print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="EVO-TR Training Pipeline")
    parser.add_argument("command", nargs="?", default="status",
                       choices=["status", "prepare", "train-sft", "train-dpo", "train-all", "train"],
                       help="Komut")
    parser.add_argument("--force", action="store_true", help="Eşikleri atla")
    parser.add_argument("--sft-only", action="store_true", help="Sadece SFT eğitimi")
    parser.add_argument("--dpo-only", action="store_true", help="Sadece DPO eğitimi")
    
    args = parser.parse_args()
    
    pipeline = TrainingPipeline()
    
    if args.command == "status":
        status = pipeline.get_status()
        print_status(status)
        
    elif args.command == "prepare":
        print("\n📦 Eğitim Verisi Hazırlanıyor...\n")
        
        sft_file = pipeline.prepare_sft_data()
        dpo_file = pipeline.prepare_dpo_data()
        
        print("\n" + "-"*40)
        if sft_file:
            print(f"✅ SFT verisi: {sft_file}")
        if dpo_file:
            print(f"✅ DPO verisi: {dpo_file}")
        
    elif args.command == "train-sft":
        status = pipeline.get_status()
        if not status['sft']['ready'] and not args.force:
            print(f"⚠️ Yeterli düzeltme yok ({status['sft']['candidates']}/{status['sft']['threshold']})")
            print("   --force ile zorla başlatabilirsiniz")
            return
        
        sft_file = pipeline.prepare_sft_data()
        if sft_file:
            success = pipeline.run_sft_training(sft_file)
            if success:
                pipeline.mark_as_trained("sft")
        
    elif args.command == "train-dpo":
        status = pipeline.get_status()
        if not status['dpo']['ready'] and not args.force:
            print("⚠️ DPO için yeterli veri yok")
            print("   --force ile zorla başlatabilirsiniz")
            return
        
        dpo_file = pipeline.prepare_dpo_data()
        if dpo_file:
            success = pipeline.run_dpo_training(dpo_file)
            if success:
                pipeline.mark_as_trained("dpo")
        
    elif args.command == "train-all":
        print("\n🚀 Tüm Eğitimler Başlatılıyor...\n")
        
        # SFT
        sft_file = pipeline.prepare_sft_data()
        if sft_file:
            pipeline.run_sft_training(sft_file)
        
        # DPO
        dpo_file = pipeline.prepare_dpo_data()
        if dpo_file:
            pipeline.run_dpo_training(dpo_file)
        
        pipeline.mark_as_trained()
    
    elif args.command == "train":
        # Web API'den çağrılan genel train komutu
        print("\n🚀 Eğitim Başlatılıyor...\n")
        
        if args.sft_only:
            # Sadece SFT
            sft_file = pipeline.prepare_sft_data()
            if sft_file:
                success = pipeline.run_sft_training(sft_file)
                if success:
                    pipeline.mark_as_trained("sft")
                    print("✅ SFT eğitimi tamamlandı!")
            else:
                print("⚠️ SFT için yeterli veri yok")
                
        elif args.dpo_only:
            # Sadece DPO
            dpo_file = pipeline.prepare_dpo_data()
            if dpo_file:
                success = pipeline.run_dpo_training(dpo_file)
                if success:
                    pipeline.mark_as_trained("dpo")
                    print("✅ DPO eğitimi tamamlandı!")
            else:
                print("⚠️ DPO için yeterli veri yok")
                
        else:
            # Her ikisi
            sft_file = pipeline.prepare_sft_data()
            if sft_file:
                pipeline.run_sft_training(sft_file)
            
            dpo_file = pipeline.prepare_dpo_data()
            if dpo_file:
                pipeline.run_dpo_training(dpo_file)
            
            pipeline.mark_as_trained()
            print("✅ Tüm eğitimler tamamlandı!")


if __name__ == "__main__":
    main()
