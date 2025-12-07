# EVO-TR Komutlar

## 🖥️ Monitor (Ana Yönetim Aracı)

```bash
# İnteraktif menü
python scripts/monitor.py

# Hızlı durum özeti
python scripts/monitor.py status

# Feedback detayları
python scripts/monitor.py feedback

# Server yönetimi
python scripts/monitor.py server start
python scripts/monitor.py server stop

# Daemon başlat (arka plan eğitim)
python scripts/monitor.py daemon

# Manuel eğitim
python scripts/monitor.py train
```

## 🔄 Feedback Daemon (Otomatik Eğitim)

```bash
# Foreground çalıştır (test için)
python scripts/feedback_daemon.py

# Daemon modunda (arka plan)
python scripts/feedback_daemon.py --daemon

# Durumu kontrol et
python scripts/feedback_daemon.py --status
```

## 🌐 Web Arayüzü

- URL: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Feedback Butonları:
- 👍 Beğendim
- 👎 Beğenmedim  
- ✏️ Düzelt (correction modal açar)

## 💻 CLI Chat

```bash
python scripts/chat_cli.py
```

### Komutlar:
- `/good` - Son cevabı beğen
- `/bad` - Son cevabı beğenme
- `/correct <düzeltme>` - Doğru cevabı gir
- `/quit` - Çıkış

## 📊 Eğitim Durumu

- **Hedef:** 10 correction
- **Mevcut:** `python scripts/monitor.py feedback` ile kontrol et
- **Otomatik:** Daemon çalışırken 10'a ulaşınca otomatik başlar
