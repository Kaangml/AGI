#!/usr/bin/env python3
"""
EVO-TR: System Monitor CLI

Merkezi monitoring ve yönetim aracı.
- Sistem durumu izleme
- Feedback istatistikleri
- Server yönetimi (start/stop)
- Eğitim yönetimi

Kullanım:
    python scripts/monitor.py              # Ana menü
    python scripts/monitor.py status       # Hızlı durum
    python scripts/monitor.py feedback     # Feedback detayları
    python scripts/monitor.py server start # Server başlat
    python scripts/monitor.py server stop  # Server durdur
"""

import sys
import os
import signal
import subprocess
import sqlite3
import psutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Proje kökünü path'e ekle
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class Colors:
    """Terminal renkleri."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


def colored(text: str, color: str) -> str:
    """Renkli text."""
    return f"{color}{text}{Colors.RESET}"


class SystemMonitor:
    """EVO-TR Sistem Monitörü."""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.db_path = self.project_root / "data" / "feedback.db"
        self.server_port = 8000
        self.log_dir = self.project_root / "logs"
        
    def clear_screen(self):
        """Ekranı temizle."""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def get_server_status(self) -> Dict[str, Any]:
        """Server durumunu kontrol et."""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', []) or []
                cmdline_str = ' '.join(cmdline)
                # run_server.py veya uvicorn kontrol et
                if 'run_server.py' in cmdline_str or ('uvicorn' in cmdline_str and '8000' in cmdline_str):
                    return {
                        'running': True,
                        'pid': proc.info['pid'],
                        'port': self.server_port,
                        'url': f'http://localhost:{self.server_port}'
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {'running': False}
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Feedback istatistiklerini al."""
        if not self.db_path.exists():
            return {'error': 'Database bulunamadı'}
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Toplam feedback
            cursor.execute("SELECT COUNT(*) FROM feedback")
            total = cursor.fetchone()[0]
            
            # Türe göre
            cursor.execute("""
                SELECT feedback_type, COUNT(*) 
                FROM feedback 
                GROUP BY feedback_type
            """)
            by_type = dict(cursor.fetchall())
            
            # Correction olanlar
            cursor.execute("""
                SELECT COUNT(*) FROM feedback 
                WHERE corrected_response IS NOT NULL AND corrected_response != ''
            """)
            corrections = cursor.fetchone()[0]
            
            # İşlenmemiş
            cursor.execute("SELECT COUNT(*) FROM feedback WHERE processed = 0")
            unprocessed = cursor.fetchone()[0]
            
            # Eğitim için kullanılan
            cursor.execute("SELECT COUNT(*) FROM feedback WHERE used_for_training = 1")
            trained = cursor.fetchone()[0]
            
            # Son 5 feedback
            cursor.execute("""
                SELECT id, feedback_type, user_message, timestamp 
                FROM feedback 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            recent = cursor.fetchall()
            
            conn.close()
            
            return {
                'total': total,
                'by_type': by_type,
                'corrections': corrections,
                'unprocessed': unprocessed,
                'trained': trained,
                'recent': recent
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_adapter_status(self) -> List[Dict[str, Any]]:
        """Adapter durumlarını al."""
        adapters_dir = self.project_root / "adapters"
        adapters = []
        
        if adapters_dir.exists():
            for adapter_path in adapters_dir.iterdir():
                if adapter_path.is_dir() and not adapter_path.name.startswith('.'):
                    # Config dosyası var mı?
                    config_file = adapter_path / "adapter_config.json"
                    adapters.append({
                        'name': adapter_path.name,
                        'path': str(adapter_path),
                        'valid': config_file.exists(),
                        'size': sum(f.stat().st_size for f in adapter_path.rglob('*') if f.is_file()) / (1024*1024)
                    })
        
        return adapters
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Sistem bellek durumu."""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total / (1024**3),
            'used': memory.used / (1024**3),
            'available': memory.available / (1024**3),
            'percent': memory.percent
        }
    
    def start_server(self) -> bool:
        """Server'ı başlat."""
        status = self.get_server_status()
        if status['running']:
            print(colored(f"⚠️  Server zaten çalışıyor (PID: {status['pid']})", Colors.YELLOW))
            return True
        
        print(colored("🚀 Server başlatılıyor...", Colors.CYAN))
        
        try:
            # Background'da başlat
            log_file = self.log_dir / "server.log"
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'a') as f:
                process = subprocess.Popen(
                    [sys.executable, str(self.project_root / "scripts" / "run_server.py")],
                    cwd=str(self.project_root),
                    stdout=f,
                    stderr=f,
                    start_new_session=True
                )
            
            # Biraz bekle
            import time
            time.sleep(3)
            
            status = self.get_server_status()
            if status['running']:
                print(colored(f"✅ Server başlatıldı", Colors.GREEN))
                print(f"   URL: {status['url']}")
                print(f"   PID: {status['pid']}")
                print(f"   Log: {log_file}")
                return True
            else:
                print(colored("❌ Server başlatılamadı", Colors.RED))
                print(f"   Log'u kontrol edin: {log_file}")
                return False
                
        except Exception as e:
            print(colored(f"❌ Hata: {e}", Colors.RED))
            return False
    
    def stop_server(self) -> bool:
        """Server'ı durdur."""
        status = self.get_server_status()
        if not status['running']:
            print(colored("⚠️  Server zaten çalışmıyor", Colors.YELLOW))
            return True
        
        print(colored(f"🛑 Server durduruluyor (PID: {status['pid']})...", Colors.CYAN))
        
        try:
            os.kill(status['pid'], signal.SIGTERM)
            import time
            time.sleep(2)
            
            # Hala çalışıyor mu?
            new_status = self.get_server_status()
            if not new_status['running']:
                print(colored("✅ Server durduruldu", Colors.GREEN))
                return True
            else:
                # Force kill
                os.kill(status['pid'], signal.SIGKILL)
                print(colored("✅ Server zorla durduruldu", Colors.YELLOW))
                return True
                
        except Exception as e:
            print(colored(f"❌ Hata: {e}", Colors.RED))
            return False
    
    def start_daemon(self) -> bool:
        """Feedback daemon'ını başlat."""
        print(colored("🔄 Feedback Daemon başlatılıyor...", Colors.CYAN))
        
        try:
            log_file = self.log_dir / "feedback_daemon.log"
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            subprocess.Popen(
                [sys.executable, str(self.project_root / "scripts" / "feedback_daemon.py"), "--daemon"],
                cwd=str(self.project_root),
                start_new_session=True
            )
            
            print(colored("✅ Daemon başlatıldı", Colors.GREEN))
            print(f"   Log: {log_file}")
            return True
            
        except Exception as e:
            print(colored(f"❌ Hata: {e}", Colors.RED))
            return False
    
    def print_header(self):
        """Header yazdır."""
        print()
        print(colored("═" * 60, Colors.BLUE))
        print(colored("  🤖 EVO-TR System Monitor", Colors.BOLD + Colors.CYAN))
        print(colored("═" * 60, Colors.BLUE))
        print()
    
    def print_status(self):
        """Hızlı durum özeti."""
        self.print_header()
        
        # Server durumu
        server = self.get_server_status()
        if server['running']:
            print(colored(f"🌐 Server:     ", Colors.BOLD) + colored(f"✅ Çalışıyor ({server['url']})", Colors.GREEN))
        else:
            print(colored(f"🌐 Server:     ", Colors.BOLD) + colored("❌ Kapalı", Colors.RED))
        
        # Feedback durumu
        feedback = self.get_feedback_stats()
        if 'error' not in feedback:
            corrections = feedback.get('corrections', 0)
            threshold = 10
            if corrections >= threshold:
                status = colored(f"✅ Eğitime hazır ({corrections}/{threshold})", Colors.GREEN)
            else:
                status = colored(f"⏳ {corrections}/{threshold} correction", Colors.YELLOW)
            print(colored(f"📊 Feedback:   ", Colors.BOLD) + status)
            print(colored(f"   Toplam:     ", Colors.GRAY) + f"{feedback.get('total', 0)} kayıt")
        else:
            print(colored(f"📊 Feedback:   ", Colors.BOLD) + colored("❌ " + feedback['error'], Colors.RED))
        
        # Bellek
        memory = self.get_memory_stats()
        mem_color = Colors.GREEN if memory['percent'] < 70 else Colors.YELLOW if memory['percent'] < 90 else Colors.RED
        print(colored(f"💾 Bellek:     ", Colors.BOLD) + colored(f"{memory['percent']:.1f}% kullanımda", mem_color))
        print(colored(f"   Kullanılan: ", Colors.GRAY) + f"{memory['used']:.1f} / {memory['total']:.1f} GB")
        
        # Adaptörler
        adapters = self.get_adapter_status()
        v2_adapters = [a for a in adapters if 'v2' in a['name']]
        print(colored(f"🔌 Adaptörler: ", Colors.BOLD) + f"{len(adapters)} toplam, {len(v2_adapters)} V2")
        
        print()
    
    def print_feedback_details(self):
        """Detaylı feedback bilgisi."""
        self.print_header()
        print(colored("📊 Feedback Detayları", Colors.BOLD + Colors.CYAN))
        print(colored("─" * 40, Colors.GRAY))
        
        stats = self.get_feedback_stats()
        if 'error' in stats:
            print(colored(f"❌ Hata: {stats['error']}", Colors.RED))
            return
        
        print(f"\n📈 Özet:")
        print(f"   Toplam feedback:     {stats['total']}")
        print(f"   Correction'lar:      {stats['corrections']}")
        print(f"   İşlenmemiş:          {stats['unprocessed']}")
        print(f"   Eğitimde kullanılan: {stats['trained']}")
        
        print(f"\n📋 Türe Göre:")
        for ftype, count in stats.get('by_type', {}).items():
            icon = "👍" if ftype == "thumbs_up" else "👎" if ftype == "thumbs_down" else "✏️" if ftype == "correction" else "📝"
            print(f"   {icon} {ftype}: {count}")
        
        print(f"\n🕒 Son 5 Feedback:")
        for fb in stats.get('recent', []):
            fb_id, fb_type, msg, ts = fb
            msg_short = (msg[:40] + "...") if msg and len(msg) > 40 else msg
            print(f"   [{fb_id[:8]}] {fb_type:12} | {msg_short}")
        
        # Eğitim durumu
        print(f"\n🎯 Eğitim Durumu:")
        threshold = 10
        corrections = stats['corrections']
        if corrections >= threshold:
            print(colored(f"   ✅ Yeterli correction var! ({corrections}/{threshold})", Colors.GREEN))
            print(f"   Eğitim başlatmak için: python scripts/process_feedback.py --train")
        else:
            remaining = threshold - corrections
            print(colored(f"   ⏳ {remaining} correction daha gerekli ({corrections}/{threshold})", Colors.YELLOW))
        
        print()
    
    def print_menu(self):
        """Ana menüyü göster."""
        self.print_status()
        
        print(colored("📋 Komutlar:", Colors.BOLD))
        print(colored("─" * 40, Colors.GRAY))
        print("  [1] Durum yenile")
        print("  [2] Feedback detayları")
        print("  [3] Server başlat")
        print("  [4] Server durdur")
        print("  [5] Daemon başlat")
        print("  [6] Web arayüzü aç")
        print("  [7] Eğitim başlat")
        print("  [q] Çıkış")
        print()
    
    def open_web(self):
        """Tarayıcıda web arayüzü aç."""
        server = self.get_server_status()
        if not server['running']:
            print(colored("⚠️  Server çalışmıyor. Önce başlatın.", Colors.YELLOW))
            return
        
        import webbrowser
        webbrowser.open(server['url'])
        print(colored(f"🌐 Tarayıcıda açılıyor: {server['url']}", Colors.CYAN))
    
    def run_training(self):
        """Eğitimi başlat."""
        print(colored("🎓 Eğitim başlatılıyor...", Colors.CYAN))
        
        try:
            result = subprocess.run(
                [sys.executable, str(self.project_root / "scripts" / "process_feedback.py"), "--train"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.stderr:
                print(colored(result.stderr, Colors.YELLOW))
        except Exception as e:
            print(colored(f"❌ Hata: {e}", Colors.RED))
    
    def interactive_menu(self):
        """İnteraktif menü."""
        while True:
            self.clear_screen()
            self.print_menu()
            
            try:
                choice = input(colored("Seçim: ", Colors.CYAN)).strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Görüşürüz!")
                break
            
            if choice == '1':
                continue  # Yenile
            elif choice == '2':
                self.clear_screen()
                self.print_feedback_details()
                input(colored("\nDevam etmek için Enter'a basın...", Colors.GRAY))
            elif choice == '3':
                self.start_server()
                input(colored("\nDevam etmek için Enter'a basın...", Colors.GRAY))
            elif choice == '4':
                self.stop_server()
                input(colored("\nDevam etmek için Enter'a basın...", Colors.GRAY))
            elif choice == '5':
                self.start_daemon()
                input(colored("\nDevam etmek için Enter'a basın...", Colors.GRAY))
            elif choice == '6':
                self.open_web()
                input(colored("\nDevam etmek için Enter'a basın...", Colors.GRAY))
            elif choice == '7':
                self.clear_screen()
                self.run_training()
                input(colored("\nDevam etmek için Enter'a basın...", Colors.GRAY))
            elif choice == 'q':
                print("👋 Görüşürüz!")
                break


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="EVO-TR System Monitor")
    parser.add_argument("command", nargs="?", default="menu",
                       choices=["menu", "status", "feedback", "server", "daemon", "train"],
                       help="Komut")
    parser.add_argument("action", nargs="?", help="Alt komut (start/stop)")
    
    args = parser.parse_args()
    
    monitor = SystemMonitor()
    
    if args.command == "menu":
        monitor.interactive_menu()
    elif args.command == "status":
        monitor.print_status()
    elif args.command == "feedback":
        monitor.print_feedback_details()
    elif args.command == "server":
        if args.action == "start":
            monitor.start_server()
        elif args.action == "stop":
            monitor.stop_server()
        else:
            print("Kullanım: python scripts/monitor.py server [start|stop]")
    elif args.command == "daemon":
        monitor.start_daemon()
    elif args.command == "train":
        monitor.run_training()


if __name__ == "__main__":
    main()
