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
