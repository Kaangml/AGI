# 🧠 Agent Memory Log

> Bu dosya, geliştirme sürecinde yapılan işlemleri, kararları ve notları takip eder.

---

## 📅 2 Aralık 2024 - Oturum 1

### 🎯 Aktif Görev
**FAZ 0: Altyapı ve Kurulum**

### 🖥️ Sistem Bilgisi
- **Donanım:** Mac Mini M4 (Apple Silicon)
- **OS:** macOS
- **Shell:** zsh
- **Python Hedef:** 3.10+

### 📝 İşlem Geçmişi

| Zaman | İşlem | Durum | Notlar |
|-------|-------|-------|--------|
| Başlangıç | Memory dosyası oluşturuldu | ✅ | - |
| 0.1.1 | macOS sürüm kontrolü | ✅ | macOS 15.5 (Sequoia) |
| 0.1.2 | Python kontrolü | ✅ | 3.11.14 kuruldu (brew) |
| 0.1.3 | Xcode CLI tools | ✅ | version 2409 |
| 0.1.4 | Homebrew kontrolü | ✅ | 5.0.3 |
| 0.1.5 | Git kontrolü | ✅ | 2.39.5 |
| 0.2.1 | Dizin yapısı oluşturma | ✅ | src, models, adapters, data, logs, scripts, tests, configs |
| 0.2.2 | Virtual environment | ✅ | .venv Python 3.11.14 |
| 0.2.3 | .gitignore | ✅ | Kapsamlı gitignore oluşturuldu |
| 0.3.1 | requirements.txt | ✅ | Oluşturuldu |
| 0.3.2 | Bağımlılık kurulumu | ✅ | mlx 0.30.0, mlx-lm 0.28.3, transformers, chromadb, sentence-transformers |
| 0.3.3 | MLX Metal kontrolü | ✅ | Device(gpu, 0) - Metal aktif |
| 0.4.1 | .env kontrolü | ✅ | HF_TOKEN mevcut |
| 0.4.2 | settings.py | ✅ | configs/settings.py oluşturuldu |
| 0.4.3 | HF CLI login | ✅ | kaangml (orgs: mcp-course) |
| 0.4.4 | Model erişim testi | ✅ | Qwen/Qwen2.5-3B-Instruct erişilebilir |
| 0.5.1 | Model indirme | ✅ | 1.63 GB (4-bit quantized MLX) |
| 0.5.2 | Hello World testi | ✅ | 57.2 tokens/saniye |
| 0.5.3 | Bellek kontrolü | ✅ | Peak: 1.829 GB |
| 0.6.1 | verify_setup.py | ✅ | Script oluşturuldu ve çalıştırıldı |

### 🎉 FAZ 0 TAMAMLANDI!

**Performans Sonuçları:**
- Token/saniye: **57.2 t/s** (hedef: 30+)
- Bellek kullanımı: **1.829 GB** peak
- Model boyutu: **1.63 GB** (4-bit quantized)

---

## 📅 2 Aralık 2024 - Oturum 2

### 🎯 Aktif Görev
**FAZ 1: Router - Yönlendirici Zeka**

### 📝 FAZ 1 İşlem Geçmişi

| Zaman | İşlem | Durum | Notlar |
|-------|-------|-------|--------|
| Başlangıç | Faz 1 başlatıldı | ✅ | Router sistemi |
| 1.1.1 | Kategori listesi | ✅ | 7 intent kategorisi tanımlandı |
| 1.1.2 | intent_mapping.json | ✅ | Adapter mapping oluşturuldu |
| 1.2.1 | Dataset formatı | ✅ | JSON format belirlendi |
| 1.2.2-8 | Sample dosyaları | ✅ | 185 örnek oluşturuldu |
| 1.2.9 | build_intent_dataset.py | ✅ | Dataset builder script |
| 1.3.1 | Model seçimi | ✅ | paraphrase-multilingual-MiniLM-L12-v2 |
| 1.3.2 | Yaklaşım seçimi | ✅ | Similarity-based (hızlı prototip) |
| 1.3.3 | Model indirme | ✅ | 471MB, models/router/sentence_transformer |
| 1.4.1 | IntentClassifier | ✅ | src/router/classifier.py |
| 1.4.2 | Router API | ✅ | src/router/api.py |
| 1.5.1 | Unit testler | ✅ | 15 test, hepsi geçti |
| 1.5.2 | Demo script | ✅ | scripts/router_demo.py |

### 🎉 FAZ 1 TAMAMLANDI!

**Sonuçlar:**
- 7 intent kategorisi (general_chat, turkish_culture, code_python, code_debug, code_explain, memory_recall, general_knowledge)
- 185 eğitim örneği
- Sentence-Transformer modeli (471MB)
- 15/15 unit test geçti (%100)
- Latency: ~50ms

---

## 📅 2 Aralık 2024 - Oturum 3

### 🎯 Aktif Görev
**FAZ 2: Türkçe Uzman - LoRA Adaptör #1**

### 📝 FAZ 2 İşlem Geçmişi

| Zaman | İşlem | Durum | Notlar |
|-------|-------|-------|--------|
| Başlangıç | Faz 2 başlatıldı | 🔄 | Türkçe LoRA eğitimi |
| 10:01 | datasets paketi yüklendi | ✅ | HuggingFace datasets 4.4.1 |
| 10:02 | download_aya_tr.py oluşturuldu | ✅ | Aya TR indirici |
| 10:03 | Aya Dataset indirildi | ✅ | 4046 Türkçe örnek, 1.76MB |
| 10:05 | Manuel veriler oluşturuldu | ✅ | greetings(25), culture(30), proverbs(32), daily_chat(32) |
| 10:07 | Veri temizleme yapıldı | ✅ | 4147 örnek, 1.78MB |
| 10:08 | Train/Val bölme yapıldı | ✅ | Train: 3732, Val: 415 |
| 10:10 | MLX format dönüşümü | ✅ | Chat format dönüştürüldü |
| 10:15 | LoRA eğitimi başladı | ✅ | 1000 iter, batch=2, lr=1e-4 |
| 10:33 | LoRA eğitimi tamamlandı | ✅ | 26MB adapter, val_loss=1.98 |

### 📊 Eğitim Metrikleri
- **Train Loss:** 3.7 → 2.0 (Başlangıç → Bitiş)
- **Val Loss:** 3.7 → 1.98 
- **Peak Memory:** 3.8GB
- **Token/sec:** ~165
- **Adapter Size:** 26.6MB

### ⚠️ Tespit Edilen Problemler
1. Base model Türkçe'de zayıf (Japonca'ya kayıyor!)
2. Adapter ile tekrarlama (repetition) problemi var
3. Daha fazla epoch ve/veya veri gerekiyor

### 🔄 V2 Eğitimi (3000 iter)
| Zaman | İşlem | Durum | Notlar |
|-------|-------|-------|--------|
| 13:36 | V2 eğitimi başladı | ✅ | 3000 iter, batch=4, lr=5e-5 |
| 17:53 | V2 eğitimi tamamlandı | ✅ | 26MB adapter |

**V2 Metrikleri:**
- Train Loss: 3.5 → 0.8 (overfitting!)
- Val Loss: En iyi 1.77 (iter 1500), son 1.93
- Peak Memory: 7GB
- Best checkpoint: iter 1000 (val_loss=1.86)

**V2 Test Sonuçları:**
- ✅ Türkçe yanıt veriyor (base modelden çok daha iyi)
- ⚠️ Hala tekrarlama problemi var
- ⚠️ Bazı bilgiler yanlış (Türk kahvesi tarifi)
- 🔄 İleride daha kaliteli veri ve/veya daha güçlü base model gerekebilir

### 🎉 FAZ 2 TAMAMLANDI!

**Final Adapter:** `adapters/tr_chat/adapters.safetensors` (26.6MB)

**Oluşturulan Dosyalar:**
- `scripts/download_aya_tr.py` - Aya dataset indirici
- `scripts/clean_training_data.py` - Veri temizleme
- `scripts/split_dataset.py` - Train/val bölme
- `scripts/convert_to_mlx_format.py` - Format dönüştürme
- `scripts/test_adapter_tr.py` - Adapter test
- `configs/lora_tr_config.yaml` - LoRA konfigürasyonu
- `data/training/manual_tr/*.jsonl` - Manuel eğitim verileri
- `data/training/mlx_format/` - MLX formatında veriler
- `adapters/tr_chat/` - Final Türkçe adapter

---

## 📅 2 Aralık 2024 - Oturum 4

### 🎯 Aktif Görev
**FAZ 3: Python Uzman - LoRA Adaptör #2**

### 📝 FAZ 3 İşlem Geçmişi

| Zaman | İşlem | Durum | Notlar |
|-------|-------|-------|--------|
| Başlangıç | Faz 3 başlatıldı | ✅ | Python LoRA eğitimi |
| 22:10 | download_code_datasets.py oluşturuldu | ✅ | 4 kaynak: HumanEval, MBPP, CodeAlpaca, Code-Instructions |
| 22:12 | Dataset'ler indirildi | ✅ | HumanEval(164), MBPP(964), CodeAlpaca(9208), Code-Instr(5000) = 15336 örnek |
| 22:20 | Manuel Python örnekleri | ✅ | basics(15), debugging(15), algorithms(12), best_practices(16) = 58 örnek |
| 22:25 | clean_code_data.py oluşturuldu | ✅ | Veri temizleme, filtreleme, duplikat kontrol |
| 22:26 | Veriler temizlendi | ✅ | 15390 ham → 13334 temiz örnek (non-python:2007, invalid:49) |
| 22:30 | convert_python_to_mlx.py oluşturuldu | ✅ | MLX chat format dönüştürücü |
| 22:31 | MLX format dönüşümü | ✅ | Train: 12000, Valid: 1334 |
| 22:35 | lora_python_config.yaml | ✅ | rank=16, alpha=32, lr=1e-5, iters=3000 |
| 22:40 | LoRA eğitimi başlatıldı | ✅ | 3000 iter, batch=4, 6.65M trainable params |
| 22:45 | OOM Error (batch=4, seq=1024) | ⚠️ | 10.36GB peak memory → crash |
| 22:46 | Restart: batch=2, seq=512 | ✅ | val_loss=2.803 başlangıç |
| 01:44 | **LoRA eğitimi tamamlandı** | ✅ | **val_loss=0.551 (best@2800), final=0.634** |
| 01:45 | Adapter test edildi | ✅ | 4/4 test başarılı! |

### 🎉 FAZ 3 TAMAMLANDI!

**Final Adapter:** `adapters/python_coder/adapters.safetensors` (26.6MB)

**Eğitim Özeti:**
- ★ **En İyi Val Loss:** 0.551 (iter 2800)
- **Final Val Loss:** 0.634 (iter 3000)
- **Train Loss:** 2.803 → 0.615
- **Peak Memory:** 6.64 GB
- **Tokens/sec:** ~200
- **Toplam Token:** 913,136

**Test Sonuçları (4/4 başarılı):**
- ✅ is_prime() fonksiyonu - doğru
- ✅ binary_search() fonksiyonu - doğru
- ✅ fibonacci() fonksiyonu (Türkçe prompt!) - doğru
- ✅ Bug fix (a-b → a+b) - doğru

**Checkpoint'lar:**
- `0000500_adapters.safetensors`
- `0001000_adapters.safetensors`
- `0001500_adapters.safetensors`
- `0002000_adapters.safetensors`
- `0002500_adapters.safetensors`
- `0003000_adapters.safetensors` (final)

### 📊 Eğitim İlerlemesi
| Iter | Train Loss | Val Loss | Peak Mem | Tokens/sec |
|------|------------|----------|----------|------------|
| 1 | - | 2.803 | 6.6 GB | - |
| 200 | 0.603 | 0.559 | 6.6 GB | 204 |
| 400 | 0.665 | 0.543 | 6.6 GB | 195 |
| 600 | 0.620 | 0.669 | 6.6 GB | 192 |
| 800 | 0.621 | 0.611 | 6.6 GB | 204 |
| 1000 | 0.581 | 0.575 | 6.6 GB | 207 |
| 1200 | 0.606 | 0.583 | 6.6 GB | 207 |
| 1400 | 0.615 | 0.562 | 6.6 GB | 203 |
| 1600 | 0.597 | 0.582 | 6.6 GB | 200 |
| 1800 | 0.604 | 0.568 | 6.6 GB | 206 |
| 2000 | 0.620 | 0.585 | 6.6 GB | 203 |
| 2200 | 0.603 | 0.649 | 6.6 GB | 195 |
| 2400 | 0.610 | 0.588 | 6.6 GB | 205 |
| 2600 | 0.617 | 0.609 | 6.6 GB | 196 |
| 2800 | 0.601 | **0.551** ★ | 6.6 GB | 197 |
| 3000 | 0.615 | 0.634 | 6.6 GB | 200 |

---

## 📅 3 Aralık 2024 - Oturum 5

### 🎯 Aktif Görev
**FAZ 4: Hafıza ve RAG Sistemi**

### 📝 FAZ 4 İşlem Geçmişi

| Zaman | İşlem | Durum | Notlar |
|-------|-------|-------|--------|
| Başlangıç | Faz 4 başlatıldı | ✅ | Hafıza sistemi |
| 02:00 | ChromaDB kontrolü | ✅ | chromadb 1.3.5 kurulu |
| 02:01 | Embedding model test | ✅ | paraphrase-multilingual-MiniLM-L12-v2 (384 dim) |
| 02:02 | data/chromadb/ dizini | ✅ | Persistent storage hazır |
| 02:05 | chromadb_handler.py | ✅ | MemoryHandler sınıfı, semantic search |
| 02:10 | context_buffer.py | ✅ | ContextBuffer, Message sınıfları |
| 02:15 | memory_manager.py | ✅ | Unified MemoryManager |
| 02:20 | __init__.py güncelleme | ✅ | Module exports |
| 02:25 | test_memory.py | ✅ | 25 unit test yazıldı |
| 02:30 | Testler çalıştırıldı | ✅ | **25/25 PASSED** |

### 📊 FAZ 4 Modül Özeti

**Oluşturulan Dosyalar:**
- `src/memory/chromadb_handler.py` - Uzun süreli hafıza (ChromaDB)
- `src/memory/context_buffer.py` - Kısa süreli hafıza (Son N mesaj)
- `src/memory/memory_manager.py` - Birleşik hafıza yönetimi
- `tests/test_memory.py` - 25 unit test

**Özellikler:**
| Özellik | Açıklama |
|---------|----------|
| Semantic Search | Türkçe/İngilizce anlamsal arama |
| RAG Context | Sorgu için ilgili bağlam oluşturma |
| Auto-save | Konuşmaları otomatik uzun süreli hafızaya kaydetme |
| Token Limit | Kısa süreli hafıza token kontrolü |
| Type Filtering | Hafıza tipi bazlı filtreleme |
| Conversation Pairs | User-Assistant çift takibi |

**Embedding Model:**
- Model: `paraphrase-multilingual-MiniLM-L12-v2`
- Boyut: 384 dimension
- Türkçe benzerlik: ~82% ("Merhaba" vs "Selam")

---

## 📅 3 Aralık 2024 - Oturum 6

### 🎯 Aktif Görev
**FAZ 5: Sistem Entegrasyonu**

### 📝 FAZ 5 İşlem Geçmişi

| Zaman | İşlem | Durum | Notlar |
|-------|-------|-------|--------|
| Başlangıç | Faz 5 başlatıldı | 🔄 | Entegrasyon |

### 📊 Veri İstatistikleri
- **Kaynaklar:** CodeAlpaca(60%), Code-Instr(31%), MBPP(7%), HumanEval(1%), Manual(0.4%)
- **Train:** 12,000 örnek
- **Valid:** 1,334 örnek
- **User avg length:** 126 karakter
- **Assistant avg length:** 296 karakter

### 🔑 Önemli Bilgiler
- `.env` dosyasında `HF_TOKEN` mevcut
- Base model: `Qwen/Qwen2.5-3B-Instruct`
- ML Framework: MLX (Apple Silicon optimized)

### ⚠️ Dikkat Edilecekler
- M4 için MLX kullanılacak (PyTorch değil)
- LoRA fine-tuning için `mlx-lm` paketi
- Tüm modeller `models/` dizininde saklanacak

### 🐛 Karşılaşılan Sorunlar
- (Henüz yok)

### 💡 Kararlar & Notlar
- (İşlemler ilerledikçe güncellenecek)

---
