# 🇹🇷 FAZ 2: Türkçe Uzman - LoRA Adaptör #1

**Durum:** ✅ Tamamlandı  
**Başlangıç:** 2 Aralık 2024  
**Bitiş:** 2 Aralık 2024  
**Öncelik:** 🟠 Yüksek  
**Bağımlılık:** ✅ Faz 0 ve Faz 1 tamamlandı

---

## 📊 Sonuçlar

### Veri Seti
- **Aya Dataset (TR):** 4046 örnek
- **Manuel veriler:** 119 örnek (selamlaşma, kültür, atasözleri, günlük sohbet)
- **Toplam:** 4147 örnek (train: 3732, val: 415)

### Eğitim (V2 - Final)
- **Parametreler:** batch=4, lr=5e-5, 3000 iter, max_seq=768
- **Best Val Loss:** 1.77 (iter 1500)
- **Peak Memory:** 7GB
- **Adapter Size:** 26.6MB

### ⚠️ Bilinen Problemler
- Base model (Qwen-2.5-3B) Türkçe'de zayıf
- Tekrarlama (repetition) problemi görülüyor
- Bazı faktüel bilgiler yanlış olabiliyor
- İlerde daha kaliteli veri ve/veya daha güçlü base model önerilir

---

## 🎯 Faz Hedefi

Qwen-2.5-3B-Instruct base modeli üzerine Türkçe iletişim, kültür ve doğal sohbet yeteneklerini geliştiren bir LoRA adaptörü eğitmek. Bu adaptör Türkçe konuşmalarda daha doğal, kültürel olarak uygun yanıtlar üretecek.

---

## 🏗️ Mimari Genel Bakış

```
┌──────────────────────────────────────────────────────────────┐
│                     BASE MODEL (Frozen)                      │
│                  Qwen-2.5-3B-Instruct                        │
│                    (~2GB, 4-bit)                             │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                   LoRA ADAPTER (Bu Faz)                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │           adapter_tr_chat.safetensors                  │  │
│  │                  (~50-100MB)                           │  │
│  │                                                        │  │
│  │  Eğitim Verisi:                                        │  │
│  │  - Aya Dataset (TR)                                    │  │
│  │  - Turkish Instructions                                │  │
│  │  - Manuel Türkçe sohbet örnekleri                      │  │
│  │                                                        │  │
│  │  LoRA Parametreleri:                                   │  │
│  │  - Rank (r): 8                                         │  │
│  │  - Alpha: 16                                           │  │
│  │  - Target: q_proj, v_proj                              │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                     MERGED OUTPUT                            │
│           Türkçe konuşan, kültürel bilgili model             │
└──────────────────────────────────────────────────────────────┘
```

---

## 📋 Detaylı Görev Listesi

### 2.1 Veri Seti Araştırma ve İndirme

#### 2.1.1 Aya Dataset (Türkçe) İnceleme
- [ ] Hugging Face'de `CohereForAI/aya_dataset` incele
- [ ] Türkçe subset boyutunu öğren
- [ ] Veri formatını incele (instruction/response pairs)
- [ ] Kalite örnekleri kontrol et
- [ ] Lisans kontrolü yap (Apache 2.0)

#### 2.1.2 Aya Dataset İndirme
- [ ] `scripts/download_aya_tr.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """Aya Dataset Türkçe subset'ini indir"""
  
  from datasets import load_dataset
  from pathlib import Path
  import json
  
  OUTPUT_DIR = Path("data/training/aya_tr")
  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
  
  def main():
      print("📥 Aya Dataset yükleniyor...")
      
      # Tüm dataset'i yükle
      dataset = load_dataset("CohereForAI/aya_dataset")
      
      # Türkçe filtrele
      tr_data = dataset.filter(lambda x: x["language"] == "Turkish")
      
      print(f"✅ Türkçe örnek sayısı: {len(tr_data['train'])}")
      
      # JSONL formatında kaydet
      output_file = OUTPUT_DIR / "aya_tr.jsonl"
      with open(output_file, "w", encoding="utf-8") as f:
          for item in tr_data["train"]:
              entry = {
                  "instruction": item["inputs"],
                  "input": "",
                  "output": item["targets"]
              }
              f.write(json.dumps(entry, ensure_ascii=False) + "\n")
      
      print(f"💾 Kaydedildi: {output_file}")
      print(f"📊 Dosya boyutu: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
  
  if __name__ == "__main__":
      main()
  ```
- [ ] Script'i çalıştır
- [ ] İndirilen veri sayısını not et

#### 2.1.3 Turkish Instructions Veri Seti
- [ ] Hugging Face'de Türkçe instruction dataset'leri ara:
  - `merve/turkish_instructions`
  - `umarbutler/open-australian-legal-qa` (alternatif format)
  - Diğer Türkçe QA dataset'leri
- [ ] En uygun olanları indir
- [ ] Formatı Alpaca formatına dönüştür

#### 2.1.4 Manuel Türkçe Sohbet Verileri
- [ ] `data/training/manual_tr/` dizini oluştur
- [ ] Aşağıdaki kategorilerde manuel örnekler yaz:

##### Selamlaşma Örnekleri (20+)
- [ ] `data/training/manual_tr/greetings.jsonl`:
  ```json
  {"instruction": "Merhaba!", "input": "", "output": "Merhaba! Size nasıl yardımcı olabilirim?"}
  {"instruction": "Günaydın", "input": "", "output": "Günaydın! Güzel bir gün geçirmenizi dilerim. Bugün size nasıl yardımcı olabilirim?"}
  {"instruction": "İyi akşamlar", "input": "", "output": "İyi akşamlar! Umarım gününüz güzel geçmiştir. Size nasıl yardımcı olabilirim?"}
  ```

##### Türk Kültürü Örnekleri (30+)
- [ ] `data/training/manual_tr/culture.jsonl`:
  ```json
  {"instruction": "Atatürk hakkında bilgi ver", "input": "", "output": "Mustafa Kemal Atatürk (1881-1938), Türkiye Cumhuriyeti'nin kurucusu ve ilk Cumhurbaşkanı'dır. Kurtuluş Savaşı'nın önderi olan Atatürk, modern Türkiye'nin temellerini atmış ve birçok devrimle ülkeyi çağdaş uygarlık seviyesine taşımıştır."}
  {"instruction": "Türk kahvesi nasıl yapılır?", "input": "", "output": "Türk kahvesi yapmak için: 1) Bir fincan soğuk su ve bir tatlı kaşığı öğütülmüş Türk kahvesini cezveye koyun. 2) İsteğe göre şeker ekleyin. 3) Kısık ateşte, karıştırarak köpürene kadar ısıtın. 4) Köpürmeye başlayınca ateşten alın, köpüğü fincanlara paylaştırın. 5) Tekrar ısıtıp servis edin. Afiyet olsun!"}
  ```

##### Deyim ve Atasözleri (30+)
- [ ] `data/training/manual_tr/proverbs.jsonl`:
  ```json
  {"instruction": "'Damlaya damlaya göl olur' ne demek?", "input": "", "output": "Bu atasözü, küçük birikimlerin zamanla büyük sonuçlar doğuracağını anlatır. Sabırla ve istikrarla yapılan küçük çabalar, uzun vadede önemli başarılara dönüşür. Tasarruf, öğrenme veya beceri geliştirme gibi konularda sıkça kullanılır."}
  {"instruction": "'Taşıma su ile değirmen dönmez' atasözünü açıkla", "input": "", "output": "Bu atasözü, dışarıdan getirilen veya geçici kaynaklarla sürdürülebilir bir iş yapılamayacağını anlatır. Başarılı olmak için kendi kaynaklarınızı, kendi gücünüzü kullanmanız gerekir. Başkalarına bağımlı kalarak kalıcı bir başarı elde etmek zordur."}
  ```

##### Günlük Konuşma (30+)
- [ ] `data/training/manual_tr/daily_chat.jsonl`:
  ```json
  {"instruction": "Bugün hava nasıl?", "input": "", "output": "Maalesef gerçek zamanlı hava durumu bilgisine erişimim yok. Ancak bulunduğunuz şehri söylerseniz, genel iklim özellikleri hakkında bilgi verebilirim. Veya bir hava durumu uygulaması kullanmanızı öneririm."}
  {"instruction": "Canım sıkılıyor, ne yapmalıyım?", "input": "", "output": "Can sıkıntısını gidermek için birkaç öneri: 1) Yeni bir hobi deneyin (resim, müzik, yemek yapma). 2) Bir kitap okuyun veya podcast dinleyin. 3) Dışarı çıkıp yürüyüş yapın. 4) Arkadaşlarınızla iletişime geçin. 5) Yeni bir beceri öğrenin. Siz ne tür aktivitelerden hoşlanırsınız?"}
  ```

---

### 2.2 Veri Seti Temizleme ve Hazırlama

#### 2.2.1 Veri Temizleme Script'i
- [ ] `scripts/clean_training_data.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """Eğitim verisini temizle ve birleştir"""
  
  import json
  import re
  from pathlib import Path
  from typing import List, Dict
  from collections import Counter
  
  INPUT_DIRS = [
      Path("data/training/aya_tr"),
      Path("data/training/manual_tr"),
  ]
  OUTPUT_FILE = Path("data/training/tr_chat_combined.jsonl")
  
  def clean_text(text: str) -> str:
      """Metni temizle"""
      # Fazla boşlukları kaldır
      text = re.sub(r'\s+', ' ', text)
      # Başta ve sondaki boşlukları kaldır
      text = text.strip()
      return text
  
  def is_valid_sample(sample: Dict) -> bool:
      """Örneğin geçerli olup olmadığını kontrol et"""
      instruction = sample.get("instruction", "")
      output = sample.get("output", "")
      
      # Boş kontrolleri
      if not instruction or not output:
          return False
      
      # Minimum uzunluk
      if len(instruction) < 5 or len(output) < 10:
          return False
      
      # Maximum uzunluk (token limiti için)
      if len(instruction) > 2000 or len(output) > 4000:
          return False
      
      return True
  
  def remove_duplicates(samples: List[Dict]) -> List[Dict]:
      """Duplicate'ları kaldır"""
      seen = set()
      unique = []
      
      for sample in samples:
          key = (sample["instruction"], sample["output"])
          if key not in seen:
              seen.add(key)
              unique.append(sample)
      
      return unique
  
  def main():
      all_samples = []
      
      for input_dir in INPUT_DIRS:
          if not input_dir.exists():
              print(f"⚠️ Dizin bulunamadı: {input_dir}")
              continue
          
          for file in input_dir.glob("*.jsonl"):
              print(f"📖 Okunuyor: {file}")
              with open(file, "r", encoding="utf-8") as f:
                  for line in f:
                      try:
                          sample = json.loads(line)
                          sample["instruction"] = clean_text(sample.get("instruction", ""))
                          sample["input"] = clean_text(sample.get("input", ""))
                          sample["output"] = clean_text(sample.get("output", ""))
                          
                          if is_valid_sample(sample):
                              all_samples.append(sample)
                      except json.JSONDecodeError:
                          continue
      
      print(f"\n📊 Toplam örnek (temizleme öncesi): {len(all_samples)}")
      
      # Duplicate kaldır
      all_samples = remove_duplicates(all_samples)
      print(f"📊 Toplam örnek (duplicate sonrası): {len(all_samples)}")
      
      # Kaydet
      OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
      with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
          for sample in all_samples:
              f.write(json.dumps(sample, ensure_ascii=False) + "\n")
      
      print(f"\n💾 Kaydedildi: {OUTPUT_FILE}")
      print(f"📊 Dosya boyutu: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.2f} MB")
      
      # İstatistikler
      instruction_lengths = [len(s["instruction"]) for s in all_samples]
      output_lengths = [len(s["output"]) for s in all_samples]
      
      print(f"\n📈 İstatistikler:")
      print(f"   Instruction uzunluğu: min={min(instruction_lengths)}, max={max(instruction_lengths)}, avg={sum(instruction_lengths)/len(instruction_lengths):.0f}")
      print(f"   Output uzunluğu: min={min(output_lengths)}, max={max(output_lengths)}, avg={sum(output_lengths)/len(output_lengths):.0f}")
  
  if __name__ == "__main__":
      main()
  ```

#### 2.2.2 Alpaca Format Dönüşümü
- [ ] Tüm verilerin şu formatta olduğunu doğrula:
  ```json
  {
    "instruction": "Kullanıcı talimatı/sorusu",
    "input": "Opsiyonel ek bağlam",
    "output": "Model yanıtı"
  }
  ```

#### 2.2.3 Train/Validation Bölme
- [ ] `scripts/split_dataset.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """Veri setini train/val olarak böl"""
  
  import json
  import random
  from pathlib import Path
  
  INPUT_FILE = Path("data/training/tr_chat_combined.jsonl")
  TRAIN_FILE = Path("data/training/tr_chat_train.jsonl")
  VAL_FILE = Path("data/training/tr_chat_val.jsonl")
  
  TRAIN_RATIO = 0.9
  RANDOM_SEED = 42
  
  def main():
      # Veriyi yükle
      samples = []
      with open(INPUT_FILE, "r", encoding="utf-8") as f:
          for line in f:
              samples.append(json.loads(line))
      
      # Karıştır
      random.seed(RANDOM_SEED)
      random.shuffle(samples)
      
      # Böl
      split_idx = int(len(samples) * TRAIN_RATIO)
      train_samples = samples[:split_idx]
      val_samples = samples[split_idx:]
      
      # Kaydet
      with open(TRAIN_FILE, "w", encoding="utf-8") as f:
          for sample in train_samples:
              f.write(json.dumps(sample, ensure_ascii=False) + "\n")
      
      with open(VAL_FILE, "w", encoding="utf-8") as f:
          for sample in val_samples:
              f.write(json.dumps(sample, ensure_ascii=False) + "\n")
      
      print(f"✅ Train: {len(train_samples)} örnek -> {TRAIN_FILE}")
      print(f"✅ Val: {len(val_samples)} örnek -> {VAL_FILE}")
  
  if __name__ == "__main__":
      main()
  ```

---

### 2.3 LoRA Eğitim Konfigürasyonu

#### 2.3.1 MLX LoRA Config Dosyası
- [ ] `configs/lora_tr_config.yaml` oluştur:
  ```yaml
  # EVO-TR Türkçe Uzman LoRA Konfigürasyonu
  
  # Model
  model: "./models/base/qwen-2.5-3b-instruct"
  
  # LoRA Parametreleri
  lora_parameters:
    rank: 8                    # LoRA rank (düşük = daha az parametre)
    alpha: 16                  # Scaling factor (genelde 2*rank)
    dropout: 0.05              # Dropout oranı
    scale: 1.0                 # LoRA scale
  
  # Target Modüller
  lora_layers: 16              # Son 16 layer'a LoRA uygula
  
  # Training Parametreleri
  training:
    batch_size: 1              # Mac M4 için güvenli
    learning_rate: 1.0e-4      # Öğrenme hızı
    epochs: 3                  # Epoch sayısı
    warmup_steps: 100          # Warmup adımları
    gradient_accumulation: 4   # Gradient biriktirme
    max_seq_length: 2048       # Maximum sequence uzunluğu
    
  # Veri
  data:
    train: "./data/training/tr_chat_train.jsonl"
    valid: "./data/training/tr_chat_val.jsonl"
  
  # Çıktı
  output:
    adapter_path: "./adapters/tr_chat"
    save_every: 500            # Her N adımda kaydet
  
  # Logging
  logging:
    log_level: "INFO"
    report_to: "tensorboard"
    log_dir: "./logs/training/tr_chat"
  ```

#### 2.3.2 Eğitim Script'i
- [ ] `scripts/train_lora_tr.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """
  EVO-TR Türkçe LoRA Eğitim Script'i
  
  Mac Mini M4 için optimize edilmiş MLX-LM tabanlı eğitim.
  """
  
  import argparse
  import json
  import yaml
  from pathlib import Path
  from datetime import datetime
  
  import mlx.core as mx
  from mlx_lm import load, generate
  from mlx_lm.tuner import train as lora_train
  from mlx_lm.tuner.trainer import TrainingArgs
  from mlx_lm.tuner.datasets import Dataset
  
  
  def load_config(config_path: str) -> dict:
      """YAML config dosyasını yükle"""
      with open(config_path, "r") as f:
          return yaml.safe_load(f)
  
  
  def prepare_dataset(data_path: str) -> list:
      """JSONL veri setini yükle"""
      samples = []
      with open(data_path, "r", encoding="utf-8") as f:
          for line in f:
              item = json.loads(line)
              # Qwen chat formatına dönüştür
              if item.get("input"):
                  prompt = f"{item['instruction']}\n\n{item['input']}"
              else:
                  prompt = item["instruction"]
              
              samples.append({
                  "prompt": prompt,
                  "response": item["output"]
              })
      return samples
  
  
  def main():
      parser = argparse.ArgumentParser(description="Türkçe LoRA Eğitimi")
      parser.add_argument(
          "--config", 
          type=str, 
          default="configs/lora_tr_config.yaml",
          help="Konfigürasyon dosyası"
      )
      parser.add_argument(
          "--resume",
          type=str,
          default=None,
          help="Checkpoint'tan devam et"
      )
      args = parser.parse_args()
      
      # Config yükle
      print(f"📖 Config yükleniyor: {args.config}")
      config = load_config(args.config)
      
      # Device kontrolü
      print(f"🖥️ Device: {mx.default_device()}")
      
      # Model yükle
      print(f"🤖 Model yükleniyor: {config['model']}")
      model, tokenizer = load(config["model"])
      
      # Veri yükle
      print(f"📚 Eğitim verisi yükleniyor...")
      train_data = prepare_dataset(config["data"]["train"])
      val_data = prepare_dataset(config["data"]["valid"])
      print(f"   Train: {len(train_data)} örnek")
      print(f"   Val: {len(val_data)} örnek")
      
      # Eğitim argümanları
      training_args = TrainingArgs(
          batch_size=config["training"]["batch_size"],
          iters=len(train_data) * config["training"]["epochs"],
          learning_rate=config["training"]["learning_rate"],
          steps_per_report=50,
          steps_per_eval=config["output"]["save_every"],
          adapter_path=config["output"]["adapter_path"],
          lora_layers=config.get("lora_layers", 16),
          lora_rank=config["lora_parameters"]["rank"],
          lora_scale=config["lora_parameters"]["scale"],
      )
      
      # Output dizinini oluştur
      Path(config["output"]["adapter_path"]).mkdir(parents=True, exist_ok=True)
      
      # Eğitimi başlat
      print(f"\n🚀 Eğitim başlıyor...")
      print(f"   Epochs: {config['training']['epochs']}")
      print(f"   Batch size: {config['training']['batch_size']}")
      print(f"   Learning rate: {config['training']['learning_rate']}")
      print(f"   LoRA rank: {config['lora_parameters']['rank']}")
      
      start_time = datetime.now()
      
      lora_train(
          model=model,
          tokenizer=tokenizer,
          args=training_args,
          train_dataset=train_data,
          val_dataset=val_data,
      )
      
      elapsed = datetime.now() - start_time
      print(f"\n✅ Eğitim tamamlandı! Süre: {elapsed}")
      print(f"💾 Adapter kaydedildi: {config['output']['adapter_path']}")
  
  
  if __name__ == "__main__":
      main()
  ```

---

### 2.4 LoRA Eğitimini Çalıştırma

#### 2.4.1 Eğitim Öncesi Kontroller
- [ ] Yeterli disk alanı var mı? (en az 5GB boş)
- [ ] Activity Monitor'da bellek durumu uygun mu?
- [ ] Gereksiz uygulamaları kapat
- [ ] MacBook'taysan şarjda olduğundan emin ol

#### 2.4.2 Eğitimi Başlatma
- [ ] Terminal'de virtual environment aktif et:
  ```bash
  source .venv/bin/activate
  cd /Users/kaan/Desktop/Kaan/Personal/agı-llm
  ```
- [ ] Eğitimi başlat:
  ```bash
  python scripts/train_lora_tr.py --config configs/lora_tr_config.yaml
  ```
- [ ] Loss değerlerini takip et
- [ ] İlerlemeyi not et

#### 2.4.3 Eğitim Sırasında İzleme
- [ ] Loss'un düştüğünü doğrula
- [ ] Overfitting belirtilerine dikkat et (val_loss artarken train_loss düşüyorsa)
- [ ] Memory kullanımını izle (Activity Monitor)
- [ ] Checkpoint'lerin kaydedildiğini kontrol et

#### 2.4.4 Eğitim Tamamlandığında
- [ ] Final adapter dosyalarını kontrol et:
  ```bash
  ls -la adapters/tr_chat/
  ```
- [ ] Beklenen dosyalar:
  - `adapter_config.json`
  - `adapters.safetensors`
- [ ] Dosya boyutunu not et (~50-100MB)

---

### 2.5 Adapter Test ve Değerlendirme

#### 2.5.1 Hızlı Test Script'i
- [ ] `scripts/test_adapter_tr.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """Türkçe adapter hızlı test"""
  
  from mlx_lm import load, generate
  from rich.console import Console
  from rich.panel import Panel
  
  console = Console()
  
  MODEL_PATH = "./models/base/qwen-2.5-3b-instruct"
  ADAPTER_PATH = "./adapters/tr_chat"
  
  TEST_PROMPTS = [
      "Merhaba! Nasılsın?",
      "Türk kahvesi nasıl yapılır?",
      "'Damlaya damlaya göl olur' ne demek?",
      "Atatürk hakkında kısa bilgi ver.",
      "Bana bir Türk atasözü söyle ve anlamını açıkla.",
      "İstanbul'un tarihi önemi nedir?",
      "Ramazan ayında neler yapılır?",
      "Türk misafirperverliği hakkında ne söylersin?",
  ]
  
  def main():
      console.print("\n[bold blue]🧪 Türkçe Adapter Testi[/bold blue]\n")
      
      # Base model yükle
      console.print("📥 Model yükleniyor (base)...")
      base_model, tokenizer = load(MODEL_PATH)
      
      # Adapter ile yükle
      console.print("📥 Model yükleniyor (adapter)...")
      adapter_model, _ = load(MODEL_PATH, adapter_path=ADAPTER_PATH)
      
      for prompt in TEST_PROMPTS:
          console.print(Panel(f"[cyan]Prompt:[/cyan] {prompt}", expand=False))
          
          # Base model yanıtı
          console.print("\n[yellow]Base Model:[/yellow]")
          base_response = generate(
              base_model, tokenizer, 
              prompt=prompt, 
              max_tokens=150,
              verbose=False
          )
          console.print(base_response)
          
          # Adapter yanıtı
          console.print("\n[green]Adapter (TR):[/green]")
          adapter_response = generate(
              adapter_model, tokenizer, 
              prompt=prompt, 
              max_tokens=150,
              verbose=False
          )
          console.print(adapter_response)
          
          console.print("\n" + "="*60 + "\n")
          
          input("Enter'a basarak devam et...")
  
  if __name__ == "__main__":
      main()
  ```

#### 2.5.2 Karşılaştırmalı Test
- [ ] Her test prompt için:
  - Base model yanıtını not et
  - Adapter yanıtını not et
  - Hangisinin daha iyi olduğunu değerlendir
- [ ] Değerlendirme kriterleri:
  - [ ] Türkçe dilbilgisi doğruluğu
  - [ ] Kültürel uygunluk
  - [ ] Doğallık
  - [ ] Bilgi doğruluğu

#### 2.5.3 Nicel Değerlendirme
- [ ] Perplexity hesapla (düşük = daha iyi)
- [ ] Türkçe benchmark varsa kullan
- [ ] Manuel puanlama (1-5 ölçeği)

---

### 2.6 Adapter Optimizasyonu (Opsiyonel)

#### 2.6.1 Hyperparameter Tuning
- [ ] Eğer sonuçlar yetersizse, şu parametreleri değiştirerek tekrar dene:
  - [ ] `rank`: 8 -> 16
  - [ ] `learning_rate`: 1e-4 -> 5e-5 veya 2e-4
  - [ ] `epochs`: 3 -> 5

#### 2.6.2 Veri Artırma
- [ ] Daha fazla manuel örnek ekle
- [ ] Parafraz ile veri çoğaltma dene
- [ ] Düşük kaliteli örnekleri temizle

#### 2.6.3 Final Adapter Kaydetme
- [ ] En iyi checkpoint'ı seç
- [ ] `adapters/tr_chat/` dizinine kopyala
- [ ] Metadata dosyası oluştur:
  ```json
  {
    "name": "adapter_tr_chat",
    "version": "1.0",
    "created": "2024-12-02",
    "base_model": "Qwen/Qwen2.5-3B-Instruct",
    "training_samples": 5000,
    "epochs": 3,
    "lora_rank": 8
  }
  ```

---

## ✅ Faz Tamamlanma Kriterleri

Bu faz tamamlanmış sayılması için:

1. [ ] Eğitim verisi hazır (3000+ örnek)
2. [ ] `data/training/tr_chat_train.jsonl` oluşturuldu
3. [ ] LoRA eğitimi tamamlandı
4. [ ] `adapters/tr_chat/` dizininde adapter var
5. [ ] Base vs Adapter karşılaştırması yapıldı
6. [ ] Türkçe yanıtlarda gözle görülür iyileşme var
7. [ ] Adapter boyutu makul (<200MB)

---

## ⏭️ Sonraki Faz

Faz 2 tamamlandıktan sonra → **FAZ-3-PYTHON-UZMAN.md** dosyasına geç.

---

## 🐛 Olası Sorunlar ve Çözümleri

### Out of Memory Hatası
```
RuntimeError: MPS backend out of memory
```
**Çözüm:**
- `batch_size: 1` yap
- `max_seq_length: 1024` düşür
- Gereksiz uygulamaları kapat
- `gradient_accumulation` artır

### Loss Düşmüyor
**Çözüm:**
- Learning rate'i artır (2e-4)
- Daha fazla epoch dene
- Veri kalitesini kontrol et

### Overfitting
**Çözüm:**
- Early stopping uygula
- Dropout artır (0.1)
- Daha fazla veri ekle

### Adapter Yüklenmiyor
**Çözüm:**
- Dosya yollarını kontrol et
- `adapter_config.json` formatını kontrol et
- Model versiyonu uyumluluğunu kontrol et

---

## 📊 Zaman Takibi

| Görev | Başlangıç | Bitiş | Süre |
|-------|-----------|-------|------|
| 2.1 Veri İndirme | | | |
| 2.2 Veri Temizleme | | | |
| 2.3 Config Hazırlama | | | |
| 2.4 Eğitim | | | |
| 2.5 Test | | | |
| 2.6 Optimizasyon | | | |
| **TOPLAM** | | | |

---

*Bu faz tamamlandığında, "✅ FAZ 2 TAMAMLANDI" olarak işaretle.*
