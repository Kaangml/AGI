#!/usr/bin/env python3
"""
EVO-TR: Feedback Daemon

Arka planda çalışarak feedback'leri izler.
10+ correction feedback olduğunda otomatik eğitimi başlatır.

Kullanım:
    # Foreground
    python scripts/feedback_daemon.py
    
    # Background (daemon mode)
    python scripts/feedback_daemon.py --daemon
    
    # Check durumu
    python scripts/feedback_daemon.py --status
"""

import sys
import time
import signal
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

# Proje kökünü path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lifecycle.feedback import FeedbackDatabase


class FeedbackDaemon:
    """Feedback izleme ve otomatik eğitim daemon'ı."""
    
    def __init__(
        self,
        db_path: str = "./data/feedback.db",
        check_interval: int = 300,  # 5 dakika
        min_corrections: int = 10,
        log_path: str = "./logs/feedback_daemon.log"
    ):
        self.db_path = db_path
        self.check_interval = check_interval
        self.min_corrections = min_corrections
        self.log_path = Path(log_path)
        self.running = False
        
        # Log klasörü
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.db: Optional[FeedbackDatabase] = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log mesajı yaz."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        print(log_line)
        
        with open(self.log_path, "a") as f:
            f.write(log_line + "\n")
    
    def init_db(self):
        """Database bağlantısını başlat."""
        try:
            self.db = FeedbackDatabase(self.db_path)
            return True
        except Exception as e:
            self.log(f"Database bağlantı hatası: {e}", "ERROR")
            return False
    
    def check_corrections(self) -> int:
        """Eğitime hazır correction sayısını kontrol et."""
        if not self.db:
            return 0
        
        try:
            corrected = self.db.get_corrected_responses()
            return len(corrected)
        except Exception as e:
            self.log(f"Correction kontrol hatası: {e}", "ERROR")
            return 0
    
    def start_training(self):
        """Eğitim sürecini başlat."""
        self.log("🚀 Eğitim başlatılıyor...", "INFO")
        
        try:
            # process_feedback.py'ı çalıştır
            script_path = Path(__file__).parent / "process_feedback.py"
            
            result = subprocess.run(
                [sys.executable, str(script_path), "--train"],
                capture_output=True,
                text=True,
                cwd=str(Path(__file__).parent.parent)
            )
            
            if result.returncode == 0:
                self.log("✅ Eğitim başarıyla tamamlandı", "INFO")
                self.log(f"Çıktı: {result.stdout[:500]}", "DEBUG")
            else:
                self.log(f"❌ Eğitim hatası: {result.stderr}", "ERROR")
                
        except Exception as e:
            self.log(f"❌ Eğitim başlatma hatası: {e}", "ERROR")
    
    def handle_signal(self, signum, frame):
        """Sinyal işleyici (SIGINT, SIGTERM)."""
        self.log("🛑 Durdurma sinyali alındı", "INFO")
        self.running = False
    
    def run(self):
        """Ana döngü."""
        self.log("=" * 50)
        self.log("🔄 EVO-TR Feedback Daemon başlatıldı", "INFO")
        self.log(f"   Check interval: {self.check_interval}s")
        self.log(f"   Min corrections: {self.min_corrections}")
        self.log(f"   Database: {self.db_path}")
        self.log("=" * 50)
        
        # Sinyal işleyicileri
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
        # Database bağlantısı
        if not self.init_db():
            self.log("Database başlatılamadı, çıkılıyor", "ERROR")
            return
        
        self.running = True
        last_training_count = 0
        
        while self.running:
            try:
                # Correction sayısını kontrol et
                correction_count = self.check_corrections()
                
                self.log(f"📊 Correction sayısı: {correction_count}/{self.min_corrections}")
                
                if correction_count >= self.min_corrections:
                    # Yeni correction var mı kontrol et
                    if correction_count > last_training_count:
                        self.log(f"✨ Yeni correction'lar tespit edildi ({correction_count - last_training_count} adet)")
                        self.start_training()
                        last_training_count = correction_count
                    else:
                        self.log("⏭️ Yeni correction yok, eğitim atlandı")
                
                # Bekle
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.log(f"Döngü hatası: {e}", "ERROR")
                time.sleep(60)  # Hata durumunda 1 dakika bekle
        
        self.log("👋 Daemon durdu", "INFO")
    
    def check_status(self):
        """Mevcut durumu göster."""
        if not self.init_db():
            print("❌ Database bağlantısı kurulamadı")
            return
        
        correction_count = self.check_corrections()
        pending = self.db.get_unprocessed_feedback()
        negative = self.db.get_negative_feedback()
        
        print("\n📊 EVO-TR Feedback Durumu")
        print("=" * 40)
        print(f"✏️  Correction sayısı:  {correction_count}")
        print(f"📋 İşlenmemiş:         {len(pending)}")
        print(f"👎 Negatif feedback:   {len(negative)}")
        print(f"🎯 Eğitim eşiği:       {self.min_corrections}")
        print()
        
        if correction_count >= self.min_corrections:
            print("✅ Eğitim için yeterli correction var!")
            print("   Daemon çalışıyorsa otomatik başlayacak.")
        else:
            remaining = self.min_corrections - correction_count
            print(f"⏳ Eğitim için {remaining} correction daha gerekli")
        print()


def daemonize():
    """Daemon modunda başlat (arka plan)."""
    import os
    
    # Fork
    pid = os.fork()
    if pid > 0:
        print(f"🔄 Daemon başlatıldı (PID: {pid})")
        print(f"   Log: ./logs/feedback_daemon.log")
        print(f"   Durdurmak için: kill {pid}")
        sys.exit(0)
    
    # Yeni session
    os.setsid()
    
    # Stdin/stdout/stderr'i kapat
    sys.stdin.close()
    
    # Log'a yönlendir
    log_path = Path("./logs/feedback_daemon.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    sys.stdout = open(log_path, "a")
    sys.stderr = sys.stdout


def main():
    parser = argparse.ArgumentParser(description="EVO-TR Feedback Daemon")
    parser.add_argument("--daemon", action="store_true", help="Daemon modunda başlat")
    parser.add_argument("--status", action="store_true", help="Durumu göster")
    parser.add_argument("--interval", type=int, default=300, help="Check interval (saniye)")
    parser.add_argument("--min-corrections", type=int, default=10, help="Minimum correction sayısı")
    
    args = parser.parse_args()
    
    daemon = FeedbackDaemon(
        check_interval=args.interval,
        min_corrections=args.min_corrections
    )
    
    if args.status:
        daemon.check_status()
    elif args.daemon:
        daemonize()
        daemon.run()
    else:
        daemon.run()


if __name__ == "__main__":
    main()
