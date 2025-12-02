Harika. Router için küçük, hızlı ve yerel çalışan bir sınıflandırıcı (Classifier) model kullanmak, sistemin "niyeti" anlamasını sağlayarak doğru uzmana yönlendirmeyi garanti altına alır. Basit kelime eşleşmesinden çok daha zeki bir yaklaşımdır.

İşte **Qwen-2.5-3B** omurgası üzerinde, **Multi-LoRA (Lego)** mimarisi ve **Router** zekasıyla çalışacak **EVO-TR** projesinin nihai Master Todo Listesi:

# 🚀 EVO-TR: Nihai Master Todo List (PoC)

Bu liste, sistemi "modüler, sürekli öğrenen ve yönetilebilir" bir yapı olarak hayata geçirmek için kesinleşmiş teknik yol haritasıdır.

### **Faz 0: Altyapı ve Omurga (The Skeleton)**
*Amaç: Tek bir 3B model üzerinde onlarca farklı uzmanlığı çalıştırabilecek motoru kurmak.*

* [ ] **Base Model Temini:** Hugging Face'den `Qwen/Qwen2.5-3B-Instruct` modelinin indirilmesi. (Sistemin sabit beyni).
* [ ] **Multi-LoRA Serving Motoru:** **`LoRAX` (LoRA Exchange)** veya **`vLLM`** kurulumu.
    * *Not:* Bu motor, bellekte tek bir Qwen modeli tutar ancak isteğe göre milisaniyeler içinde "Türkçe LoRA" veya "Kodlama LoRA"sını devreye sokar.
* [ ] **Donanım & Hız Testi:** Seçilen GPU/CPU üzerinde modelin saniyede kaç token ürettiğinin (t/s) test edilmesi.

### **Faz 1: Router (Yönlendirici Zeka)**
*Amaç: Gelen sorunun hangi uzmana gitmesi gerektiğine karar veren "Kapı Görevlisi".*

* [ ] **Sınıflandırıcı Model Seçimi:** Çok hafif bir BERT modeli (Örn: `distilbert-base-multilingual-cased` veya `bge-m3`) seçilmesi.
* [ ] **Sınıflandırma Eğitimi (Few-Shot):** Bu küçük modeli şu etiketlerle eğitmek (veya fine-tune etmek):
    * `expert_tr_chat` (Genel sohbet, selamlaşma, tarih vb.)
    * `expert_python_coder` (Kod yazma, debug, script)
    * `expert_memory` (Geçmişi hatırlama soruları)
* [ ] **API Endpoint:** Router'ın gelen promptu alıp, çıktı olarak `"adapter_id"` (örn: `adapter_python`) döndüreceği mini bir Python fonksiyonu yazılması.

### **Faz 2: Uzman Modüllerin Üretimi (The Legos)**
*Amaç: Base modelin yeteneklerini özelleştirmek.*

* [ ] **Uzman 1: Türkçe İletişim:**
    * Veri Seti: `Aya-dataset (TR)` + `Turkish-Instructions`.
    * İşlem: Qwen-2.5-3B üzerine QLoRA eğitimi.
    * Çıktı: `adapter_tr_chat.safetensors`.
* [ ] **Uzman 2: Python Geliştirici:**
    * Veri Seti: `Humaneval-X (Python)` + `MBPP`.
    * İşlem: Kodlama odaklı QLoRA eğitimi.
    * Çıktı: `adapter_python_coder.safetensors`.

### **Faz 3: Hafıza ve Bilinç (Hippocampus)**
*Amaç: RAG ve Vektör hafıza ile süreklilik.*

* [ ] **Embedding Modeli:** `emrecan/bert-base-turkish-cased-mean-nli-stsb-tr` entegrasyonu.
* [ ] **Vektör DB:** `ChromaDB` kurulumu ve kalıcı depolama ayarı (Persistent Storage).
* [ ] **Kısa Süreli Bellek:** LangChain veya manuel script ile son 10 konuşma turunu tutan tampon bellek.

### **Faz 4: Yaşam Döngüsü (Sync/Async Loop)**
*Amaç: Sistemin kendi kendini güncellemesi.*

* [ ] **Gündüz Modu (Sync):**
    * Kullanıcı -> Router -> Seçilen Uzman (LoRA) -> Yanıt -> Loglama.
* [ ] **Gece Modu (Async - Uyku Scripti):**
    * **Log Analizi:** Günlük sohbet loglarını tarayan bir script.
    * **Bilgi Çıkarımı:** "Kullanıcı bugün yeni bir proje ismi verdi mi? Yeni bir tercih belirtti mi?" kontrolü.
    * **Hafıza Yazımı:** Değerli bilgilerin ChromaDB'ye vektör olarak eklenmesi.
    * **(İleri Seviye) Öz-Eğitim:** Çok fazla hata yapılan konuların tespit edilip, bir sonraki LoRA eğitimi için "ToDo" listesine eklenmesi.

---

