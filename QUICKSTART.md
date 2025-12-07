# 🚀 EVO-TR Quickstart Guide

**Mini AGI PoC - Hızlı Başlangıç Kılavuzu**

---

## ⚡ 30 Saniyede Başla

```bash
# 1. Proje dizinine git
cd /Users/kaan/Desktop/Kaan/Personal/agı-llm

# 2. Virtual environment aktif et
source .venv/bin/activate

# 3. CLI'ı başlat
python scripts/chat_cli.py
```

**İşte bu kadar!** 🎉

---

## 🎯 Ne Yapabilirsin?

### Türkçe Sohbet
```
You: Merhaba, nasılsın?
You: Türk mutfağının en güzel yemeği nedir?
You: Bana bir atasözü söyle
```

### Python Kod Yazma
```
You: Python'da binary search fonksiyonu yaz
You: Fibonacci serisini hesaplayan bir fonksiyon
You: Bu kodda bug var, düzelt: def add(a, b): return a - b
```

### Hafıza Kullanımı
```
You: Benim adım Kaan
You: (... daha sonra ...)
You: Benim adım neydi?
```

---

## 🔧 CLI Komutları

| Komut | Açıklama |
|-------|----------|
| `/help` | Yardım menüsü |
| `/status` | Sistem durumu |
| `/clear` | Konuşmayı temizle |
| `/adapters` | Yüklü LoRA'ları listele |
| `/memory` | Hafıza istatistikleri |
| `/quit` | Çıkış |

---

## 📊 Gece Analizi Çalıştır

```bash
# Bugünün analizini yap
python scripts/run_analysis.py

# Son 7 günün analizini yap
python scripts/run_analysis.py --days 7
```

---

## 🧪 Testleri Çalıştır

```bash
# Tüm testleri çalıştır (93 test)
python -m pytest tests/ -v

# Sadece belirli modülü test et
python -m pytest tests/test_router.py -v
python -m pytest tests/test_memory.py -v
python -m pytest tests/test_lifecycle.py -v
```

---

## 🏗️ Sistem Bileşenleri

```
EVO-TR Mini AGI
├── 🧠 Router → Intent classification (7 kategori)
├── 🎓 LoRA Adapters
│   ├── tr_chat_v2 → Türkçe sohbet (V2 - %92 iyileşme) ⭐
│   ├── python_coder_v2 → Kod yazma (V2) ⭐
│   ├── math_expert → Matematik
│   ├── history_expert → Tarih
│   └── science_expert → Bilim
├── 💾 Memory
│   ├── ChromaDB → Uzun süreli (RAG)
│   └── ContextBuffer → Kısa süreli
├── ⚙️ Inference → MLX (Apple Silicon)
└── 🔄 Lifecycle
    ├── SyncHandler → Gündüz modu
    ├── AsyncProcessor → Gece analizi
    └── SelfImprovement → Otomatik iyileştirme
```

---

## 📁 Önemli Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `scripts/chat_cli.py` | Ana chat arayüzü |
| `src/orchestrator.py` | Tüm sistemi birleştirir |
| `src/router/classifier.py` | Intent sınıflandırıcı |
| `src/memory/memory_manager.py` | Hafıza yönetimi |
| `src/lifecycle/logger.py` | Log sistemi |
| `scripts/run_analysis.py` | Gece analizi |
| `scripts/gemini_data_generator.py` | Gemma 3 27B veri üretici |

---

## 📚 Dökümanlar

| Dosya | Açıklama |
|-------|----------|
| `docs/PROJECT-STRUCTURE.md` | Dizin yapısı |
| `docs/ARCHITECTURE.md` | Sistem mimarisi |
| `docs/COMPONENTS.md` | Bileşen detayları |
| `v2/TODO.md` | Güncel görevler |
| `v2/MEMORY.md` | Güncel durum |

---

## 🔄 Otomatik Gece Analizi (Opsiyonel)

macOS'ta her gece 03:00'te otomatik analiz için:

```bash
# LaunchD config'i kopyala
cp configs/com.evotr.night-analysis.plist ~/Library/LaunchAgents/

# LaunchAgent'ı yükle
launchctl load ~/Library/LaunchAgents/com.evotr.night-analysis.plist
```

---

## 🐛 Sorun Giderme

### Model yüklenmiyorsa
```bash
# Model yolunu kontrol et
ls -la models/base/qwen-2.5-3b-instruct/
```

### ChromaDB hatası
```bash
# ChromaDB dizinini temizle
rm -rf data/chromadb/
```

### Import hatası
```bash
# PYTHONPATH ayarla
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

---

## 📈 Sistem Gereksinimleri

- **OS:** macOS 14+ (Apple Silicon)
- **RAM:** Minimum 8GB, önerilen 16GB+
- **Disk:** ~5GB boş alan
- **Python:** 3.11+

---

## 🎯 Sonraki Adımlar

1. **Yeni LoRA eğit** - Farklı alanlarda uzmanlaşma
2. **Memory'yi zenginleştir** - Daha fazla fact ekle
3. **Router'ı genişlet** - Yeni intent kategorileri
4. **Self-improvement** - Gece analizlerini incele

---

**Happy Hacking! 🚀**
