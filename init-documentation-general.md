Harika bir karar. Bir yazılım veya mühendislik projesinde "harita" (kod) kadar "pusula" (dokümantasyon) da önemlidir. Özellikle **MoE (Mixture of Experts)** ve **Sürekli Öğrenme** gibi karmaşık mimarilerde kaybolmamak için bu "Anayasa" niteliğindeki dokümanı hazırladım.

Bu dokümanı bir `.md` (Markdown) dosyası veya proje yönetim aracına (Notion/Obsidian) kopyalayarak projenin merkezine koyabilirsin.

---

# 📘 EVO-TR: Otonom ve Modüler YZ Mimari Dokümantasyonu

**Sürüm:** 1.0 (PoC)
**Tarih:** 02 Aralık 2025
**Temel Model:** Qwen-2.5-3B-Instruct

## 1. Proje Vizyonu ve Felsefesi
EVO-TR, statik ve her şeyi tek seferde öğrenmeye çalışan devasa bir model yerine; **modüler, adaptif ve zamanla gelişen** biyolojik bir öğrenme sürecini simüle etmeyi hedefler.

* **Metafor:** "Bebek -> Çocuk -> Uzman".
* **Temel Prensip:** "Omurga (Base Model) sabit kalır, yetenekler (LoRA) ve hafıza (Vector DB) dinamik olarak büyür."
* **Çalışma Mantığı:** Gündüz etkileşime girer (Senkron), gece deneyimlerini işler (Asenkron).

---

## 2. Sistem Mimarisi (Kuş Bakışı)

Sistem 4 ana katmandan oluşur. Veri akışı şu şekildedir:

`Kullanıcı Girdisi` -> `Router (Sınıflandırıcı)` -> `Seçilen Uzman (LoRA)` + `Hafıza (RAG)` -> `Çıktı` -> `Loglama`

### A. Yönetim Katmanı (The Router - Beyincik)
Sistemin "ne yapacağına" karar veren hafif katmandır.
* **Model:** `DistilBERT` (veya benzeri hafif sınıflandırıcı).
* **Görevi:** Gelen istemin (prompt) niyetini anlamak.
* **Çıktı:** Hangi LoRA adaptörünün (Legonun) kullanılacağı bilgisi. (Örn: `id: tr_chat` veya `id: python_coder`).

### B. Omurga ve Uzmanlar (The Brain & Skills)
Asıl zekanın ve işlemenin olduğu katmandır.
* **Base Model (Omurga):** `Qwen-2.5-3B-Instruct`. Dondurulmuş (Frozen) ağırlıklar.
* **Serving Motoru:** `vLLM` veya `LoRAX`. (Multi-LoRA desteği için şart).
* **Uzmanlar (LoRA Modülleri):**
    1.  **Expert A (Dil Uzmanı):** Türkçe kültürü, sohbet, metin işleme.
    2.  **Expert B (Kod Uzmanı):** Python, algoritma, debugging.
    3.  *(Gelecekte)* Expert C: Matematik/Analiz.

### C. Hafıza Katmanı (The Memory - Hipokampus)
Modelin kimliğini ve geçmişi hatırladığı yerdir.
* **Kısa Süreli Hafıza:** Context Window (Son 10-20 mesaj).
* **Uzun Süreli Hafıza (RAG):** `ChromaDB`.
* **Embedding Model:** `emrecan/bert-base-turkish-cased-mean-nli-stsb-tr` (Türkçe anlamsal vektörleme).

### D. Yaşam Döngüsü Katmanı (The Loop)
Sistemin uyuyup uyandığı süreçtir.
* **Senkron (Gündüz):** Canlı sohbet ve anlık yanıt.
* **Asenkron (Gece):** `n8n` veya Python scriptleri ile günlük logların analizi, hafızaya işlenmesi ve başarısız yanıtların etiketlenmesi.

---

## 3. Veri Setleri ve Eğitim Stratejisi

Modelin "Legolarını" (Uzmanlarını) oluşturmak için kullanılacak kaynaklar.

| Uzmanlık Alanı | Kaynak Veri Setleri | Eğitim Yöntemi | Hedef Yetenek |
| :--- | :--- | :--- | :--- |
| **Router (Sınıflandırıcı)** | Elle hazırlanmış "Intent" (Niyet) veri seti (50-100 örnek). | Few-Shot Classification / Fine-tuning | Soruyu doğru kategoriye (Kod/Sohbet) ayırma. |
| **Türkçe Uzmanı (Lego 1)** | `CohereForAI/aya_dataset (tr)` + `Turkish-Instructions`. | QLoRA (Quantized Low-Rank Adaptation) | Doğal Türkçe konuşma, kültürel uyum. |
| **Python Uzmanı (Lego 2)** | `Humaneval-X (Python)` + `MBPP`. | QLoRA | Python syntax hakimiyeti, hatasız kod üretimi. |

---

## 4. Teknik Teknoloji Yığını (Tech Stack)

Projeyi inşa ederken kullanılacak kesinleşmiş araçlar:

* **Dil:** Python 3.10+
* **Base Model:** Qwen-2.5-3B-Instruct (GGUF veya Safetensors formatı).
* **Inference Engine:** `vLLM` (Üretim ortamı için) veya `LoRAX`.
* **Fine-Tuning:** `HuggingFace PEFT`, `BitsAndBytes` (4-bit quantization için), `TRL` (Transformer Reinforcement Learning).
* **Vector DB:** `ChromaDB` (Yerel ve kalıcı).
* **Orkestrasyon:** `LangChain` (Zincirleme mantık için) + Python Scriptleri.

---

## 5. Geliştirme Yol Haritası (Detaylı Fazlar)

Bu kısım projenin ilerleyiş cetvelidir.

### Faz 0: Temel Kurulum (Setup)
* [ ] Donanım kontrolü (GPU VRAM yeterliliği).
* [ ] Sanal ortamın (venv/conda) kurulması.
* [ ] Qwen-2.5-3B modelinin indirilmesi ve "Hello World" testi.

### Faz 1: Beyincik İnşası (Router)
* [ ] Niyet sınıflandırma veri setinin hazırlanması (Excel/JSON).
* [ ] DistilBERT modelinin bu veri setiyle eğitilmesi.
* [ ] Router API'nin yazılması (Input: Text -> Output: Adapter_ID).

### Faz 2: İlk Uzman (Türkçe)
* [ ] Aya ve Instruction veri setlerinin birleştirilmesi.
* [ ] QLoRA eğitim scriptinin hazırlanması.
* [ ] Eğitimin yapılması ve `adapter_tr.safetensors` çıktısının alınması.
* [ ] Base Model + Adapter TR testi.

### Faz 3: İkinci Uzman (Kodlama)
* [ ] Kodlama veri setinin hazırlanması.
* [ ] İkinci QLoRA eğitimi.
* [ ] `adapter_py.safetensors` çıktısının alınması.

### Faz 4: Entegrasyon ve Hafıza
* [ ] Multi-LoRA sunucusunun (vLLM/LoRAX) başlatılması.
* [ ] Router + Server + RAG bağlantısının yapılması.
* [ ] Uçtan uca test (Sohbet -> Hafıza -> Kodlama).

### Faz 5: Otomasyon (Uyku Modu)
* [ ] Loglama sisteminin aktifleştirilmesi.
* [ ] "Gece Scripti"nin (Log Analizörü) yazılması.

---

## 6. Risk Yönetimi ve Uyarılar

1.  **Bermuda Şeytan Üçgeni (Hafıza Karışıklığı):**
    * *Risk:* Kod yazarken Türkçe sohbet modülünün devreye girmesi ve kodun içine Türkçe yorumlar/hatalar eklemesi.
    * *Önlem:* Router'ın "Confidence Score" (Güven Skoru) kontrol edilmeli. Eğer emin değilse varsayılan olarak Base Modeli kullanmalı.

2.  **Token Limitleri:**
    * *Risk:* RAG sisteminin çok fazla veri çekip Qwen'in context penceresini (32k) doldurması.
    * *Önlem:* `Top-k=3` (En alakalı 3 parça) sınırı konulmalı.

3.  **Soğuk Başlangıç (Cold Start):**
    * *Risk:* Adaptör değişimlerinde milisaniyelik gecikmelerin kullanıcıyı rahatsız etmesi.
    * *Önlem:* vLLM veya LoRAX bu geçişleri önbelleğe alarak (caching) optimize eder, bu araçların kullanımı şarttır.

---

Bu doküman projemizin anayasasıdır. Kaybolursak buraya döneceğiz.
