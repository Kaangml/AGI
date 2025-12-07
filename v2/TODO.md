# 📋 EVO-TR V2 TODO

**Versiyon:** 2.0  
**Başlangıç:** 6 Aralık 2024  
**Son Güncelleme:** 7 Aralık 2024  
**Hedef:** Kaliteli veri + Gerçek kullanım + Sürekli öğrenme

---

## 🎯 V2 Vizyonu

V1'de **altyapı** kuruldu. V2'de **bebeği doğurup besleyeceğiz**:
1. ✅ Kaliteli veri ile LoRA'ları güçlendir
2. ⬜ Gerçek kullanım deneyimi
3. ⬜ Feedback loop ile sürekli öğrenme

---

## ✅ FAZ V2.1: Veri Üretimi (Gemma 3 27B) - TAMAMLANDI

### V2.1.1 Altyapı
- [x] v1/ ve v2/ klasör yapısı
- [x] V1 Final raporu
- [x] .env'den GOOGLE_API_KEY okuma
- [x] Gemini/Gemma API wrapper (async)
- [x] Rate limiting ve retry logic
- [x] API key rotation (2 key)
- [x] Checkpoint kaydetme

### V2.1.2 Türkçe Sohbet Verisi
- [x] Günlük sohbet (selamlama, vedalaşma, soru-cevap)
- [x] Türk kültürü (yemek, gelenek, coğrafya)
- [x] Atasözleri ve deyimler
- [x] Duygusal destek ve empati
- [x] **Sonuç:** 500 kaliteli örnek üretildi ✅

### V2.1.3 Python Kod Verisi
- [x] Temel Python soruları
- [x] Algoritma çözümleri
- [x] Debugging senaryoları
- [x] Kod açıklama örnekleri
- [x] **Sonuç:** 500 kaliteli örnek üretildi ✅

---

## ✅ FAZ V2.2: LoRA Yeniden Eğitimi - TAMAMLANDI

### V2.2.1 tr_chat_v2
- [x] Yeni Gemma verisi ile fine-tuning
- [x] 500 iterasyon, rank=8
- [x] Val Loss: 3.074 → 0.257 (%92 iyileşme)
- [x] Adapter: adapters/tr_chat_v2/

### V2.2.2 python_coder_v2
- [x] Bellek-dostu config (batch=2, seq=512)
- [x] Adapter: adapters/python_coder_v2/

---

## ⬜ FAZ V2.3: Gerçek Kullanım - SIRADA

### V2.3.1 Chat CLI Güncelleme
- [ ] V2 adaptörlerini entegre et
- [ ] Sistem promptunu güncelle
- [ ] Feedback butonu ekle

### V2.3.2 Günlük Kullanım
- [ ] Her gün en az 10 sohbet
- [ ] Farklı konular test etme
- [ ] Feedback verme

---

## ⬜ FAZ V2.4: Öğrenme Döngüsü

### V2.4.1 Feedback Analizi
- [ ] Haftalık feedback raporu
- [ ] Zayıf nokta tespiti

### V2.4.2 Incremental Training
- [ ] Feedback'lerden veri hazırlama
- [ ] LoRA güncelleme

---

## 📊 V2 İlerleme

| Metrik | V1 | V2 Hedef | V2 Mevcut | Durum |
|--------|-----|----------|-----------|-------|
| Türkçe Veri | 4,147 | 5,000+ | 4,652 | ✅ |
| Python Veri | 13,334 | 14,000+ | 13,836 | ✅ |
| Gemma Üretilen | 0 | 1,000 | 1,005 | ✅ |
| LoRA V2 | 0 | 2 | 2 | ✅ |
| Gerçek Konuşma | 2 | 100+ | 2 | ⬜ |
