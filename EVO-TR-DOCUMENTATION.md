# 📘 EVO-TR: Otonom ve Modüler YZ Mimari Dokümantasyonu

**Sürüm:** 1.0 (PoC)  
**Tarih:** 02 Aralık 2025  
**Temel Model:** Qwen-2.5-3B-Instruct  
**Donanım:** Mac Mini M4 (Apple Silicon)

---

## 1. Proje Vizyonu ve Felsefesi

EVO-TR, statik ve her şeyi tek seferde öğrenmeye çalışan devasa bir model yerine; **modüler, adaptif ve zamanla gelişen** biyolojik bir öğrenme sürecini simüle etmeyi hedefler.

* **Metafor:** "Bebek -> Çocuk -> Uzman"
* **Temel Prensip:** "Omurga (Base Model) sabit kalır, yetenekler (LoRA) ve hafıza (Vector DB) dinamik olarak büyür."
* **Çalışma Mantığı:** Gündüz etkileşime girer (Senkron), gece deneyimlerini işler (Asenkron)

---

## 2. Sistem Mimarisi (Kuş Bakışı)

```
┌─────────────────────────────────────────────────────────────────┐
│                        KULLANICI GİRDİSİ                        │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ROUTER (Sınıflandırıcı)                       │
│              DistilBERT / BGE-M3 (Hafif Model)                  │
│         Çıktı: expert_tr_chat | expert_python_coder             │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              OMURGA + SEÇİLEN UZMAN (LoRA)                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │         Qwen-2.5-3B-Instruct (Frozen Base)              │   │
│   │                      +                                  │   │
│   │   adapter_tr_chat.safetensors | adapter_python.safetensors  │
│   └─────────────────────────────────────────────────────────┘   │
│              Serving: MLX-LM (Apple Silicon Optimized)          │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     HAFIZA KATMANI                              │
│   ┌──────────────────┐    ┌──────────────────────────────────┐  │
│   │ Kısa Süreli      │    │ Uzun Süreli (RAG)                │  │
│   │ Context Window   │    │ ChromaDB + Turkish Embeddings    │  │
│   │ (Son 10-20 mesaj)│    │ emrecan/bert-base-turkish-cased  │  │
│   └──────────────────┘    └──────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ÇIKTI + LOGLAMA                         │
└─────────────────────────────────────────────────────────────────┘
```

### A. Yönetim Katmanı (The Router - Beyincik)
* **Model:** `DistilBERT` veya `bge-m3`
* **Görevi:** Gelen istemin niyetini anlamak
* **Çıktı:** Hangi LoRA adaptörünün kullanılacağı bilgisi

### B. Omurga ve Uzmanlar (The Brain & Skills)
* **Base Model:** `Qwen-2.5-3B-Instruct` (Frozen)
* **Serving Motoru:** `MLX-LM` (Mac M4 için optimize)
* **Uzmanlar:**
  1. **Expert A (Dil Uzmanı):** Türkçe kültürü, sohbet, metin işleme
  2. **Expert B (Kod Uzmanı):** Python, algoritma, debugging

### C. Hafıza Katmanı (The Memory - Hipokampus)
* **Kısa Süreli Hafıza:** Context Window (Son 10-20 mesaj)
* **Uzun Süreli Hafıza (RAG):** `ChromaDB`
* **Embedding Model:** `emrecan/bert-base-turkish-cased-mean-nli-stsb-tr`

### D. Yaşam Döngüsü Katmanı (The Loop)
* **Senkron (Gündüz):** Canlı sohbet ve anlık yanıt
* **Asenkron (Gece):** Log analizi, hafızaya işleme, etiketleme

---

## 3. Mac Mini M4 Özel Konfigürasyonu

### Donanım Özellikleri
* **Chip:** Apple M4
* **Unified Memory:** 16GB/24GB/32GB (paylaşımlı RAM/VRAM)
* **Neural Engine:** 16-core (ML workloads için optimize)
* **Metal:** GPU acceleration desteği

### Yazılım Stack (Apple Silicon Optimize)
| Araç | Açıklama | Neden? |
|------|----------|--------|
| `MLX` | Apple'ın ML framework'ü | M4 için native, hızlı |
| `MLX-LM` | LLM inference/training | LoRA desteği, düşük bellek |
| `Ollama` | Alternatif inference | Kolay kurulum |
| `llama.cpp` | GGUF format desteği | Metal backend |

### Bellek Optimizasyonu
```
Qwen-2.5-3B-Instruct (4-bit): ~2GB VRAM
LoRA Adapter: ~100MB each
ChromaDB: ~500MB (başlangıç)
Router Model: ~250MB
─────────────────────────────
Toplam Tahmini: ~4-5GB
```

---

## 4. Veri Setleri ve Eğitim Stratejisi

| Uzmanlık Alanı | Kaynak Veri Setleri | Eğitim Yöntemi | Hedef |
|----------------|---------------------|----------------|-------|
| **Router** | Elle hazırlanmış Intent seti (100+ örnek) | Few-Shot / Fine-tuning | Doğru kategori |
| **Türkçe Uzmanı** | `CohereForAI/aya_dataset (tr)` + Turkish-Instructions | QLoRA (MLX) | Doğal Türkçe |
| **Python Uzmanı** | `Humaneval-X` + `MBPP` | QLoRA (MLX) | Hatasız kod |

---

## 5. Teknoloji Yığını (Tech Stack)

### Core
* **Python:** 3.10+ (pyenv ile yönetim)
* **Base Model:** Qwen-2.5-3B-Instruct
* **Format:** MLX format veya GGUF (4-bit quantized)

### ML/AI
* **Framework:** `mlx`, `mlx-lm` (Apple Silicon native)
* **Fine-Tuning:** `mlx-lm` LoRA/QLoRA
* **Embeddings:** `sentence-transformers`

### Veri & Hafıza
* **Vector DB:** `ChromaDB`
* **Orkestrasyon:** `LangChain` veya pure Python

### Geliştirme
* **Paket Yönetimi:** `uv` veya `pip`
* **Ortam:** `venv` veya `conda`
* **IDE:** VS Code + Copilot

---

## 6. Ortam Değişkenleri (.env)

```env
# Hugging Face
HF_TOKEN=your_huggingface_token_here

# Model Paths
BASE_MODEL_PATH=./models/qwen-2.5-3b-instruct
ADAPTER_TR_PATH=./adapters/adapter_tr_chat.safetensors
ADAPTER_PYTHON_PATH=./adapters/adapter_python_coder.safetensors

# ChromaDB
CHROMA_PERSIST_DIR=./data/chromadb

# Logging
LOG_DIR=./logs
LOG_LEVEL=INFO

# System
DEVICE=mps  # Metal Performance Shaders for Mac
```

---

## 7. Risk Yönetimi

### 1. Bermuda Şeytan Üçgeni (Hafıza Karışıklığı)
* **Risk:** Kod yazarken Türkçe sohbet modülünün devreye girmesi
* **Önlem:** Router'ın Confidence Score kontrolü, düşükse Base Model kullan

### 2. Token Limitleri
* **Risk:** RAG sisteminin context'i doldurması
* **Önlem:** `Top-k=3` sınırı

### 3. Soğuk Başlangıç (Cold Start)
* **Risk:** Adaptör değişimlerinde gecikme
* **Önlem:** MLX'in önbellek mekanizması kullan

### 4. Mac M4 Spesifik
* **Risk:** Büyük batch size'larda bellek taşması
* **Önlem:** Batch size=1, gradient checkpointing aktif

---

## 8. Dizin Yapısı

```
agı-llm/
├── .env                          # Ortam değişkenleri
├── EVO-TR-DOCUMENTATION.md       # Bu doküman
├── EVO-TR-TODO-MASTER.md         # Ana todo listesi
├── requirements.txt              # Python bağımlılıkları
│
├── src/                          # Kaynak kodları
│   ├── __init__.py
│   ├── router/                   # Router modülü
│   │   ├── __init__.py
│   │   ├── classifier.py         # Intent sınıflandırıcı
│   │   └── intent_data.json      # Eğitim verisi
│   │
│   ├── experts/                  # Uzman LoRA yönetimi
│   │   ├── __init__.py
│   │   └── lora_manager.py
│   │
│   ├── memory/                   # Hafıza sistemi
│   │   ├── __init__.py
│   │   ├── chromadb_handler.py
│   │   └── context_buffer.py
│   │
│   ├── inference/                # Model inference
│   │   ├── __init__.py
│   │   └── mlx_inference.py
│   │
│   └── lifecycle/                # Yaşam döngüsü
│       ├── __init__.py
│       ├── sync_handler.py       # Gündüz modu
│       └── async_processor.py    # Gece modu
│
├── models/                       # Base modeller
│   └── qwen-2.5-3b-instruct/
│
├── adapters/                     # LoRA adaptörleri
│   ├── adapter_tr_chat/
│   └── adapter_python_coder/
│
├── data/                         # Veri dosyaları
│   ├── chromadb/                 # Vector DB
│   ├── training/                 # Eğitim verileri
│   └── intents/                  # Intent örnekleri
│
├── logs/                         # Log dosyaları
│   └── conversations/
│
├── scripts/                      # Yardımcı scriptler
│   ├── download_model.py
│   ├── train_lora.py
│   └── night_processor.py
│
└── tests/                        # Testler
    ├── test_router.py
    └── test_inference.py
```

---

Bu doküman projemizin anayasasıdır. Kaybolursak buraya döneceğiz. 🧭
