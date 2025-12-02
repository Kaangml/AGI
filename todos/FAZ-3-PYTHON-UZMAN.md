# 🐍 FAZ 3: Python Uzman - LoRA Adaptör #2

**Durum:** ⬜ Başlanmadı  
**Tahmini Süre:** 2-3 gün  
**Öncelik:** 🟠 Yüksek  
**Bağımlılık:** Faz 0, 1, 2 tamamlanmış olmalı

---

## 🎯 Faz Hedefi

Qwen-2.5-3B-Instruct base modeli üzerine Python programlama, kod yazma, debugging ve algoritma geliştirme yeteneklerini güçlendiren bir LoRA adaptörü eğitmek.

---

## 🏗️ Mimari Genel Bakış

```
┌──────────────────────────────────────────────────────────────┐
│                     BASE MODEL (Frozen)                      │
│                  Qwen-2.5-3B-Instruct                        │
└─────────────────────────┬────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                   LoRA ADAPTER (Bu Faz)                      │
│  ┌────────────────────────────────────────────────────────┐  │
│  │        adapter_python_coder.safetensors                │  │
│  │                  (~50-100MB)                           │  │
│  │                                                        │  │
│  │  Eğitim Verisi:                                        │  │
│  │  - HumanEval                                           │  │
│  │  - MBPP (Mostly Basic Programming Problems)            │  │
│  │  - CodeAlpaca                                          │  │
│  │  - Manuel Python örnekleri                             │  │
│  │                                                        │  │
│  │  Yetenekler:                                           │  │
│  │  - Fonksiyon yazma                                     │  │
│  │  - Debug / Hata ayıklama                               │  │
│  │  - Kod açıklama                                        │  │
│  │  - Algoritma implementasyonu                           │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 📋 Detaylı Görev Listesi

### 3.1 Veri Seti Araştırma ve İndirme

#### 3.1.1 HumanEval Dataset
- [ ] Hugging Face'de `openai/humaneval` incele
- [ ] Veri formatını anla:
  ```python
  {
      "task_id": "HumanEval/0",
      "prompt": "def has_close_elements(...",
      "canonical_solution": "for idx, elem...",
      "test": "def check(candidate)..."
  }
  ```
- [ ] Python subset'ini kontrol et (tamamı Python)

#### 3.1.2 MBPP Dataset
- [ ] `google-research/mbpp` incele
- [ ] Örnek sayısını not et (~1000 problem)
- [ ] Format:
  ```python
  {
      "text": "Write a function to...",
      "code": "def function_name(...)...",
      "test_list": ["assert function_name(...) == ..."]
  }
  ```

#### 3.1.3 CodeAlpaca Dataset
- [ ] `sahil2801/CodeAlpaca-20k` incele
- [ ] Multi-language olduğu için Python filtresi uygula
- [ ] Instruction-response formatında olduğunu doğrula

#### 3.1.4 Veri İndirme Script'i
- [ ] `scripts/download_code_datasets.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """Kod eğitim veri setlerini indir"""
  
  from datasets import load_dataset
  from pathlib import Path
  import json
  
  OUTPUT_DIR = Path("data/training/python_code")
  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
  
  
  def download_humaneval():
      print("📥 HumanEval indiriliyor...")
      dataset = load_dataset("openai_humaneval")
      
      samples = []
      for item in dataset["test"]:
          samples.append({
              "instruction": f"Complete the following Python function:\n\n{item['prompt']}",
              "input": "",
              "output": item["canonical_solution"]
          })
      
      output_file = OUTPUT_DIR / "humaneval.jsonl"
      with open(output_file, "w", encoding="utf-8") as f:
          for sample in samples:
              f.write(json.dumps(sample, ensure_ascii=False) + "\n")
      
      print(f"✅ HumanEval: {len(samples)} örnek -> {output_file}")
      return len(samples)
  
  
  def download_mbpp():
      print("📥 MBPP indiriliyor...")
      dataset = load_dataset("google-research-datasets/mbpp", "full")
      
      samples = []
      for item in dataset["train"]:
          instruction = item["text"]
          code = item["code"]
          
          # Test case'leri de ekle
          tests = "\n".join(item["test_list"])
          
          samples.append({
              "instruction": f"{instruction}\n\nTest cases:\n{tests}",
              "input": "",
              "output": code
          })
      
      output_file = OUTPUT_DIR / "mbpp.jsonl"
      with open(output_file, "w", encoding="utf-8") as f:
          for sample in samples:
              f.write(json.dumps(sample, ensure_ascii=False) + "\n")
      
      print(f"✅ MBPP: {len(samples)} örnek -> {output_file}")
      return len(samples)
  
  
  def download_code_alpaca():
      print("📥 CodeAlpaca indiriliyor...")
      dataset = load_dataset("sahil2801/CodeAlpaca-20k")
      
      # Python filtresi
      python_keywords = ["python", "def ", "class ", "import ", "print("]
      
      samples = []
      for item in dataset["train"]:
          instruction = item["instruction"].lower()
          output = item["output"].lower()
          
          # Python ile ilgili mi kontrol et
          is_python = any(kw in instruction or kw in output for kw in python_keywords)
          
          if is_python:
              samples.append({
                  "instruction": item["instruction"],
                  "input": item.get("input", ""),
                  "output": item["output"]
              })
      
      output_file = OUTPUT_DIR / "code_alpaca_python.jsonl"
      with open(output_file, "w", encoding="utf-8") as f:
          for sample in samples:
              f.write(json.dumps(sample, ensure_ascii=False) + "\n")
      
      print(f"✅ CodeAlpaca (Python): {len(samples)} örnek -> {output_file}")
      return len(samples)
  
  
  def main():
      total = 0
      total += download_humaneval()
      total += download_mbpp()
      total += download_code_alpaca()
      
      print(f"\n🎉 Toplam: {total} Python kod örneği indirildi!")
  
  
  if __name__ == "__main__":
      main()
  ```

---

### 3.2 Manuel Python Örnekleri Ekleme

#### 3.2.1 Temel Python Kavramları (30+ örnek)
- [ ] `data/training/manual_python/basics.jsonl` oluştur:
  ```json
  {"instruction": "Python'da bir liste oluştur ve elemanlarını yazdır", "input": "", "output": "# Liste oluşturma\nfruits = ['elma', 'armut', 'muz', 'çilek']\n\n# Elemanları yazdırma\nfor fruit in fruits:\n    print(fruit)\n\n# Alternatif: join ile\nprint(', '.join(fruits))"}
  {"instruction": "Python'da dictionary kullanımını göster", "input": "", "output": "# Dictionary oluşturma\nperson = {\n    'isim': 'Ahmet',\n    'yaş': 25,\n    'şehir': 'İstanbul'\n}\n\n# Değer okuma\nprint(person['isim'])  # Ahmet\nprint(person.get('yaş'))  # 25\n\n# Değer ekleme/güncelleme\nperson['meslek'] = 'Mühendis'\n\n# Döngü ile gezinme\nfor key, value in person.items():\n    print(f'{key}: {value}')"}
  {"instruction": "Python'da fonksiyon nasıl tanımlanır?", "input": "", "output": "# Basit fonksiyon\ndef selamla(isim):\n    \"\"\"Verilen ismi selamlar.\"\"\"\n    return f'Merhaba, {isim}!'\n\n# Varsayılan parametreli\ndef topla(a, b=0):\n    return a + b\n\n# *args ve **kwargs\ndef esnek_fonksiyon(*args, **kwargs):\n    print('Args:', args)\n    print('Kwargs:', kwargs)\n\n# Kullanım\nprint(selamla('Kaan'))  # Merhaba, Kaan!\nprint(topla(5, 3))  # 8\nesnek_fonksiyon(1, 2, 3, isim='test')"}
  ```

#### 3.2.2 Hata Ayıklama Örnekleri (30+ örnek)
- [ ] `data/training/manual_python/debugging.jsonl` oluştur:
  ```json
  {"instruction": "IndexError: list index out of range hatası alıyorum, nasıl düzeltirim?", "input": "my_list = [1, 2, 3]\nprint(my_list[5])", "output": "Bu hata, listenin olmayan bir indeksine erişmeye çalıştığınızda oluşur.\n\n**Sorun:** `my_list` sadece 3 eleman içeriyor (indeksler: 0, 1, 2), ama siz indeks 5'e erişmeye çalışıyorsunuz.\n\n**Çözüm:**\n```python\nmy_list = [1, 2, 3]\n\n# Güvenli erişim - indeks kontrolü\nindex = 5\nif index < len(my_list):\n    print(my_list[index])\nelse:\n    print(f'Hata: İndeks {index} geçersiz. Liste uzunluğu: {len(my_list)}')\n\n# Veya try-except kullanın\ntry:\n    print(my_list[5])\nexcept IndexError:\n    print('Geçersiz indeks!')\n```"}
  {"instruction": "TypeError: 'NoneType' object is not subscriptable hatası ne anlama geliyor?", "input": "", "output": "Bu hata, `None` değerine sahip bir değişkene indeksleme (`[]`) uygulamaya çalıştığınızda oluşur.\n\n**Yaygın nedenler:**\n1. Fonksiyon `return` yapmıyor\n2. `.sort()` gibi in-place metodların sonucunu değişkene atama\n\n**Örnek ve Çözüm:**\n```python\n# YANLIŞ\nmy_list = [3, 1, 2]\nsorted_list = my_list.sort()  # sort() None döner!\nprint(sorted_list[0])  # TypeError!\n\n# DOĞRU\nmy_list = [3, 1, 2]\nmy_list.sort()  # In-place sıralar\nprint(my_list[0])  # 1\n\n# VEYA\nmy_list = [3, 1, 2]\nsorted_list = sorted(my_list)  # Yeni liste döner\nprint(sorted_list[0])  # 1\n```"}
  ```

#### 3.2.3 Algoritma Örnekleri (25+ örnek)
- [ ] `data/training/manual_python/algorithms.jsonl` oluştur:
  ```json
  {"instruction": "Binary search algoritmasını Python'da implement et", "input": "", "output": "def binary_search(arr, target):\n    \"\"\"\n    Sıralı bir dizide binary search yapar.\n    \n    Args:\n        arr: Sıralı liste\n        target: Aranan değer\n    \n    Returns:\n        Bulunan indeks veya -1\n    \"\"\"\n    left, right = 0, len(arr) - 1\n    \n    while left <= right:\n        mid = (left + right) // 2\n        \n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    \n    return -1\n\n# Kullanım\nnumbers = [1, 3, 5, 7, 9, 11, 13]\nindex = binary_search(numbers, 7)\nprint(f'7 bulundu: indeks {index}')  # 7 bulundu: indeks 3"}
  {"instruction": "Fibonacci serisini hesaplayan fonksiyon yaz", "input": "", "output": "# Recursive (yavaş, büyük n için uygun değil)\ndef fib_recursive(n):\n    if n <= 1:\n        return n\n    return fib_recursive(n-1) + fib_recursive(n-2)\n\n# Iterative (hızlı)\ndef fib_iterative(n):\n    if n <= 1:\n        return n\n    \n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n\n# Memoization ile (hızlı, recursive)\nfrom functools import lru_cache\n\n@lru_cache(maxsize=None)\ndef fib_memo(n):\n    if n <= 1:\n        return n\n    return fib_memo(n-1) + fib_memo(n-2)\n\n# Test\nfor i in range(10):\n    print(fib_iterative(i), end=' ')  # 0 1 1 2 3 5 8 13 21 34"}
  ```

#### 3.2.4 Best Practices ve Clean Code (20+ örnek)
- [ ] `data/training/manual_python/best_practices.jsonl` oluştur:
  ```json
  {"instruction": "Python'da dosya okuma için best practice göster", "input": "", "output": "# Context manager kullanın (dosya otomatik kapanır)\nwith open('dosya.txt', 'r', encoding='utf-8') as f:\n    content = f.read()\n\n# Satır satır okuma (büyük dosyalar için)\nwith open('dosya.txt', 'r', encoding='utf-8') as f:\n    for line in f:\n        process(line.strip())\n\n# Pathlib kullanımı (modern yaklaşım)\nfrom pathlib import Path\n\nfile_path = Path('data') / 'dosya.txt'\nif file_path.exists():\n    content = file_path.read_text(encoding='utf-8')\n\n# YAPMAYIN:\n# f = open('dosya.txt', 'r')  # Dosya kapanmayabilir\n# content = f.read()\n# f.close()"}
  {"instruction": "Python'da exception handling nasıl yapılmalı?", "input": "", "output": "# Spesifik exception yakalayın\ntry:\n    result = 10 / 0\nexcept ZeroDivisionError:\n    print('Sıfıra bölme hatası!')\n    result = 0\n\n# Birden fazla exception\ntry:\n    value = int(input('Sayı girin: '))\n    result = 100 / value\nexcept ValueError:\n    print('Geçersiz sayı formatı')\nexcept ZeroDivisionError:\n    print('Sıfıra bölme hatası')\nfinally:\n    print('İşlem tamamlandı')\n\n# Custom exception\nclass ValidationError(Exception):\n    pass\n\ndef validate_age(age):\n    if age < 0:\n        raise ValidationError('Yaş negatif olamaz')\n    return age\n\n# YAPMAYIN:\n# except:  # Tüm hataları yakalar, tehlikeli\n# except Exception:  # Çok genel"}
  ```

---

### 3.3 Veri Birleştirme ve Temizleme

#### 3.3.1 Kod Veri Temizleme
- [ ] `scripts/clean_code_data.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """Python kod verisini temizle ve birleştir"""
  
  import json
  import re
  from pathlib import Path
  from typing import List, Dict
  
  INPUT_DIRS = [
      Path("data/training/python_code"),
      Path("data/training/manual_python"),
  ]
  OUTPUT_FILE = Path("data/training/python_coder_combined.jsonl")
  
  
  def clean_code(code: str) -> str:
      """Kod temizleme"""
      # Gereksiz boş satırları kaldır
      lines = code.split('\n')
      cleaned_lines = []
      prev_empty = False
      
      for line in lines:
          is_empty = len(line.strip()) == 0
          if not (is_empty and prev_empty):
              cleaned_lines.append(line)
          prev_empty = is_empty
      
      return '\n'.join(cleaned_lines).strip()
  
  
  def is_valid_python(code: str) -> bool:
      """Geçerli Python kodu mu kontrol et"""
      try:
          compile(code, '<string>', 'exec')
          return True
      except SyntaxError:
          return False
  
  
  def is_valid_sample(sample: Dict) -> bool:
      """Örneğin geçerli olup olmadığını kontrol et"""
      instruction = sample.get("instruction", "")
      output = sample.get("output", "")
      
      # Boş kontrolleri
      if not instruction or not output:
          return False
      
      # Minimum uzunluk
      if len(instruction) < 10 or len(output) < 20:
          return False
      
      # Maximum uzunluk
      if len(instruction) > 3000 or len(output) > 6000:
          return False
      
      return True
  
  
  def main():
      all_samples = []
      valid_count = 0
      invalid_count = 0
      
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
                          sample["output"] = clean_code(sample.get("output", ""))
                          
                          if is_valid_sample(sample):
                              all_samples.append(sample)
                              valid_count += 1
                          else:
                              invalid_count += 1
                      except json.JSONDecodeError:
                          invalid_count += 1
                          continue
      
      print(f"\n📊 Geçerli: {valid_count}, Geçersiz: {invalid_count}")
      
      # Duplicate kaldır
      seen = set()
      unique_samples = []
      for sample in all_samples:
          key = sample["instruction"][:100]  # İlk 100 karakter
          if key not in seen:
              seen.add(key)
              unique_samples.append(sample)
      
      print(f"📊 Unique: {len(unique_samples)}")
      
      # Kaydet
      OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
      with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
          for sample in unique_samples:
              f.write(json.dumps(sample, ensure_ascii=False) + "\n")
      
      print(f"\n💾 Kaydedildi: {OUTPUT_FILE}")
  
  
  if __name__ == "__main__":
      main()
  ```

#### 3.3.2 Train/Val Bölme
- [ ] Faz 2'deki split script'ini kullan
- [ ] %90 train, %10 validation

---

### 3.4 LoRA Eğitim Konfigürasyonu

#### 3.4.1 Config Dosyası
- [ ] `configs/lora_python_config.yaml` oluştur:
  ```yaml
  # EVO-TR Python Uzman LoRA Konfigürasyonu
  
  # Model
  model: "./models/base/qwen-2.5-3b-instruct"
  
  # LoRA Parametreleri
  lora_parameters:
    rank: 8
    alpha: 16
    dropout: 0.05
    scale: 1.0
  
  # Target Modüller
  lora_layers: 16
  
  # Training Parametreleri
  training:
    batch_size: 1
    learning_rate: 1.0e-4
    epochs: 3
    warmup_steps: 100
    gradient_accumulation: 4
    max_seq_length: 2048
    
  # Veri
  data:
    train: "./data/training/python_coder_train.jsonl"
    valid: "./data/training/python_coder_val.jsonl"
  
  # Çıktı
  output:
    adapter_path: "./adapters/python_coder"
    save_every: 500
  
  # Logging
  logging:
    log_level: "INFO"
    log_dir: "./logs/training/python_coder"
  ```

#### 3.4.2 Eğitim Script'i
- [ ] `scripts/train_lora_python.py` oluştur (Faz 2'deki script'i adapte et):
  ```python
  #!/usr/bin/env python3
  """
  EVO-TR Python LoRA Eğitim Script'i
  """
  
  # Faz 2'deki script ile aynı yapı, sadece config farklı
  # scripts/train_lora_tr.py'dan kopyala ve config path'i değiştir
  
  # Default config:
  # --config configs/lora_python_config.yaml
  ```

---

### 3.5 Eğitimi Çalıştırma

#### 3.5.1 Eğitim Öncesi
- [ ] Disk alanı kontrolü
- [ ] Memory kontrolü
- [ ] Önceki eğitim loglarını yedekle

#### 3.5.2 Eğitimi Başlat
- [ ] ```bash
  python scripts/train_lora_python.py --config configs/lora_python_config.yaml
  ```
- [ ] Loss değerlerini izle
- [ ] ~2-4 saat sürebilir

#### 3.5.3 Checkpoint Yönetimi
- [ ] Checkpoint'lerin kaydedildiğini doğrula
- [ ] En iyi val_loss'a sahip checkpoint'ı not et

---

### 3.6 Test ve Değerlendirme

#### 3.6.1 Hızlı Test Script'i
- [ ] `scripts/test_adapter_python.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """Python adapter hızlı test"""
  
  from mlx_lm import load, generate
  from rich.console import Console
  from rich.syntax import Syntax
  from rich.panel import Panel
  
  console = Console()
  
  MODEL_PATH = "./models/base/qwen-2.5-3b-instruct"
  ADAPTER_PATH = "./adapters/python_coder"
  
  TEST_PROMPTS = [
      "Python'da bir liste içindeki tekrar eden elemanları kaldıran fonksiyon yaz",
      "Binary search algoritmasını implement et",
      "Verilen bir string'in palindrome olup olmadığını kontrol eden fonksiyon yaz",
      "Python'da dosya okuyup satır sayısını bulan kod yaz",
      "Bubble sort algoritmasını implement et",
      "Python'da dictionary'yi değerlerine göre sıralayan kod yaz",
      "Fibonacci serisinin n. elemanını döndüren fonksiyon yaz",
      "Python'da bir class oluştur: Kişi (isim, yaş, meslek)",
  ]
  
  def main():
      console.print("\n[bold blue]🐍 Python Adapter Testi[/bold blue]\n")
      
      # Adapter ile yükle
      console.print("📥 Model yükleniyor...")
      model, tokenizer = load(MODEL_PATH, adapter_path=ADAPTER_PATH)
      
      for prompt in TEST_PROMPTS:
          console.print(Panel(f"[cyan]Prompt:[/cyan] {prompt}", expand=False))
          
          response = generate(
              model, tokenizer, 
              prompt=f"Aşağıdaki görevi Python ile çöz:\n\n{prompt}",
              max_tokens=500,
              verbose=False
          )
          
          # Kod bloklarını syntax highlighting ile göster
          if "```python" in response:
              code = response.split("```python")[1].split("```")[0]
              syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
              console.print(syntax)
          else:
              console.print(response)
          
          console.print("\n" + "="*60 + "\n")
          input("Enter'a basarak devam et...")
  
  
  if __name__ == "__main__":
      main()
  ```

#### 3.6.2 Kod Doğruluk Testi
- [ ] `scripts/validate_code_output.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """Üretilen kodun çalışıp çalışmadığını test et"""
  
  import subprocess
  import tempfile
  from mlx_lm import load, generate
  
  def test_code(code: str) -> tuple[bool, str]:
      """Kodu çalıştır ve sonucu döndür"""
      with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
          f.write(code)
          f.flush()
          
          try:
              result = subprocess.run(
                  ['python3', f.name],
                  capture_output=True,
                  text=True,
                  timeout=10
              )
              
              if result.returncode == 0:
                  return True, result.stdout
              else:
                  return False, result.stderr
          except subprocess.TimeoutExpired:
              return False, "Timeout"
          except Exception as e:
              return False, str(e)
  
  
  TEST_CASES = [
      {
          "prompt": "1'den 10'a kadar sayıları yazdır",
          "expected_output": "1\n2\n3\n4\n5\n6\n7\n8\n9\n10"
      },
      {
          "prompt": "Bir listenin toplamını hesapla: [1, 2, 3, 4, 5]",
          "expected_output": "15"
      }
  ]
  
  # Test implementation...
  ```

#### 3.6.3 Performans Karşılaştırması
- [ ] Base model vs Adapter karşılaştırması yap
- [ ] Aşağıdaki metrikleri ölç:
  - [ ] Syntax doğruluğu (compile edilebilir mi?)
  - [ ] Mantıksal doğruluk (beklenen çıktıyı veriyor mu?)
  - [ ] Kod kalitesi (okunabilirlik, best practices)

---

### 3.7 Final Optimizasyon

#### 3.7.1 Kod Formatı İyileştirme
- [ ] Prompt template'i optimize et:
  ```
  ### Görev
  {instruction}
  
  ### Python Kodu
  ```python
  ```
- [ ] System prompt ekle (opsiyonel)

#### 3.7.2 Adapter Kaydetme
- [ ] En iyi checkpoint'ı `adapters/python_coder/` dizinine kopyala
- [ ] Metadata oluştur:
  ```json
  {
    "name": "adapter_python_coder",
    "version": "1.0",
    "created": "2024-12-02",
    "base_model": "Qwen/Qwen2.5-3B-Instruct",
    "training_samples": 8000,
    "epochs": 3,
    "lora_rank": 8,
    "capabilities": ["code_generation", "debugging", "algorithms"]
  }
  ```

---

## ✅ Faz Tamamlanma Kriterleri

1. [ ] Eğitim verisi hazır (5000+ örnek)
2. [ ] LoRA eğitimi tamamlandı
3. [ ] `adapters/python_coder/` dizininde adapter var
4. [ ] Üretilen kodların %80+'ı syntax-valid
5. [ ] Base model'e göre belirgin iyileşme var
6. [ ] Test script'leri çalışıyor

---

## ⏭️ Sonraki Faz

Faz 3 tamamlandıktan sonra → **FAZ-4-HAFIZA-RAG.md** dosyasına geç.

---

## 🐛 Olası Sorunlar ve Çözümleri

### Üretilen Kod Syntax Hatası Veriyor
**Çözüm:**
- Eğitim verisindeki syntax hatalarını temizle
- Prompt template'i iyileştir
- Temperature'ı düşür (0.3-0.5)

### Çok Uzun/Kısa Kod Üretiyor
**Çözüm:**
- `max_tokens` ayarla
- Stop token ekle (```\n)
- Veri setindeki kod uzunluklarını normalize et

---

## 📊 Zaman Takibi

| Görev | Başlangıç | Bitiş | Süre |
|-------|-----------|-------|------|
| 3.1 Veri İndirme | | | |
| 3.2 Manuel Örnekler | | | |
| 3.3 Temizleme | | | |
| 3.4 Config | | | |
| 3.5 Eğitim | | | |
| 3.6 Test | | | |
| **TOPLAM** | | | |

---

*Bu faz tamamlandığında, "✅ FAZ 3 TAMAMLANDI" olarak işaretle.*
