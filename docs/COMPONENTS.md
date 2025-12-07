# 🧩 EVO-TR Bileşen Detayları

**Bu döküman versiyondan bağımsızdır ve projenin bileşenlerini detaylı açıklar.**

---

## 📋 İçindekiler

1. [Base Model](#1-base-model)
2. [LoRA Adaptörler](#2-lora-adaptörler)
3. [Router Sistemi](#3-router-sistemi)
4. [Expert Modülleri](#4-expert-modülleri)
5. [Memory Sistemi](#5-memory-sistemi)
6. [Inference Engine](#6-inference-engine)
7. [Lifecycle Management](#7-lifecycle-management)
8. [Veri Üretim Pipeline](#8-veri-üretim-pipeline)

---

## 1. Base Model

### Qwen 2.5 3B Instruct


**Konum:** `models/base/qwen-2.5-3b-instruct/`

| Özellik | Değer |
|---------|-------|
| Parametre | 3 Milyar |
| Context | 32K token |
| Format | Chat/Instruct |
| Boyut | ~6GB |

**Neden Qwen 2.5 3B?**
- ✅ Mac Mini M4 için optimize boyut
- ✅ Türkçe dil desteği
- ✅ Kod anlama yeteneği
- ✅ MLX uyumluluğu

**Chat Format:**
```
<|im_start|>system
Sen EVO-TR, yardımcı bir Türkçe AI asistanısın.
<|im_end|>
<|im_start|>user
Merhaba, nasılsın?
<|im_end|>
<|im_start|>assistant
Merhaba! Ben bir AI olarak duygularım yok ama size yardımcı olmaya hazırım!
<|im_end|>
```

---

## 2. LoRA Adaptörler

### 2.1 Adaptör Yapısı

**Konum:** `adapters/`

```
adapters/
├── tr_chat/           # V1 - Türkçe sohbet
├── tr_chat_v2/        # V2 - Türkçe sohbet (geliştirilmiş)
├── python_coder/      # V1 - Python kod
├── python_coder_v2/   # V2 - Python kod (geliştirilmiş)
├── math_expert/       # Matematik
├── history_expert/    # Tarih
└── science_expert/    # Bilim
```

### 2.2 LoRA Parametreleri

| Parametre | Açıklama | Tipik Değer |
|-----------|----------|-------------|
| `rank` | Adaptör boyutu | 8-16 |
| `alpha` | Öğrenme ölçeği | 16-32 |
| `layers` | Uygulanacak katman sayısı | 8-16 |
| `target_modules` | Hedef modüller | q_proj, v_proj |

### 2.3 Adaptör Performansları

| Adaptör | Val Loss | İyileşme |
|---------|----------|----------|
| tr_chat_v2 | 0.257 | %92 |
| python_coder_v2 | TBD | TBD |

### 2.4 Eğitim Config Örneği

```yaml
# configs/lora_tr_config_v2.yaml
model: models/base/qwen-2.5-3b-instruct
data: data/training/gemma_tr_chat
train: true
adapter_path: adapters/tr_chat_v2

batch_size: 4
learning_rate: 1e-5
iters: 500
val_batches: 10
steps_per_eval: 50
steps_per_save: 250

lora_layers: 8
lora_parameters:
  rank: 8
  alpha: 16
  scale: 1.0
  dropout: 0.0

max_seq_length: 1024
grad_checkpoint: true
```

---

## 3. Router Sistemi

### 3.1 Intent Sınıflandırma

**Dosya:** `src/router/intent_classifier.py`

```python
class IntentClassifier:
    """Kullanıcı girdisini intent'e dönüştürür."""
    
    INTENTS = {
        "tr_chat": ["merhaba", "nasılsın", "teşekkür", ...],
        "python_code": ["python", "kod", "fonksiyon", "hata", ...],
        "math": ["hesapla", "toplam", "çarp", "denklem", ...],
        "history": ["tarih", "osmanlı", "savaş", "antik", ...],
        "science": ["bilim", "fizik", "kimya", "biyoloji", ...]
    }
    
    def classify(self, text: str) -> str:
        """Intent belirle."""
        text_lower = text.lower()
        
        # Keyword matching
        for intent, keywords in self.INTENTS.items():
            if any(kw in text_lower for kw in keywords):
                return intent
        
        # Fallback
        return "tr_chat"
```

### 3.2 Expert Router

**Dosya:** `src/router/expert_router.py`

```python
class ExpertRouter:
    """Intent'e göre expert seçer."""
    
    def __init__(self):
        self.classifier = IntentClassifier()
        self.intent_to_expert = {
            "tr_chat": "TrChatExpert",
            "python_code": "PythonExpert",
            "math": "MathExpert",
            "history": "HistoryExpert",
            "science": "ScienceExpert"
        }
    
    def route(self, text: str) -> str:
        """Expert adını döndür."""
        intent = self.classifier.classify(text)
        return self.intent_to_expert.get(intent, "TrChatExpert")
```

### 3.3 Intent Mapping Config

**Dosya:** `configs/intent_mapping.json`

```json
{
  "tr_chat": {
    "adapter": "adapters/tr_chat_v2",
    "expert": "TrChatExpert",
    "priority": 1
  },
  "python_code": {
    "adapter": "adapters/python_coder_v2",
    "expert": "PythonExpert",
    "priority": 2
  },
  ...
}
```

---

## 4. Expert Modülleri

### 4.1 Base Expert

**Dosya:** `src/experts/base_expert.py`

```python
from abc import ABC, abstractmethod

class BaseExpert(ABC):
    """Tüm expertler için temel sınıf."""
    
    def __init__(self, adapter_path: str, inference_engine):
        self.adapter_path = adapter_path
        self.inference = inference_engine
        self.system_prompt = self.get_system_prompt()
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Expert'e özel sistem promptu."""
        pass
    
    def prepare_messages(self, user_input: str, context: str = "") -> list:
        """Chat format için mesaj listesi hazırla."""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        if context:
            messages.append({
                "role": "system", 
                "content": f"Önceki bağlam:\n{context}"
            })
        
        messages.append({"role": "user", "content": user_input})
        return messages
    
    async def generate(self, user_input: str, context: str = "") -> str:
        """Yanıt üret."""
        messages = self.prepare_messages(user_input, context)
        return await self.inference.generate(messages, self.adapter_path)
```

### 4.2 Türkçe Sohbet Expert

**Dosya:** `src/experts/tr_chat_expert.py`

```python
class TrChatExpert(BaseExpert):
    """Türkçe genel sohbet uzmanı."""
    
    def __init__(self, inference_engine):
        super().__init__(
            adapter_path="adapters/tr_chat_v2",
            inference_engine=inference_engine
        )
    
    def get_system_prompt(self) -> str:
        return """Sen EVO-TR, samimi ve yardımsever bir Türkçe AI asistanısın.

Özelliklerin:
- Doğal ve akıcı Türkçe kullanırsın
- Türk kültürünü ve geleneklerini bilirsin
- Empati kurar, duygusal destek verirsin
- Atasözleri ve deyimleri yerinde kullanırsın
- Kısa, öz ve anlaşılır cevaplar verirsin

Yanıt verirken:
- Samimi ama saygılı ol
- Gerektiğinde emoji kullan
- Uzun açıklamalardan kaçın"""
```

### 4.3 Python Expert

**Dosya:** `src/experts/python_expert.py`

```python
class PythonExpert(BaseExpert):
    """Python programlama uzmanı."""
    
    def __init__(self, inference_engine):
        super().__init__(
            adapter_path="adapters/python_coder_v2",
            inference_engine=inference_engine
        )
    
    def get_system_prompt(self) -> str:
        return """Sen EVO-TR Python Uzmanı, deneyimli bir Python geliştiricisisin.

Özelliklerin:
- Python 3.10+ syntax bilirsin
- Clean code prensiplerini uygularsın
- Type hints kullanırsın
- Docstring yazarsın
- Error handling yaparsın

Kod yazarken:
- PEP 8 standardına uy
- Anlamlı değişken isimleri kullan
- Karmaşık kodları yorumla
- Örneklerle açıkla"""
```

---

## 5. Memory Sistemi

### 5.1 Conversation Memory

**Dosya:** `src/memory/conversation_memory.py`

```python
from collections import deque
from datetime import datetime

class ConversationMemory:
    """Kısa ve uzun süreli konuşma belleği."""
    
    def __init__(self, short_term_limit: int = 10):
        self.short_term = deque(maxlen=short_term_limit)
        self.long_term = ChromaStore()
    
    def add(self, user_input: str, response: str):
        """Yeni konuşma ekle."""
        entry = {
            "user": user_input,
            "assistant": response,
            "timestamp": datetime.now().isoformat()
        }
        
        # Kısa süreli belleğe ekle
        self.short_term.append(entry)
        
        # Uzun süreli belleğe kaydet
        self.long_term.store(entry)
    
    def get_context(self, query: str, k: int = 3) -> str:
        """İlgili bağlamı getir."""
        # Kısa süreli + RAG birleştir
        short_context = self._format_short_term()
        rag_context = self.long_term.retrieve(query, k)
        
        return f"{short_context}\n\n{rag_context}"
```

### 5.2 ChromaDB Store

**Dosya:** `src/memory/chroma_store.py`

```python
import chromadb
from chromadb.config import Settings

class ChromaStore:
    """ChromaDB vektör deposu."""
    
    def __init__(self, persist_dir: str = "data/chromadb"):
        self.client = chromadb.Client(Settings(
            persist_directory=persist_dir,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection(
            name="conversations",
            metadata={"hnsw:space": "cosine"}
        )
    
    def store(self, entry: dict):
        """Konuşmayı depola."""
        text = f"User: {entry['user']}\nAssistant: {entry['assistant']}"
        
        self.collection.add(
            documents=[text],
            ids=[entry['timestamp']],
            metadatas=[{"timestamp": entry['timestamp']}]
        )
    
    def retrieve(self, query: str, k: int = 3) -> str:
        """Benzer konuşmaları getir."""
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        
        return "\n---\n".join(results['documents'][0])
```

### 5.3 RAG Retriever

**Dosya:** `src/memory/rag_retriever.py`

```python
class RAGRetriever:
    """Retrieval-Augmented Generation."""
    
    def __init__(self, chroma_store: ChromaStore):
        self.store = chroma_store
    
    def retrieve_and_format(self, query: str, k: int = 3) -> str:
        """Bağlam getir ve formatla."""
        docs = self.store.retrieve(query, k)
        
        if not docs:
            return ""
        
        formatted = "📚 İlgili önceki konuşmalar:\n\n"
        for i, doc in enumerate(docs, 1):
            formatted += f"{i}. {doc}\n\n"
        
        return formatted
```

---

## 6. Inference Engine

### 6.1 MLX Inference

**Dosya:** `src/inference/mlx_inference.py`

```python
import mlx.core as mx
from mlx_lm import load, generate

class MLXInference:
    """MLX tabanlı model çıkarımı."""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Base modeli yükle."""
        self.model, self.tokenizer = load(self.model_path)
    
    async def generate(
        self, 
        messages: list, 
        adapter_path: str = None,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """Yanıt üret."""
        
        # Prompt hazırla
        prompt = self.tokenizer.apply_chat_template(
            messages, 
            add_generation_prompt=True,
            tokenize=False
        )
        
        # LoRA adaptör varsa fuse et
        model = self.model
        if adapter_path:
            model = self._fuse_adapter(adapter_path)
        
        # Generate
        response = generate(
            model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=max_tokens,
            temp=temperature
        )
        
        return response
    
    def _fuse_adapter(self, adapter_path: str):
        """LoRA adaptörü modele fuse et."""
        from mlx_lm import load
        
        model, _ = load(
            self.model_path,
            adapter_path=adapter_path
        )
        return model
```

### 6.2 Adapter Manager

**Dosya:** `src/inference/adapter_manager.py`

```python
from pathlib import Path

class AdapterManager:
    """LoRA adaptör yönetimi."""
    
    def __init__(self, adapters_dir: str = "adapters"):
        self.adapters_dir = Path(adapters_dir)
        self.loaded_adapters = {}
    
    def list_adapters(self) -> list:
        """Mevcut adaptörleri listele."""
        return [d.name for d in self.adapters_dir.iterdir() if d.is_dir()]
    
    def get_latest(self, adapter_name: str) -> str:
        """En son checkpoint'i getir."""
        adapter_dir = self.adapters_dir / adapter_name
        
        checkpoints = sorted(adapter_dir.glob("*_adapters.safetensors"))
        if checkpoints:
            return str(checkpoints[-1].parent)
        
        return str(adapter_dir)
    
    def validate(self, adapter_path: str) -> bool:
        """Adaptör geçerliliğini kontrol et."""
        path = Path(adapter_path)
        
        required_files = [
            "adapter_config.json",
            # checkpoint files
        ]
        
        return path.exists() and any(path.glob("*.safetensors"))
```

---

## 7. Lifecycle Management

### 7.1 Active Learning

**Dosya:** `src/lifecycle/active_learning.py`

```python
class ActiveLearning:
    """Aktif öğrenme yönetimi."""
    
    def __init__(self, data_dir: str = "data/active_learning"):
        self.data_dir = Path(data_dir)
        self.feedback_queue = []
    
    def collect_feedback(self, conversation: dict, rating: int, comment: str = ""):
        """Kullanıcı geri bildirimi topla."""
        feedback = {
            "conversation": conversation,
            "rating": rating,  # 1-5
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        }
        self.feedback_queue.append(feedback)
        self._save_feedback(feedback)
    
    def identify_weak_areas(self) -> list:
        """Düşük puanlı alanları belirle."""
        # Rating < 3 olan konuşmaları analiz et
        weak = []
        for fb in self.feedback_queue:
            if fb["rating"] < 3:
                weak.append(fb)
        return weak
    
    def prepare_training_data(self) -> list:
        """Eğitim verisi hazırla."""
        # Yüksek puanlı örneklerden veri oluştur
        training_data = []
        for fb in self.feedback_queue:
            if fb["rating"] >= 4:
                training_data.append(fb["conversation"])
        return training_data
```

### 7.2 Incremental Trainer

**Dosya:** `src/lifecycle/incremental_trainer.py`

```python
class IncrementalTrainer:
    """Artımlı LoRA eğitimi."""
    
    def __init__(self, base_model_path: str):
        self.base_model_path = base_model_path
    
    async def train(
        self,
        training_data: list,
        adapter_path: str,
        epochs: int = 1,
        learning_rate: float = 1e-5
    ):
        """Artımlı eğitim yap."""
        
        # Veriyi hazırla
        prepared_data = self._prepare_data(training_data)
        
        # Eğitim config
        config = {
            "model": self.base_model_path,
            "data": prepared_data,
            "adapter_path": adapter_path,
            "epochs": epochs,
            "learning_rate": learning_rate,
            "batch_size": 2,
            "grad_checkpoint": True
        }
        
        # mlx_lm lora komutu çalıştır
        await self._run_training(config)
    
    def _prepare_data(self, data: list) -> str:
        """Veriyi eğitim formatına dönüştür."""
        # JSONL formatında kaydet
        output_path = "data/incremental/train.jsonl"
        
        with open(output_path, "w") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        return "data/incremental"
```

### 7.3 Preference Learning

**Dosya:** `src/lifecycle/preference_learning.py`

```python
class PreferenceLearning:
    """Tercih tabanlı öğrenme (RLHF benzeri)."""
    
    def __init__(self):
        self.preferences = []
    
    def add_preference(self, prompt: str, chosen: str, rejected: str):
        """Tercih çifti ekle."""
        self.preferences.append({
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected
        })
    
    def prepare_dpo_data(self) -> list:
        """DPO formatında veri hazırla."""
        dpo_data = []
        
        for pref in self.preferences:
            dpo_data.append({
                "prompt": pref["prompt"],
                "chosen": pref["chosen"],
                "rejected": pref["rejected"]
            })
        
        return dpo_data
```

---

## 8. Veri Üretim Pipeline

### 8.1 Gemini/Gemma Veri Üretici

**Dosya:** `scripts/gemini_data_generator.py`

```python
class GeminiClient:
    """Gemma 3 27B API istemcisi."""
    
    def __init__(self, api_keys: list):
        self.key_rotator = APIKeyRotator(api_keys)
        self.model = "gemma-3-27b-it"
    
    async def generate(self, prompt: str) -> str:
        """Yanıt üret."""
        api_key = self.key_rotator.get_next_key()
        
        # Rate limit kontrolü
        await self._wait_for_rate_limit()
        
        # API çağrısı
        response = await self._call_api(prompt, api_key)
        
        return response
```

### 8.2 Veri Hazırlama

**Dosya:** `scripts/prepare_gemma_data.py`

```python
def prepare_mlx_format(input_path: str, output_path: str):
    """Ham veriyi MLX formatına dönüştür."""
    
    data = []
    with open(input_path) as f:
        for line in f:
            item = json.loads(line)
            
            # Messages formatına dönüştür
            formatted = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": item["input"]},
                    {"role": "assistant", "content": item["output"]}
                ]
            }
            data.append(formatted)
    
    # Train/valid split
    train, valid = train_test_split(data, test_size=0.1)
    
    # Kaydet
    save_jsonl(f"{output_path}/train.jsonl", train)
    save_jsonl(f"{output_path}/valid.jsonl", valid)
```

---

## 📚 İlgili Dökümanlar

- [PROJECT-STRUCTURE.md](./PROJECT-STRUCTURE.md) - Dizin yapısı
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Sistem mimarisi
- [v2/TODO.md](../v2/TODO.md) - Güncel görevler
- [v2/MEMORY.md](../v2/MEMORY.md) - Güncel durum
