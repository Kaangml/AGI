# 🧠 EVO-TR V2 Memory

**Son Güncelleme:** 7 Aralık 2024 15:30

---

## 📍 Şu An Neredeyiz?

**Aktif Faz:** V2.3 - Gerçek Kullanım (başlamak üzere)

**V2 Ana Hedefler:**
1. ✅ Gemma 3 27B ile kaliteli veri üretimi - TAMAMLANDI
2. ✅ LoRA V2 adaptörleri eğitimi - TAMAMLANDI
3. ⬜ Gerçek kullanım ve feedback toplama
4. ⬜ Sürekli öğrenme döngüsü

---

## 🔧 Teknik Ortam

| Bileşen | Değer |
|---------|-------|
| Donanım | Mac Mini M4 (Apple Silicon, Metal GPU) |
| Python | 3.11.14 (.venv) |
| MLX | 0.30.0 |
| mlx_lm | 0.28.3 |
| Base Model | Qwen-2.5-3B-Instruct |
| Veri Generator | Gemma 3 27B (gemma-3-27b-it) |
| API Keys | 2 adet (GOOGLE_API_KEY, GOOGLE_API_KEY_2) |

---

## 📊 Veri Durumu

### Gemma 3 27B Üretimi (7 Aralık 2024)
| Kategori | Adet | Dosya | Boyut |
|----------|------|-------|-------|
| Türkçe Sohbet | 500 | data/generated/turkish_chat/*.jsonl | 421 KB |
| Python Kod | 500 | data/generated/python_code/*.jsonl | 493 KB |
| **Toplam** | **1,005** | - | **914 KB** |

### MLX Eğitim Formatı
- `data/training/gemma_tr_chat/`: 450 train + 55 valid
- `data/training/gemma_python_code/`: 452 train + 50 valid

---

## 🎯 LoRA V2 Adaptörler

### tr_chat_v2 ✅
| Metrik | Değer |
|--------|-------|
| Durum | TAMAMLANDI |
| Başlangıç Val Loss | 3.074 |
| Final Val Loss | 0.257 |
| İyileşme | %92 |
| Süre | ~82 dakika (4911s) |
| Klasör | adapters/tr_chat_v2/ |

### python_coder_v2 ✅
| Metrik | Değer |
|--------|-------|
| Durum | TAMAMLANDI |
| Config | batch=2, rank=8, seq=512 |
| Süre | ~92 dakika (5526s) |
| Klasör | adapters/python_coder_v2/ |

---

## 📜 Son Oturum Logları

### 7 Aralık 2024 - Veri Üretimi & Eğitim
```
05:45 - Gemma 3 27B API'ye geçiş (rate limit: RPM=30, TPM=15K)
05:50 - scripts/gemini_data_generator.py oluşturuldu
06:00 - 500 Türkçe sohbet örneği üretimi başladı
06:45 - Türkçe veri tamamlandı (500 örnek)
07:00 - 500 Python kod örneği üretimi başladı
07:55 - Python veri tamamlandı (500 örnek)
08:30 - prepare_gemma_data.py ile MLX formatına dönüştürme
09:00 - tr_chat_v2 eğitimi başladı
10:22 - tr_chat_v2 tamamlandı (Val Loss: 0.257)
10:30 - python_coder_v2 eğitimi başladı (bellek crash)
10:35 - Bellek-dostu config ile yeniden başlatıldı
12:00 - python_coder_v2 tamamlandı
```

---

## 🔑 Önemli Bilgiler

### API Rate Limits (Gemma 3 27B)
- RPM: 30 (Request per minute)
- TPM: 15,000 (Token per minute)
- RPD: 14,400 (Request per day)

### Bellek-Dostu Eğitim Config
```yaml
batch_size: 2
lora_layers: 8
lora_parameters:
  rank: 8
  scale: 1.0
max_seq_length: 512
```

### Öğrenilen Dersler
1. Gemini 2.5 Flash rate limit çok düşük (RPM=5) - Gemma 3 27B kullan
2. Python eğitimi için batch_size=2 ve rank=8 yeterli
3. max_seq_length=512 bellek için güvenli
4. API key rotation veri üretimini hızlandırır

---

## �� Kritik Dosyalar

| Dosya | Amaç |
|-------|------|
| scripts/gemini_data_generator.py | Gemma 3 27B ile veri üretimi |
| scripts/prepare_gemma_data.py | MLX formatına dönüştürme |
| configs/lora_tr_config_v2.yaml | Türkçe V2 eğitim config |
| configs/lora_python_config_v2.yaml | Python V2 eğitim config |
| adapters/tr_chat_v2/ | Türkçe sohbet V2 adaptör |
| adapters/python_coder_v2/ | Python kod V2 adaptör |

---

## ⏭️ Sonraki Adımlar

1. **Chat CLI Güncelle**
   - V2 adaptörlerini varsayılan yap
   - EVO-TR system prompt ekle

2. **Gerçek Kullanım Başlat**
   - Her gün 10+ sohbet
   - Çeşitli konular test et

3. **Feedback Loop**
   - Kaliteli/kötü yanıtları işaretle
   - Haftalık analiz yap

---

## 🔬 Sistem Analizi (7 Aralık 2024 - 16:00)

### Test Sonuçları

#### Router Performansı
| Mesaj | Intent | Güven | Durum |
|-------|--------|-------|-------|
| "Merhaba nasılsın" | general_chat | 87% | ✅ Doğru |
| "Python liste oluştur" | code_python | 77% | ✅ Doğru |
| "5+3 kaç eder" | code_math | 55% | ⚠️ Düşük güven |
| "Osmanlı tarihi anlat" | turkish_culture | 83% | ⚠️ history olmalıydı |
| "Fizik kanunları nedir" | science | 53% | ⚠️ Düşük güven |

#### Adaptör Test Sonuçları
- **V1 vs V2 karşılaştırması:** Aynı çıktılar üretiyorlar - beklenmedik!
- **Olası sebep:** Aynı base model, benzer eğitim verisi

#### Hafıza (Memory) Testi
- ✅ Kısa süreli hafıza çalışıyor ("Benim adım Kaan" → hatırlandı)
- ✅ RAG context ekleniyor (233-660 karakter)
- ⚠️ ChromaDB'de 53 döküman birikmiş

---

### 🚨 Tespit Edilen Sorunlar

#### 1. V2 Adaptörleri Kullanılmıyor!
**Kritiklik:** 🔴 YÜKSEK

```python
# src/experts/lora_manager.py - ADAPTER_REGISTRY
"turkish_culture": "tr_chat",     # ❌ tr_chat_v2 olmalı
"code_python": "python_coder",    # ❌ python_coder_v2 olmalı
```

**Düzeltme:**
```python
ADAPTER_REGISTRY = {
    "general_chat": None,
    "turkish_culture": "tr_chat_v2",     # ✅
    "code_python": "python_coder_v2",    # ✅
    "code_debug": "python_coder_v2",     # ✅
    "code_explain": "python_coder_v2",   # ✅
    ...
}
```

#### 2. CLI'da Feedback Mekanizması Yok!
**Kritiklik:** 🔴 YÜKSEK

- Web arayüzünde 👍/👎 butonları var ama CLI'da yok
- `preference_learning.py` hazır ama CLI'a entegre değil
- Lifecycle döngüsü feedback olmadan çalışamaz

**Gereken:**
- `/feedback good` veya `/feedback bad` komutu
- Ya da yanıttan sonra `[g]ood / [b]ad` prompt'u

#### 3. Intent-Adapter Mapping Tutarsızlık
**Kritiklik:** 🟡 ORTA

- `configs/intent_mapping.json` → `adapter_tr_chat` prefix kullanıyor
- `src/experts/lora_manager.py` → `tr_chat` (prefix'siz) kullanıyor
- İki farklı mapping sistemi çakışıyor

#### 4. Router Güven Eşiği Sorunu
**Kritiklik:** 🟡 ORTA

- Bazı intent'ler %50-55 güvenle tespit ediliyor
- `confidence_threshold: 0.7` config'de var ama uygulanmıyor
- Düşük güvenli tahminlerde fallback çalışmalı

#### 5. "Osmanlı tarihi" → "turkish_culture" Hatalı
**Kritiklik:** 🟡 ORTA

- Tarih sorusu `history` intent'ine gitmeli
- Router eğitim verisi yetersiz olabilir

---

### 💡 İyileştirme Önerileri

#### Öncelik 1 - Kritik (Bu Hafta)
1. **V2 adaptör mapping'ini düzelt** - 10 dk
2. **CLI'a feedback komutu ekle** - 30 dk
3. **Router confidence kontrolü aktifleştir** - 15 dk

#### Öncelik 2 - Önemli (Bu Ay)
4. **Router eğitim verisine tarih örnekleri ekle**
5. **Intent mapping tutarsızlığını çöz** (tek kaynak)
6. **Gece analizi için feedback toplama başlat**

#### Öncelik 3 - İyileştirme
7. V1 vs V2 adaptör kalite karşılaştırması
8. TTT cache hit oranı takibi
9. Uzun konuşmalarda context overflow kontrolü

---

### 📊 Sistem Sağlık Durumu

| Bileşen | Durum | Not |
|---------|-------|-----|
| Base Model | ✅ Çalışıyor | Qwen 2.5 3B |
| Router | ⚠️ Kısmen | Düşük güven sorunları |
| LoRA V2 | ✅ Entegre edildi | ADAPTER_REGISTRY güncellendi |
| Memory/RAG | ✅ Çalışıyor | 53 döküman |
| TTT | ✅ Çalışıyor | dynamic_prompt aktif |
| Feedback | ✅ Birleştirildi | CLI + Web → SQLite |
| Lifecycle | ✅ Hazır | process_feedback.py oluşturuldu |

---

## ✅ Düzeltmeler (7 Aralık 2024 - 17:00)

### 1. V2 Adaptör Entegrasyonu - TAMAMLANDI ✅
**Dosya:** `src/experts/lora_manager.py`

```python
ADAPTER_REGISTRY = {
    "general_chat": "tr_chat_v2",        # ✅ V2
    "turkish_culture": "tr_chat_v2",     # ✅ V2
    "code_python": "python_coder_v2",    # ✅ V2
    "code_debug": "python_coder_v2",     # ✅ V2
    ...
}
```

### 2. CLI Feedback Komutları - TAMAMLANDI ✅
**Dosya:** `scripts/chat_cli.py`

Eklenen komutlar:
- `/good` - Yanıtı olumlu işaretle (thumbs_up)
- `/bad` - Yanıtı olumsuz işaretle (thumbs_down)
- `/correct <düzeltme>` - Doğru yanıtı gir (correction)

### 3. Feedback Birleştirme - TAMAMLANDI ✅
**Sorun:** Web (SQLite) ve CLI (JSONL) farklı formatlarda kaydediyordu

**Çözüm:**
- CLI artık `FeedbackDatabase` kullanıyor
- Tek veritabanı: `data/feedback.db` (SQLite)
- Web ve CLI aynı tabloya yazıyor

### 4. Lifecycle Script - TAMAMLANDI ✅
**Dosya:** `scripts/process_feedback.py`

```bash
# Analiz modu
python scripts/process_feedback.py --analyze

# Eğitim başlat (10+ düzeltme gerekli)
python scripts/process_feedback.py --train
```

### 5. Web Correction Özelliği - TAMAMLANDI ✅
**Dosya:** `src/web/static/index.html`

- ✏️ düzeltme butonu eklendi
- Modal popup ile correction girişi
- FeedbackDatabase'e kayıt

---

## 📊 Mevcut Feedback Durumu

```
📊 Toplam Feedback: 5 adet
✏️ Düzeltme: 2 adet
👎 Negatif: 2 adet
👍 Pozitif: 1 adet

⚠️ Eğitim için 8 düzeltme daha gerekli (min: 10)
```

---

## 🎯 Sonraki Hedefler

1. **Kullanım ve Feedback Toplama**
   - Her gün 5-10 sohbet yap
   - Kötü cevapları düzelt (/correct)
   - 10 düzeltmeye ulaş

2. **İlk Preference Training**
   - `python scripts/process_feedback.py --train`
   - DPO ile iyileştirme

3. **Router İyileştirmesi**
   - Tarih intent'i için örnekler ekle
   - Confidence threshold uygula

