# 📘 EVO-TR: Otonom ve Modüler YZ Mimari Dokümantasyonu

**Sürüm:** 1.1 (PoC - Tamamlandı)  
**Tarih:** 03 Aralık 2025  
**Temel Model:** Qwen-2.5-3B-Instruct (MLX 4-bit, 1.6GB)  
**Donanım:** Mac Mini M4 (Apple Silicon)  
**Durum:** ✅ 6/6 Faz Tamamlandı | 93 Test Geçti

---

## 🚀 Hızlı Başlangıç

```bash
cd /Users/kaan/Desktop/Kaan/Personal/agı-llm
source .venv/bin/activate
python scripts/chat_cli.py
```

Detaylı kullanım için: [QUICKSTART.md](./QUICKSTART.md)

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
* **Kısa Süreli Hafıza:** ContextBuffer (Son 10-20 mesaj, token-aware)
* **Uzun Süreli Hafıza (RAG):** `ChromaDB` (persistent)
* **Embedding Model:** `paraphrase-multilingual-MiniLM-L12-v2` (384d, Türkçe destekli)

### D. Yaşam Döngüsü Katmanı (The Loop)
* **Senkron (Gündüz):** `SyncHandler` - Real-time chat, session management
* **Asenkron (Gece):** `AsyncProcessor` - Log analizi, pattern detection
* **Self-Improvement:** `SelfImprovementPipeline` - Otomatik iyileştirme, re-training triggers

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
Qwen-2.5-3B-Instruct (4-bit): ~1.6GB VRAM
LoRA Adapters: ~27MB each (python_coder: 26.6MB)
ChromaDB: ~500MB (başlangıç)
Router Model: ~471MB (sentence-transformer)
─────────────────────────────────────────
Toplam Tahmini: ~3-4GB
```

---

## 4. Proje Durumu (Güncel)

| Faz | İsim | Durum | Test |
|-----|------|-------|------|
| 0 | Altyapı ve Kurulum | ✅ Tamamlandı | - |
| 1 | Router | ✅ Tamamlandı | 15/15 |
| 2 | Türkçe Uzman (LoRA) | ✅ Tamamlandı | - |
| 3 | Python Uzman (LoRA) | ✅ Tamamlandı | 4/4 |
| 4 | Hafıza ve RAG | ✅ Tamamlandı | 25/25 |
| 5 | Entegrasyon | ✅ Tamamlandı | 25/25 |
| 6 | Yaşam Döngüsü | ✅ Tamamlandı | 28/28 |

**Toplam: 93 test geçti!**

---

## 5. Veri Setleri ve Eğitim Sonuçları

| Uzmanlık Alanı | Kaynak Veri Setleri | Örnek Sayısı | Sonuç |
|----------------|---------------------|--------------|-------|
| **Router** | Elle hazırlanmış Intent seti | 185 örnek, 7 kategori | ~50ms latency |
| **Türkçe Uzmanı** | `CohereForAI/aya_dataset (tr)` + Manuel | 4,147 örnek | val_loss=1.86 |
| **Python Uzmanı** | `HumanEval` + `MBPP` + `CodeAlpaca` | 13,334 örnek | val_loss=0.551 |

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

## 8. Dizin Yapısı (Güncel)

```
agı-llm/
├── .env                          # Ortam değişkenleri
├── .venv/                        # Virtual environment (Python 3.11)
├── QUICKSTART.md                 # Hızlı başlangıç kılavuzu
├── EVO-TR-DOCUMENTATION.md       # Bu doküman
├── EVO-TR-TODO-MASTER.md         # Ana todo listesi
├── AGENT-MEMORY.md               # Geliştirme süreç kaydı
├── requirements.txt              # Python bağımlılıkları
│
├── src/                          # Kaynak kodları
│   ├── __init__.py
│   ├── orchestrator.py           # 🎯 Ana EvoTR sınıfı (tüm sistemi birleştirir)
│   │
│   ├── router/                   # Router modülü
│   │   ├── __init__.py
│   │   ├── classifier.py         # IntentClassifier (7 kategori)
│   │   └── api.py                # Router API
│   │
│   ├── experts/                  # Uzman LoRA yönetimi
│   │   ├── __init__.py
│   │   └── lora_manager.py       # LoRA adapter hot-swap
│   │
│   ├── memory/                   # Hafıza sistemi
│   │   ├── __init__.py
│   │   ├── chromadb_handler.py   # Uzun süreli (RAG)
│   │   ├── context_buffer.py     # Kısa süreli
│   │   └── memory_manager.py     # Unified manager
│   │
│   ├── inference/                # Model inference
│   │   ├── __init__.py
│   │   └── mlx_inference.py      # MLX-LM generation
│   │
│   └── lifecycle/                # Yaşam döngüsü
│       ├── __init__.py
│       ├── logger.py             # JSON structured logging
│       ├── sync_handler.py       # Gündüz modu (real-time)
│       ├── async_processor.py    # Gece modu (analiz)
│       └── self_improvement.py   # Self-improvement pipeline
│
├── models/                       # Base modeller
│   ├── base/
│   │   └── qwen-2.5-3b-instruct/ # 1.6GB (4-bit MLX)
│   └── router/
│       └── sentence_transformer/ # 471MB
│
├── adapters/                     # LoRA adaptörleri
│   ├── python_coder/             # 26.6MB
│   ├── tr_chat/                  # Türkçe v1
│   └── tr_chat_v2/               # Türkçe v2
│
├── data/                         # Veri dosyaları
│   ├── chromadb/                 # Vector DB (persistent)
│   ├── training/                 # Eğitim verileri
│   │   ├── python_coder_mlx/     # 13,334 örnek
│   │   └── tr_chat_mlx/          # 4,147 örnek
│   └── intents/                  # Intent örnekleri (185)
│
├── logs/                         # Log dosyaları
│   ├── conversations_*.jsonl     # Konuşma logları
│   ├── performance_*.jsonl       # Performance metrikleri
│   ├── errors_*.jsonl            # Hata logları
│   └── analysis/                 # Gece analiz raporları
│       └── improvements/         # Self-improvement raporları
│
├── configs/                      # Konfigürasyon dosyaları
│   ├── settings.py               # Python settings
│   ├── lora_python_config.yaml   # LoRA eğitim config
│   └── com.evotr.night-analysis.plist  # macOS LaunchD
│
├── scripts/                      # Yardımcı scriptler
│   ├── chat_cli.py               # 🚀 Ana chat arayüzü
│   ├── run_analysis.py           # Gece analizi
│   ├── router_demo.py            # Router demo
│   ├── memory_rag_demo.py        # Memory demo
│   └── verify_setup.py           # Kurulum doğrulama
│
├── tests/                        # Testler (93 toplam)
│   ├── test_router.py            # 15 test
│   ├── test_memory.py            # 25 test
│   ├── test_integration.py       # 25 test
│   └── test_lifecycle.py         # 28 test
│
└── todos/                        # Faz-bazlı todo dosyaları
    ├── FAZ-0-ALTYAPI-KURULUM.md
    ├── FAZ-1-ROUTER.md
    ├── FAZ-2-TURKCE-UZMAN.md
    ├── FAZ-3-PYTHON-UZMAN.md
    ├── FAZ-4-HAFIZA-RAG.md
    ├── FAZ-5-ENTEGRASYON.md
    └── FAZ-6-YASAM-DONGUSU.md
```

---

## 9. Kullanım

### Hızlı Başlangıç
```bash
source .venv/bin/activate
python scripts/chat_cli.py
```

### Gece Analizi
```bash
python scripts/run_analysis.py --days 7
```

### Testler
```bash
python -m pytest tests/ -v
```

Detaylı kullanım için: [QUICKSTART.md](./QUICKSTART.md)

---

## 10. 🚀 Gelecek Vizyonu: AGI'ya Giden Yol

**Mevcut Durum:** "Bebek" seviyesi - Temel yetenekler kazanıldı  
**Hedef:** Otonom, sürekli öğrenen, kendi kendini geliştiren AGI sistemi

### 10.1 Kısa Vadeli Hedefler (v1.x)
- [ ] Daha fazla uzman LoRA (matematik, bilim, tarih)
- [ ] Gelişmiş gece modu scheduler (cron-based)
- [ ] Otomatik adapter yönetimi ve versiyonlama
- [ ] Web arayüzü (FastAPI + React)

### 10.2 Orta Vadeli Hedefler (v2.x)
- [ ] **Continuous Learning (Sürekli Öğrenme)**
  - Kullanıcı etkileşimlerinden aktif öğrenme
  - Hatalardan otomatik düzeltme
  - Preference learning (kullanıcı tercihlerini öğrenme)

- [ ] **Test-Time Training (TTT)**
  - Inference sırasında anlık adaptasyon
  - Context-aware model güncelleme
  - One-shot/few-shot learning iyileştirmeleri

- [ ] **Multi-Modal Yetenekler**
  - Görüntü anlama (Vision LoRA)
  - Ses işleme (Audio LoRA)
  - Kod görselleştirme

### 10.3 Uzun Vadeli Vizyon (v3.x - AGI Yolu)
- [ ] **Self-Directed Learning**
  - Kendi eksiklerini tespit etme
  - Otomatik veri toplama ve eğitim
  - Öğrenme stratejisi optimizasyonu

- [ ] **Meta-Learning (Learning to Learn)**
  - Yeni görevlere hızlı adaptasyon
  - Transfer learning optimizasyonu
  - Domain-agnostic skill acquisition

- [ ] **Hibrit Mimari**
  - Symbolic + Neural reasoning
  - Knowledge graph entegrasyonu
  - Causal reasoning yetenekleri

- [ ] **Otonom Araştırma**
  - Web scraping + knowledge synthesis
  - Paper reading ve özetleme
  - Yeni model mimarileri keşfi

### 10.4 Felsefe: "Bebek -> Çocuk -> Uzman -> Usta"

```
Bebek (v1.0) ──────────────────────────────────────────────────▶ AGI
   │                                                              │
   ├─ Temel anlama ✅                                             │
   ├─ Sohbet yeteneği ✅                                          │
   ├─ Kod yazma ✅                                                │
   ├─ Hafıza ✅                                                   │
   │                                                              │
   ▼ Sürekli Öğrenme                                             │
   ├─ TTT ile anlık adaptasyon                                   │
   ├─ Gece modu ile deneyim işleme                               │
   ├─ Otomatik skill acquisition                                 │
   │                                                              │
   ▼ Meta-Learning                                               │
   ├─ Öğrenmeyi öğrenme                                          │
   ├─ Strateji optimizasyonu                                     │
   └─────────────────────────────────────────────────────────────┘
```

**Temel İlkeler:**
1. **Modülerlik:** Her yetenek bağımsız, değiştirilebilir
2. **Verimlilik:** Edge deployment, düşük kaynak tüketimi
3. **Şeffaflık:** Karar süreçleri izlenebilir
4. **Güvenlik:** Self-improvement güvenlik sınırları

---

Bu doküman projemizin anayasasıdır. Kaybolursak buraya döneceğiz. 🧭
