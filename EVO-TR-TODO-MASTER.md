# 🚀 EVO-TR: Master Todo List (Mac Mini M4 Edition)

**Tarih:** 02 Aralık 2025  
**Donanım:** Mac Mini M4 (Apple Silicon)  
**Durum:** PoC (Proof of Concept)

---

## 📋 Genel Bakış

| Faz | İsim | Durum | Tahmini Süre |
|-----|------|-------|--------------|
| 0 | Altyapı ve Kurulum | ⬜ Başlanmadı | 1-2 gün |
| 1 | Router (Yönlendirici) | ⬜ Başlanmadı | 2-3 gün |
| 2 | Türkçe Uzman (LoRA #1) | ⬜ Başlanmadı | 3-4 gün |
| 3 | Python Uzman (LoRA #2) | ⬜ Başlanmadı | 2-3 gün |
| 4 | Hafıza ve RAG | ⬜ Başlanmadı | 2-3 gün |
| 5 | Entegrasyon | ⬜ Başlanmadı | 2-3 gün |
| 6 | Yaşam Döngüsü | ⬜ Başlanmadı | 2-3 gün |

---

## ⬜ Faz 0: Altyapı ve Kurulum (The Skeleton)

*Amaç: Mac M4 üzerinde çalışacak temel ortamı hazırlamak*

### 0.1 Sistem Gereksinimleri Kontrolü
- [ ] macOS sürümü kontrolü (Sonoma 14+ önerilir)
- [ ] Python 3.10+ kurulu mu kontrol et
- [ ] Xcode Command Line Tools kurulu mu kontrol et
- [ ] Homebrew kurulu mu kontrol et

### 0.2 Python Ortamı Kurulumu
- [ ] Proje dizininde virtual environment oluştur
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
- [ ] pip güncelle
- [ ] requirements.txt oluştur

### 0.3 Temel Bağımlılıklar
- [ ] `mlx` kurulumu (Apple ML Framework)
- [ ] `mlx-lm` kurulumu (LLM desteği)
- [ ] `transformers` kurulumu
- [ ] `huggingface_hub` kurulumu
- [ ] `torch` kurulumu (CPU-only, MLX ile uyumluluk için)

### 0.4 Hugging Face Ayarları
- [ ] `.env` dosyasında HF_TOKEN kontrolü
- [ ] `huggingface-cli login` ile giriş yap
- [ ] Token'ı test et: Model erişimi var mı?

### 0.5 Base Model İndirme
- [ ] Qwen-2.5-3B-Instruct MLX formatında indir
  ```bash
  mlx_lm.convert --hf-path Qwen/Qwen2.5-3B-Instruct --mlx-path ./models/qwen-2.5-3b-instruct -q
  ```
- [ ] Model boyutunu kontrol et (~2GB olmalı)
- [ ] "Hello World" testi yap

### 0.6 Dizin Yapısı Oluşturma
- [ ] `src/` ana kaynak dizini
- [ ] `models/` model dizini
- [ ] `adapters/` LoRA adaptör dizini
- [ ] `data/` veri dizini
- [ ] `logs/` log dizini
- [ ] `scripts/` yardımcı script dizini

---

## ⬜ Faz 1: Router (Yönlendirici Zeka)

*Amaç: Gelen sorunun hangi uzmana gitmesi gerektiğine karar veren "Kapı Görevlisi"*

### 1.1 Intent Veri Seti Hazırlama
- [ ] Intent kategorilerini belirle:
  - `general_chat` - Genel sohbet, selamlaşma
  - `turkish_culture` - Türkçe kültür, deyimler
  - `code_python` - Python kodu yazma
  - `code_debug` - Hata ayıklama
  - `memory_recall` - Geçmişi hatırlama
- [ ] Her kategori için 20+ örnek yaz
- [ ] `data/intents/intent_dataset.json` oluştur
- [ ] Veri setini train/val olarak böl (80/20)

### 1.2 Sınıflandırıcı Model Seçimi
- [ ] `distilbert-base-multilingual-cased` indir
- [ ] Alternatif: `sentence-transformers` + cosine similarity
- [ ] Bellek kullanımı test et (<500MB olmalı)

### 1.3 Router Eğitimi
- [ ] `src/router/train_classifier.py` yaz
- [ ] Few-shot learning veya fine-tuning seç
- [ ] Eğitimi başlat
- [ ] Accuracy kontrolü (%90+ hedef)
- [ ] Model'i kaydet: `models/router/`

### 1.4 Router API Yazımı
- [ ] `src/router/classifier.py` oluştur
- [ ] `RouterClassifier` sınıfı yaz
- [ ] `predict(text) -> {"intent": str, "confidence": float}` metodu
- [ ] Confidence threshold ayarla (0.7 önerilen)
- [ ] Düşük confidence için fallback stratejisi

### 1.5 Router Testleri
- [ ] `tests/test_router.py` yaz
- [ ] Edge case'leri test et
- [ ] Latency testi (<50ms hedef)

---

## ⬜ Faz 2: Türkçe Uzman (LoRA #1)

*Amaç: Base modelin Türkçe iletişim yeteneklerini geliştirmek*

### 2.1 Veri Seti Hazırlama
- [ ] `CohereForAI/aya_dataset` Türkçe subset'ini indir
- [ ] `Turkish-Instructions` veri setini incele
- [ ] Veri setlerini birleştir
- [ ] Temizlik yap:
  - Duplice kayıtları kaldır
  - Çok kısa/uzun örnekleri filtrele
  - Format kontrolü
- [ ] Alpaca formatına dönüştür:
  ```json
  {"instruction": "...", "input": "...", "output": "..."}
  ```
- [ ] `data/training/tr_chat_dataset.jsonl` oluştur

### 2.2 QLoRA Eğitim Konfigürasyonu
- [ ] `scripts/train_lora_tr.py` oluştur
- [ ] MLX LoRA parametreleri:
  ```python
  lora_config = {
      "r": 8,                    # LoRA rank
      "lora_alpha": 16,          # Scaling factor
      "lora_dropout": 0.05,
      "target_modules": ["q_proj", "v_proj"]
  }
  ```
- [ ] Training parametreleri:
  ```python
  training_args = {
      "learning_rate": 1e-4,
      "batch_size": 1,           # M4 için güvenli
      "epochs": 3,
      "gradient_accumulation": 4
  }
  ```

### 2.3 Eğitim Süreci
- [ ] Eğitimi başlat
- [ ] Loss değerlerini logla
- [ ] Checkpoint'ler kaydet (her epoch)
- [ ] Eğitim bitince final model kaydet
- [ ] `adapters/adapter_tr_chat/` dizinine taşı

### 2.4 Türkçe Adapter Testi
- [ ] Base + Adapter yükle
- [ ] Test promptları hazırla:
  - Selamlaşma
  - Günlük sohbet
  - Türk kültürü soruları
  - Deyim/atasözü açıklamaları
- [ ] Yanıt kalitesini değerlendir
- [ ] Base model ile karşılaştır

---

## ⬜ Faz 3: Python Uzman (LoRA #2)

*Amaç: Kod yazma ve debugging yeteneklerini geliştirmek*

### 3.1 Veri Seti Hazırlama
- [ ] `openai/humaneval` indir
- [ ] `mbpp` (Mostly Basic Programming Problems) indir
- [ ] Veri setlerini birleştir
- [ ] Python-spesifik format:
  ```json
  {
      "instruction": "Write a function that...",
      "input": "def function_name(params):",
      "output": "complete code here"
  }
  ```
- [ ] `data/training/python_coder_dataset.jsonl` oluştur

### 3.2 QLoRA Eğitim Konfigürasyonu
- [ ] `scripts/train_lora_python.py` oluştur
- [ ] Aynı LoRA parametreleri (Faz 2 ile tutarlı)
- [ ] Code-specific augmentation düşün

### 3.3 Eğitim Süreci
- [ ] Eğitimi başlat
- [ ] Loss takibi
- [ ] `adapters/adapter_python_coder/` dizinine kaydet

### 3.4 Python Adapter Testi
- [ ] Basit fonksiyon yazma
- [ ] Algoritma implementasyonu
- [ ] Bug fixing senaryoları
- [ ] Kod açıklama yetenekleri

---

## ⬜ Faz 4: Hafıza ve RAG Sistemi

*Amaç: Sürekli hatırlayan bir sistem oluşturmak*

### 4.1 ChromaDB Kurulumu
- [ ] `chromadb` paketini kur
- [ ] Persistent storage ayarla
- [ ] `data/chromadb/` dizini oluştur
- [ ] Connection testi yap

### 4.2 Embedding Model Entegrasyonu
- [ ] `emrecan/bert-base-turkish-cased-mean-nli-stsb-tr` indir
- [ ] `sentence-transformers` ile yükle
- [ ] Embedding boyutunu kontrol et
- [ ] Test embedding oluştur

### 4.3 ChromaDB Handler
- [ ] `src/memory/chromadb_handler.py` oluştur
- [ ] `MemoryHandler` sınıfı:
  ```python
  class MemoryHandler:
      def add_memory(text, metadata)
      def search(query, top_k=3)
      def delete(id)
      def clear_all()
  ```
- [ ] Collection yönetimi
- [ ] Metadata schema tanımla

### 4.4 Kısa Süreli Hafıza
- [ ] `src/memory/context_buffer.py` oluştur
- [ ] Son N mesajı tutan buffer
- [ ] Token limiti kontrolü
- [ ] Sliding window mantığı

### 4.5 RAG Pipeline
- [ ] Query -> Embed -> Search -> Retrieve
- [ ] Context augmentation
- [ ] Top-k=3 sınırı
- [ ] Relevance score filtering

---

## ⬜ Faz 5: Sistem Entegrasyonu

*Amaç: Tüm parçaları birleştirmek*

### 5.1 LoRA Manager
- [ ] `src/experts/lora_manager.py` oluştur
- [ ] Adapter yükleme/değiştirme
- [ ] Adapter caching
- [ ] Hot-swap desteği

### 5.2 Inference Engine
- [ ] `src/inference/mlx_inference.py` oluştur
- [ ] MLX-LM ile generation
- [ ] Streaming desteği
- [ ] Token limiti yönetimi

### 5.3 Ana Orkestrasyon
- [ ] `src/main.py` veya `src/orchestrator.py` oluştur
- [ ] Flow:
  ```
  1. User Input
  2. Router -> Intent Classification
  3. LoRA Manager -> Load Adapter
  4. Memory -> Retrieve Context
  5. Inference -> Generate Response
  6. Logger -> Save Conversation
  ```
- [ ] Error handling
- [ ] Graceful degradation

### 5.4 CLI Interface
- [ ] Basit terminal chat interface
- [ ] `/help`, `/clear`, `/switch` komutları
- [ ] Güzel output formatting

### 5.5 Entegrasyon Testleri
- [ ] Uçtan uca test senaryoları
- [ ] Türkçe sohbet -> Kod yazma geçişi
- [ ] Hafıza hatırlama
- [ ] Performance metrikleri

---

## ⬜ Faz 6: Yaşam Döngüsü (Sync/Async)

*Amaç: Sistemin kendi kendini güncellemesi*

### 6.1 Loglama Sistemi
- [ ] `src/lifecycle/logger.py` oluştur
- [ ] Structured logging (JSON format)
- [ ] Log rotasyonu
- [ ] Conversation tracking

### 6.2 Gündüz Modu (Sync Handler)
- [ ] `src/lifecycle/sync_handler.py` oluştur
- [ ] Real-time chat loop
- [ ] Anlık yanıt üretimi
- [ ] Session yönetimi

### 6.3 Gece Modu (Async Processor)
- [ ] `src/lifecycle/async_processor.py` oluştur
- [ ] Log analiz fonksiyonları:
  ```python
  def analyze_daily_logs(date):
      # Başarısız yanıtları bul
      # Yeni bilgi çıkar
      # Patterns tespit et
  ```
- [ ] Bilgi çıkarımı (NER, keyword extraction)
- [ ] ChromaDB'ye yeni bilgi yazımı

### 6.4 Scheduler
- [ ] Gece script'i için cron job veya launchd
- [ ] Manuel tetikleme seçeneği
- [ ] Rapor üretimi

### 6.5 Self-Improvement Pipeline (İleri Seviye)
- [ ] Hata pattern analizi
- [ ] Yeni eğitim verisi önerileri
- [ ] LoRA re-training trigger'ları

---

## 📝 Notlar

### Bellek Yönetimi İpuçları (Mac M4)
- Batch size=1 kullan, memory overflow önle
- Gradient checkpointing aktif et
- Model'leri lazy load yap
- Kullanılmayan adapter'ları unload et

### Performans Hedefleri
- Router latency: <50ms
- Inference latency: <500ms (ilk token)
- Memory search: <100ms
- Token/saniye: 30+ (streaming)

### Debugging
- `MPS_FALLBACK_TO_CPU=1` (fallback için)
- `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0` (memory)

---

## 🔗 Faydalı Linkler

- [MLX Documentation](https://ml-explore.github.io/mlx/)
- [MLX-LM Examples](https://github.com/ml-explore/mlx-examples)
- [Qwen2.5 Model Card](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [HuggingFace Hub](https://huggingface.co/)

---

*Bu liste projemizin yol haritasıdır. Her tamamlanan görev için ⬜ yerine ✅ koyun.*
