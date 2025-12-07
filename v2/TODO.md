# 📋 EVO-TR V2 TODO

**Versiyon:** 2.0  
**Başlangıç:** 6 Aralık 2024  
**Hedef:** Kaliteli veri + Gerçek kullanım + Sürekli öğrenme

---

## 🎯 V2 Vizyonu

V1'de **altyapı** kuruldu. V2'de **bebeği doğurup besleyeceğiz**:
1. Kaliteli veri ile LoRA'ları güçlendir
2. Gerçek kullanım deneyimi
3. Feedback loop ile sürekli öğrenme

---

## ✅ FAZ V2.1: Veri Üretimi (Gemini ile)

### V2.1.1 Altyapı
- [x] v1/ ve v2/ klasör yapısı
- [x] V1 Final raporu
- [ ] .env'den GOOGLE_API_KEY okuma
- [ ] Gemini API wrapper (async)
- [ ] Rate limiting ve retry logic

### V2.1.2 Türkçe Sohbet Verisi
- [ ] Günlük sohbet (selamlama, vedalaşma, soru-cevap)
- [ ] Türk kültürü (yemek, gelenek, coğrafya)
- [ ] Atasözleri ve deyimler
- [ ] Duygusal destek ve empati
- [ ] **Hedef:** 1,000 kaliteli örnek

### V2.1.3 Python Kod Verisi
- [ ] Temel Python soruları
- [ ] Algoritma çözümleri
- [ ] Debugging senaryoları
- [ ] Kod açıklama örnekleri
- [ ] **Hedef:** 500 kaliteli örnek

### V2.1.4 Kalite Kontrol
- [ ] Duplicate kontrolü
- [ ] Format validasyonu
- [ ] İçerik kalitesi değerlendirme
- [ ] Manuel sampling review

---

## ⬜ FAZ V2.2: LoRA Yeniden Eğitimi

### V2.2.1 tr_chat Güçlendirme
- [ ] Yeni veri ile fine-tuning
- [ ] A/B karşılaştırma (eski vs yeni)
- [ ] Kalite metrikleri ölçümü

### V2.2.2 python_coder Güçlendirme
- [ ] Yeni veri ile fine-tuning
- [ ] Kod çalıştırma testleri
- [ ] Accuracy ölçümü

---

## ⬜ FAZ V2.3: Gerçek Kullanım

### V2.3.1 Günlük Kullanım
- [ ] Her gün en az 10 sohbet
- [ ] Farklı konular test etme
- [ ] Feedback verme (👍/👎)

### V2.3.2 Feedback Analizi
- [ ] Haftalık feedback raporu
- [ ] Zayıf nokta tespiti
- [ ] İyileştirme önerileri

---

## ⬜ FAZ V2.4: Öğrenme Döngüsü

### V2.4.1 İlk Incremental Training
- [ ] Feedback'lerden veri hazırlama
- [ ] LoRA güncelleme
- [ ] Performans karşılaştırma

### V2.4.2 DPO Preference Learning
- [ ] Tercih çiftleri oluşturma
- [ ] DPO eğitimi
- [ ] Kalite iyileşme ölçümü

---

## 📊 V2 Başarı Kriterleri

| Metrik | V1 Değeri | V2 Hedefi |
|--------|-----------|-----------|
| Eğitim Verisi (Türkçe) | 4,147 | 5,000+ |
| Eğitim Verisi (Python) | 13,334 | 14,000+ |
| Gerçek Konuşma | 2 | 100+ |
| Feedback | 0 | 50+ |
| Incremental Training | 0 | 2+ |
| Kullanıcı Memnuniyeti | N/A | %80+ |

---

## 🔄 İlerleme Takibi

| Tarih | Görev | Durum |
|-------|-------|-------|
| 6 Aralık | V1 Final Raporu | ✅ |
| 6 Aralık | v1/v2 yapısı | ✅ |
| 6 Aralık | Gemini Data Generator | 🔄 |
| - | İlk veri üretimi | ⬜ |
| - | LoRA güçlendirme | ⬜ |
| - | Gerçek kullanım | ⬜ |

---

*Son Güncelleme: 6 Aralık 2024*
