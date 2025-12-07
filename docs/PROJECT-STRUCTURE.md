# 📁 EVO-TR Proje Yapısı

**Bu döküman versiyondan bağımsızdır ve projenin genel dizin yapısını açıklar.**

---

## 🗂️ Kök Dizin Yapısı

```
agı-llm/
├── 📄 QUICKSTART.md          # Hızlı başlangıç rehberi
├── 📄 requirements.txt       # Python bağımlılıkları
├── 📄 .env                   # API anahtarları (git'te yok)
│
├── 📁 adapters/              # LoRA adaptörleri
├── 📁 configs/               # Konfigürasyon dosyaları
├── 📁 data/                  # Eğitim ve üretilen veriler
├── 📁 docs/                  # Proje dökümanları
├── 📁 logs/                  # Log dosyaları
├── 📁 models/                # Temel modeller
├── 📁 scripts/               # Yardımcı scriptler
├── 📁 src/                   # Ana kaynak kodları
├── 📁 tests/                 # Test dosyaları
├── 📁 todos/                 # Faz bazlı görev listeleri
├── 📁 v1/                    # V1 arşiv dökümanları
└── 📁 v2/                    # V2 aktif dökümanlar
```

---

## 📁 adapters/ - LoRA Adaptörleri

Fine-tune edilmiş LoRA adaptör ağırlıklarını içerir.

```
adapters/
├── history_expert/           # Tarih uzmanı adaptörü
│   ├── 0000500_adapters.safetensors
│   ├── 0001000_adapters.safetensors
│   └── ...
├── math_expert/              # Matematik uzmanı adaptörü
├── python_coder/             # Python kod V1 adaptörü
├── python_coder_v2/          # Python kod V2 adaptörü ⭐
├── science_expert/           # Bilim uzmanı adaptörü
├── tr_chat/                  # Türkçe sohbet V1 adaptörü
└── tr_chat_v2/               # Türkçe sohbet V2 adaptörü ⭐
```

**Adaptör Dosya Formatı:** `{iterasyon}_adapters.safetensors`

---

## 📁 configs/ - Konfigürasyonlar

Eğitim ve sistem konfigürasyonları.

```
configs/
├── intent_mapping.json       # Intent-expert eşleştirme
├── settings.py               # Genel ayarlar
├── lora_history_config.yaml  # Tarih LoRA config
├── lora_math_config.yaml     # Matematik LoRA config
├── lora_python_config.yaml   # Python V1 config
├── lora_python_config_v2.yaml # Python V2 config ⭐
├── lora_science_config.yaml  # Bilim LoRA config
├── lora_tr_config.yaml       # Türkçe V1 config
└── lora_tr_config_v2.yaml    # Türkçe V2 config ⭐
```

---

## 📁 data/ - Veriler

Tüm eğitim, test ve üretilen veriler.

```
data/
├── active_learning/          # Aktif öğrenme verileri
├── chromadb/                 # ChromaDB vektör deposu
├── generated/                # Üretilen ham veriler
│   ├── turkish_chat/         # Türkçe sohbet verileri
│   └── python_code/          # Python kod verileri
├── incremental/              # Artımlı eğitim verileri
├── intents/                  # Intent sınıflandırma verileri
├── preferences/              # Tercih öğrenme verileri
├── training/                 # MLX formatında eğitim verileri
│   ├── gemma_tr_chat/        # Türkçe V2 eğitim seti
│   ├── gemma_python_code/    # Python V2 eğitim seti
│   └── ...
├── test_incremental/         # Artımlı test verileri
└── test_preferences/         # Tercih test verileri
```

---

## 📁 docs/ - Dökümanlar

Versiyondan bağımsız proje dökümanları.

```
docs/
├── PROJECT-STRUCTURE.md      # Bu dosya
├── ARCHITECTURE.md           # Sistem mimarisi
└── COMPONENTS.md             # Bileşen açıklamaları
```

---

## 📁 logs/ - Loglar

Çalışma zamanı logları ve analiz çıktıları.

```
logs/
├── conversations_*.jsonl     # Konuşma logları
├── evotr_*.jsonl             # Sistem logları
├── performance_*.jsonl       # Performans metrikleri
├── active_learning/          # Aktif öğrenme logları
├── analysis/                 # Analiz çıktıları
├── conversations/            # Konuşma arşivi
└── improvements/             # İyileştirme logları
```

---

## 📁 models/ - Modeller

Temel model dosyaları.

```
models/
└── base/
    └── qwen-2.5-3b-instruct/ # Temel Qwen 2.5 3B modeli
        ├── config.json
        ├── model-*.safetensors
        ├── tokenizer.json
        └── ...
```

---

## 📁 scripts/ - Scriptler

Yardımcı script ve araçlar.

```
scripts/
├── # Veri Hazırlama
├── build_intent_dataset.py   # Intent veri seti oluşturma
├── clean_code_data.py        # Kod verisi temizleme
├── clean_training_data.py    # Eğitim verisi temizleme
├── download_*.py             # Veri indirme scriptleri
├── prepare_*.py              # Veri hazırlama scriptleri
│
├── # Veri Üretimi
├── gemini_data_generator.py  # Gemma 3 27B ile veri üretimi ⭐
│
├── # Model İşlemleri
├── convert_python_to_mlx.py  # Python model dönüştürme
├── convert_to_mlx_format.py  # MLX format dönüştürme
│
├── # Test & Demo
├── chat_cli.py               # CLI sohbet arayüzü
├── memory_rag_demo.py        # RAG bellek demosu
├── router_demo.py            # Router demo
├── test_adapter_*.py         # Adaptör testleri
├── verify_setup.py           # Kurulum doğrulama
│
├── # Sunucu & Analiz
├── run_analysis.py           # Analiz çalıştırma
├── run_server.py             # Web sunucu başlatma
└── split_dataset.py          # Veri seti bölme
```

---

## 📁 src/ - Kaynak Kod

Ana uygulama kaynak kodları.

```
src/
├── __init__.py
├── orchestrator.py           # Ana orchestrator
│
├── experts/                  # Uzman modülleri
│   ├── __init__.py
│   ├── base_expert.py        # Temel uzman sınıfı
│   ├── history_expert.py     # Tarih uzmanı
│   ├── math_expert.py        # Matematik uzmanı
│   ├── python_expert.py      # Python uzmanı
│   ├── science_expert.py     # Bilim uzmanı
│   └── tr_chat_expert.py     # Türkçe sohbet uzmanı
│
├── inference/                # Çıkarım modülleri
│   ├── __init__.py
│   ├── adapter_manager.py    # Adaptör yönetimi
│   ├── base_inference.py     # Temel çıkarım
│   └── mlx_inference.py      # MLX çıkarım motoru
│
├── lifecycle/                # Yaşam döngüsü yönetimi
│   ├── __init__.py
│   ├── active_learning.py    # Aktif öğrenme
│   ├── incremental_trainer.py # Artımlı eğitim
│   └── preference_learning.py # Tercih öğrenme
│
├── memory/                   # Bellek & RAG
│   ├── __init__.py
│   ├── chroma_store.py       # ChromaDB entegrasyonu
│   ├── conversation_memory.py # Konuşma belleği
│   └── rag_retriever.py      # RAG getirici
│
├── router/                   # Intent yönlendirme
│   ├── __init__.py
│   ├── intent_classifier.py  # Intent sınıflandırıcı
│   └── expert_router.py      # Uzman yönlendirici
│
├── ttt/                      # Test-Time Training
│   ├── __init__.py
│   └── ttt_engine.py         # TTT motoru
│
└── web/                      # Web API
    ├── __init__.py
    ├── api.py                # REST API
    └── websocket.py          # WebSocket desteği
```

---

## 📁 tests/ - Testler

Birim ve entegrasyon testleri.

```
tests/
├── test_active_learning.py   # Aktif öğrenme testleri
├── test_history_expert.py    # Tarih uzmanı testleri
├── test_incremental_training.py # Artımlı eğitim testleri
├── test_integration.py       # Entegrasyon testleri
├── test_lifecycle.py         # Yaşam döngüsü testleri
├── test_math_expert.py       # Matematik uzmanı testleri
├── test_memory.py            # Bellek testleri
├── test_preference_learning.py # Tercih öğrenme testleri
├── test_router.py            # Router testleri
├── test_science_expert.py    # Bilim uzmanı testleri
├── test_ttt.py               # TTT testleri
└── test_web_api.py           # Web API testleri
```

---

## 📁 todos/ - Görev Listeleri

Faz bazlı detaylı görev listeleri.

```
todos/
├── FAZ-0-ALTYAPI-KURULUM.md  # Altyapı kurulumu
├── FAZ-1-ROUTER.md           # Router geliştirme
├── FAZ-2-TURKCE-UZMAN.md     # Türkçe uzman
├── FAZ-3-PYTHON-UZMAN.md     # Python uzman
├── FAZ-4-HAFIZA-RAG.md       # Hafıza & RAG
├── FAZ-5-ENTEGRASYON.md      # Entegrasyon
└── FAZ-6-YASAM-DONGUSU.md    # Yaşam döngüsü
```

---

## 📁 v1/ ve v2/ - Versiyon Dökümanları

```
v1/                           # Arşiv (V1 tamamlandı)
├── AGENT-MEMORY.md
├── EVO-TR-DOCUMENTATION.md
├── EVO-TR-TODO-MASTER.md
├── init-documentation-general.md
├── init-todo-list.md
└── V1-FINAL-REPORT.md

v2/                           # Aktif (mevcut versiyon)
├── TODO.md                   # V2 görev listesi
└── MEMORY.md                 # V2 bellek/durum
```

---

## 🔧 Önemli Dosyalar

| Dosya | Açıklama | Öncelik |
|-------|----------|---------|
| `.env` | API anahtarları | 🔴 Kritik |
| `requirements.txt` | Python bağımlılıkları | 🔴 Kritik |
| `src/orchestrator.py` | Ana koordinatör | 🔴 Kritik |
| `scripts/chat_cli.py` | CLI arayüzü | 🟡 Önemli |
| `scripts/gemini_data_generator.py` | Veri üretici | 🟡 Önemli |
| `v2/TODO.md` | Aktif görevler | 🟢 Referans |
| `v2/MEMORY.md` | Aktif durum | 🟢 Referans |

---

## 📏 Dosya Adlandırma Kuralları

1. **Python dosyaları:** `snake_case.py`
2. **Markdown dökümanları:** `UPPERCASE-WITH-DASHES.md`
3. **YAML config:** `component_type_config.yaml`
4. **Log dosyaları:** `category_YYYY-MM-DD.jsonl`
5. **Adaptör dosyaları:** `{iterasyon}_adapters.safetensors`
