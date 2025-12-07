# 🏗️ EVO-TR Sistem Mimarisi

**Bu döküman versiyondan bağımsızdır ve projenin genel sistem mimarisini açıklar.**

---

## 🎯 Proje Hedefi

**EVO-TR** (Evolvable Turkish AI), Mac Mini M4 üzerinde çalışan, sürekli öğrenen bir AI asistanıdır.

### Ana Özellikler
- 🇹🇷 Doğal Türkçe iletişim
- 🐍 Python kod yardımı
- 🧠 Konuşma belleği (RAG)
- 🔄 Sürekli öğrenme döngüsü
- ⚡ Yerel çalışma (Apple Silicon optimizasyonu)

---

## 🏛️ Yüksek Seviye Mimari

```
┌─────────────────────────────────────────────────────────────────┐
│                        KULLANICI ARAYÜZÜ                        │
│                   (CLI / Web API / WebSocket)                   │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                            │
│              (İstek koordinasyonu ve akış kontrolü)             │
└──────┬──────────────────────────────────────────────┬───────────┘
       │                                              │
       ▼                                              ▼
┌──────────────┐                             ┌─────────────────┐
│   ROUTER     │                             │     MEMORY      │
│ (Intent →    │                             │   (RAG + Chat   │
│  Expert)     │                             │    History)     │
└──────┬───────┘                             └────────┬────────┘
       │                                              │
       ▼                                              │
┌──────────────────────────────────────────┐         │
│              EXPERT LAYER                │◄────────┘
│  ┌─────────┐ ┌─────────┐ ┌─────────┐    │
│  │TR Chat  │ │Python   │ │Math     │    │
│  │Expert   │ │Expert   │ │Expert   │    │
│  └────┬────┘ └────┬────┘ └────┬────┘    │
│       │           │           │          │
│  ┌────▼────┐ ┌────▼────┐ ┌────▼────┐    │
│  │tr_chat  │ │python   │ │math     │    │
│  │LoRA     │ │LoRA     │ │LoRA     │    │
│  └─────────┘ └─────────┘ └─────────┘    │
└──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│            MLX INFERENCE ENGINE          │
│         (Base Model + LoRA Fusion)       │
└──────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────┐
│            QWEN 2.5 3B INSTRUCT          │
│              (Base Model)                │
└──────────────────────────────────────────┘
```

---

## 📦 Bileşen Detayları

### 1. Orchestrator (`src/orchestrator.py`)

Ana koordinatör modülü. Tüm bileşenler arasındaki iletişimi yönetir.

```python
class Orchestrator:
    def __init__(self):
        self.router = ExpertRouter()
        self.memory = ConversationMemory()
        self.experts = {
            "tr_chat": TrChatExpert(),
            "python_coder": PythonExpert(),
            ...
        }
    
    async def process(self, user_input: str) -> str:
        # 1. Memory'den bağlam al
        context = self.memory.get_context(user_input)
        
        # 2. Intent belirle ve expert seç
        intent = self.router.classify(user_input)
        expert = self.experts[intent]
        
        # 3. Expert ile yanıt üret
        response = await expert.generate(user_input, context)
        
        # 4. Memory'ye kaydet
        self.memory.store(user_input, response)
        
        return response
```

**Sorumluluklar:**
- ✅ İstek akışı koordinasyonu
- ✅ Bileşen yaşam döngüsü yönetimi
- ✅ Hata yönetimi
- ✅ Logging

---

### 2. Router (`src/router/`)

Kullanıcı girdisini analiz ederek doğru uzmanı seçer.

```
router/
├── intent_classifier.py   # Intent sınıflandırma
└── expert_router.py       # Expert seçimi
```

**Intent Türleri:**
| Intent | Açıklama | Expert |
|--------|----------|--------|
| `tr_chat` | Türkçe genel sohbet | TrChatExpert |
| `python_code` | Python programlama | PythonExpert |
| `math` | Matematik soruları | MathExpert |
| `history` | Tarih soruları | HistoryExpert |
| `science` | Bilim soruları | ScienceExpert |

**Yönlendirme Mantığı:**
```python
def classify(self, text: str) -> str:
    # 1. Keyword matching
    # 2. Embedding similarity
    # 3. Fallback: tr_chat
    return intent
```

---

### 3. Experts (`src/experts/`)

Her alan için özelleşmiş uzman modülleri.

```
experts/
├── base_expert.py         # Tüm expertler için temel sınıf
├── tr_chat_expert.py      # Türkçe sohbet
├── python_expert.py       # Python programlama
├── math_expert.py         # Matematik
├── history_expert.py      # Tarih
└── science_expert.py      # Bilim
```

**Expert Yapısı:**
```python
class BaseExpert:
    def __init__(self, adapter_path: str):
        self.adapter_path = adapter_path
        self.system_prompt = "..."
    
    def prepare_prompt(self, user_input: str, context: str) -> str:
        ...
    
    async def generate(self, user_input: str, context: str) -> str:
        prompt = self.prepare_prompt(user_input, context)
        return await self.inference.generate(prompt, self.adapter_path)
```

---

### 4. Inference Engine (`src/inference/`)

MLX tabanlı model çıkarım motoru.

```
inference/
├── base_inference.py      # Temel inference sınıfı
├── mlx_inference.py       # MLX implementasyonu
└── adapter_manager.py     # LoRA adaptör yönetimi
```

**Özellikler:**
- ⚡ Apple Silicon optimizasyonu (Metal GPU)
- 🔄 Dinamik LoRA yükleme/boşaltma
- 🧵 Async generation desteği
- 📊 Token/performans metrikleri

```python
class MLXInference:
    def __init__(self, base_model_path: str):
        self.model = load_model(base_model_path)
        self.tokenizer = load_tokenizer(base_model_path)
    
    async def generate(self, prompt: str, adapter_path: str = None) -> str:
        if adapter_path:
            model = fuse_lora(self.model, adapter_path)
        
        tokens = self.tokenizer.encode(prompt)
        output = model.generate(tokens, ...)
        return self.tokenizer.decode(output)
```

---

### 5. Memory System (`src/memory/`)

Konuşma belleği ve RAG sistemi.

```
memory/
├── conversation_memory.py  # Kısa/uzun süreli bellek
├── chroma_store.py         # ChromaDB vektör deposu
└── rag_retriever.py        # Retrieval-Augmented Generation
```

**Bellek Katmanları:**
```
┌─────────────────────────────────────────┐
│          KISA SÜRELİ BELLEK             │
│    (Son N konuşma - in-memory)          │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│          UZUN SÜRELİ BELLEK             │
│         (ChromaDB - persistent)         │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│            RAG RETRIEVER                │
│  (Semantic search + context assembly)   │
└─────────────────────────────────────────┘
```

---

### 6. Lifecycle Management (`src/lifecycle/`)

Sürekli öğrenme ve adaptasyon.

```
lifecycle/
├── active_learning.py      # Aktif öğrenme
├── incremental_trainer.py  # Artımlı eğitim
└── preference_learning.py  # Tercih öğrenme
```

**Öğrenme Döngüsü:**
```
Kullanıcı Geri Bildirimi
         │
         ▼
┌─────────────────┐
│ Feedback Toplama │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Veri Hazırlama  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Incremental     │
│ LoRA Training   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Adaptör         │
│ Güncelleme      │
└─────────────────┘
```

---

### 7. Web Interface (`src/web/`)

REST API ve WebSocket desteği.

```
web/
├── api.py           # FastAPI REST endpoints
└── websocket.py     # Real-time WebSocket
```

**API Endpoints:**
| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/chat` | Sohbet mesajı gönder |
| GET | `/history` | Konuşma geçmişi |
| POST | `/feedback` | Geri bildirim gönder |
| GET | `/health` | Sistem durumu |

---

## 🔄 Veri Akışı

### Sohbet Akışı

```
1. Kullanıcı mesaj girer
   └─► CLI/Web API

2. Orchestrator mesajı alır
   ├─► Memory'den bağlam çeker
   └─► Router'a intent sorgusu

3. Router intent belirler
   └─► "python_code", "tr_chat", vs.

4. İlgili Expert seçilir
   └─► PythonExpert, TrChatExpert, vs.

5. Expert prompt hazırlar
   ├─► System prompt
   ├─► Context (memory'den)
   └─► User input

6. MLX Inference çalışır
   ├─► Base model yükle
   ├─► LoRA adaptör fuse et
   └─► Generate

7. Yanıt kullanıcıya döner
   └─► Memory'ye kaydet
```

---

## 🛠️ Teknoloji Stack

### Core
| Bileşen | Teknoloji | Versiyon |
|---------|-----------|----------|
| Runtime | Python | 3.11+ |
| ML Framework | MLX | 0.30+ |
| LLM Library | mlx_lm | 0.28+ |
| Vector DB | ChromaDB | 0.4+ |

### Model
| Bileşen | Model | Boyut |
|---------|-------|-------|
| Base Model | Qwen-2.5-3B-Instruct | ~6GB |
| LoRA Rank | 8-16 | ~50MB/adaptör |

### API
| Bileşen | Teknoloji |
|---------|-----------|
| REST API | FastAPI |
| WebSocket | Starlette |
| Async | asyncio |

### Veri
| Bileşen | Format |
|---------|--------|
| Training Data | JSONL (messages format) |
| Config | YAML |
| Logs | JSONL |

---

## 📊 Performans Hedefleri

| Metrik | Hedef | Açıklama |
|--------|-------|----------|
| Latency (ilk token) | <500ms | İlk token üretim süresi |
| Throughput | 30+ tok/s | Token üretim hızı |
| Memory | <8GB | Maksimum RAM kullanımı |
| LoRA Switch | <1s | Adaptör değiştirme süresi |

---

## 🔒 Güvenlik

### API Anahtarları
- `.env` dosyasında saklanır
- Git'e dahil edilmez (`.gitignore`)
- Environment variables olarak yüklenir

### Veri Gizliliği
- Tüm veriler yerel makinede
- Cloud'a veri gönderilmez
- Konuşma logları şifrelenebilir

---

## 📈 Ölçeklenebilirlik

### Yatay Ölçekleme
- Birden fazla expert paralel çalışabilir
- Farklı domainler için yeni expertler eklenebilir

### Dikey Ölçekleme
- Daha büyük base model kullanılabilir (7B, 14B)
- Daha yüksek LoRA rank
- Daha fazla training verisi

---

## 🧪 Test Stratejisi

```
tests/
├── Unit Tests           # Bileşen bazlı testler
├── Integration Tests    # Bileşenler arası testler
└── E2E Tests           # Uçtan uca testler
```

**Test Çalıştırma:**
```bash
# Tüm testler
pytest tests/

# Belirli modül
pytest tests/test_router.py

# Coverage
pytest --cov=src tests/
```

---

## 🔧 Geliştirme Ortamı

### Kurulum
```bash
# Virtual environment
python -m venv .venv
source .venv/bin/activate

# Bağımlılıklar
pip install -r requirements.txt

# Model indirme
python scripts/download_base_model.py
```

### Geliştirme Döngüsü
1. Feature branch oluştur
2. Testleri yaz
3. Kodu geliştir
4. Testleri çalıştır
5. PR oluştur

---

## 📚 İlgili Dökümanlar

- [PROJECT-STRUCTURE.md](./PROJECT-STRUCTURE.md) - Dizin yapısı
- [COMPONENTS.md](./COMPONENTS.md) - Bileşen detayları
- [v2/TODO.md](../v2/TODO.md) - Güncel görevler
- [v2/MEMORY.md](../v2/MEMORY.md) - Güncel durum
