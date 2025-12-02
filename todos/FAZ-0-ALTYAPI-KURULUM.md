# 🛠️ FAZ 0: Altyapı ve Kurulum (The Skeleton)

**Durum:** ✅ TAMAMLANDI  
**Tahmini Süre:** 1-2 gün  
**Gerçekleşen Süre:** ~30 dakika  
**Öncelik:** 🔴 Kritik (Tüm fazların temeli)  
**Donanım:** Mac Mini M4 (Apple Silicon)

---

## 🎯 Faz Hedefi

Mac Mini M4 üzerinde EVO-TR projesinin çalışabileceği temel altyapıyı kurmak. Bu faz tamamlanmadan diğer fazlara geçilemez.

---

## 📋 Detaylı Görev Listesi

### 0.1 Sistem Gereksinimleri Kontrolü

#### 0.1.1 macOS Sürüm Kontrolü
- [x] Terminal'de `sw_vers` komutunu çalıştır
- [x] macOS Sonoma 14.0+ olduğunu doğrula ✅ **macOS 15.5** (Sequoia)
- [x] Eğer eski sürümse güncelleme yap (Gerek yok)
- [x] **Beklenen Çıktı:** `ProductVersion: 14.x.x` veya üzeri ✅

#### 0.1.2 Python Kurulum Kontrolü
- [x] `python3 --version` komutunu çalıştır
- [x] Python 3.10+ olduğunu doğrula ✅ **Python 3.11.14 kuruldu (brew)**
- [x] Eğer yoksa: `brew install python@3.11` ✅ Kuruldu
- [x] **Beklenen Çıktı:** `Python 3.10.x` veya üzeri ✅

#### 0.1.3 Xcode Command Line Tools
- [x] `xcode-select --version` komutunu çalıştır
- [x] Eğer hata verirse: `xcode-select --install` (Zaten kurulu)
- [x] Kurulumu tamamla (5-10 dakika sürebilir)
- [x] **Beklenen Çıktı:** `xcode-select version 2xxx` ✅ **version 2409**

#### 0.1.4 Homebrew Kontrolü
- [x] `brew --version` komutunu çalıştır
- [x] Eğer yoksa: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"` (Zaten kurulu)
- [x] `brew update` çalıştır ✅ (python@3.11 kurulurken otomatik güncellendi)
- [x] **Beklenen Çıktı:** `Homebrew 4.x.x` ✅ **Homebrew 5.0.3**

#### 0.1.5 Git Kontrolü
- [x] `git --version` komutunu çalıştır
- [x] Eğer yoksa: `brew install git` (Zaten kurulu)
- [x] **Beklenen Çıktı:** `git version 2.x.x` ✅ **git 2.39.5**

---

### 0.2 Proje Dizini ve Virtual Environment

#### 0.2.1 Proje Dizin Yapısı Oluşturma
- [x] Ana dizinde olduğundan emin ol: `cd /Users/kaan/Desktop/Kaan/Personal/agı-llm` ✅
- [x] Aşağıdaki dizinleri oluştur: ✅
  ```bash
  mkdir -p src/{router,experts,memory,inference,lifecycle}
  mkdir -p models/{base,router}
  mkdir -p adapters/{tr_chat,python_coder}
  mkdir -p data/{chromadb,training,intents}
  mkdir -p logs/conversations
  mkdir -p scripts
  mkdir -p tests
  mkdir -p configs
  ```
- [x] Her `src/` alt dizinine boş `__init__.py` ekle: ✅
  ```bash
  touch src/__init__.py
  touch src/router/__init__.py
  touch src/experts/__init__.py
  touch src/memory/__init__.py
  touch src/inference/__init__.py
  touch src/lifecycle/__init__.py
  ```

#### 0.2.2 Virtual Environment Oluşturma
- [x] Python venv oluştur: ✅ (Python 3.11.14)
  ```bash
  python3 -m venv .venv
  ```
- [x] Ortamı aktif et: ✅
  ```bash
  source .venv/bin/activate
  ```
- [x] Aktif olduğunu doğrula: ✅ `/Users/kaan/Desktop/Kaan/Personal/agı-llm/.venv/bin/python`
  ```bash
  which python
  # Beklenen: /Users/kaan/.../agı-llm/.venv/bin/python
  ```
- [x] pip güncelle: ✅ (pip 25.3, setuptools 80.9.0, wheel 0.45.1)
  ```bash
  pip install --upgrade pip setuptools wheel
  ```

#### 0.2.3 .gitignore Oluşturma
- [x] `.gitignore` dosyası oluştur: ✅ (Kapsamlı .gitignore oluşturuldu)
  ```gitignore
  # Virtual Environment
  .venv/
  venv/
  
  # Python
  __pycache__/
  *.py[cod]
  *.egg-info/
  
  # Environment
  .env
  .env.local
  
  # Models (büyük dosyalar)
  models/
  adapters/
  
  # Data
  data/chromadb/
  
  # Logs
  logs/
  
  # IDE
  .vscode/
  .idea/
  
  # OS
  .DS_Store
  ```

---

### 0.3 Temel Bağımlılıkların Kurulumu

#### 0.3.1 requirements.txt Oluşturma
- [x] `requirements.txt` dosyası oluştur: ✅ Oluşturuldu
  ```txt
  # Apple MLX Framework
  mlx>=0.10.0
  mlx-lm>=0.10.0
  
  # Hugging Face
  transformers>=4.36.0
  huggingface_hub>=0.20.0
  tokenizers>=0.15.0
  
  # Vector Database
  chromadb>=0.4.22
  
  # Embeddings
  sentence-transformers>=2.2.2
  
  # Utilities
  python-dotenv>=1.0.0
  tqdm>=4.66.0
  rich>=13.7.0
  
  # Data Processing
  pandas>=2.1.0
  numpy>=1.26.0
  
  # API (opsiyonel, ileride)
  # fastapi>=0.109.0
  # uvicorn>=0.27.0
  ```

#### 0.3.2 Bağımlılıkları Kur
- [x] MLX kurulumu (Apple Silicon için): ✅ mlx 0.30.0, mlx-lm 0.28.3
  ```bash
  pip install mlx mlx-lm
  ```
- [x] Kurulumu doğrula: ✅
  ```bash
  python -c "import mlx; print(mlx.__version__)"
  ```
- [x] Tüm bağımlılıkları kur: ✅ (transformers, chromadb, sentence-transformers, pandas, numpy...)
  ```bash
  pip install -r requirements.txt
  ```
- [x] Kurulumu test et: ✅
  ```bash
  python -c "import transformers; import chromadb; import sentence_transformers; print('OK')"
  ```

#### 0.3.3 MLX Metal Desteği Kontrolü
- [x] Metal backend'in aktif olduğunu doğrula: ✅ **Device(gpu, 0)**
  ```python
  import mlx.core as mx
  print(f"Default device: {mx.default_device()}")
  # Beklenen: Device(gpu, 0)
  ```

---

### 0.4 Hugging Face Ayarları

#### 0.4.1 .env Dosyası Kontrolü
- [x] `.env` dosyasını kontrol et: ✅
  ```bash
  cat .env
  ```
- [x] `HF_TOKEN` değişkeninin var olduğunu doğrula ✅ **HF_TOKEN mevcut**
- [x] Eğer yoksa ekle: (Zaten vardı)
  ```env
  HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
  ```

#### 0.4.2 python-dotenv Entegrasyonu
- [x] `configs/settings.py` oluştur: ✅ Oluşturuldu
  ```python
  import os
  from dotenv import load_dotenv
  
  load_dotenv()
  
  class Settings:
      HF_TOKEN = os.getenv("HF_TOKEN")
      BASE_MODEL_PATH = "./models/base/qwen-2.5-3b-instruct"
      ADAPTER_TR_PATH = "./adapters/tr_chat"
      ADAPTER_PYTHON_PATH = "./adapters/python_coder"
      CHROMA_PERSIST_DIR = "./data/chromadb"
      LOG_DIR = "./logs"
      
  settings = Settings()
  ```

#### 0.4.3 Hugging Face CLI Login
- [x] CLI ile giriş yap: ✅
  ```bash
  huggingface-cli login --token $HF_TOKEN
  ```
- [x] Token'ı test et: ✅ **kaangml** (orgs: mcp-course)
  ```bash
  huggingface-cli whoami
  ```
- [x] **Beklenen Çıktı:** Kullanıcı adın görünmeli ✅

#### 0.4.4 Model Erişim Testi
- [x] Qwen modeline erişim olduğunu doğrula: ✅ **Qwen/Qwen2.5-3B-Instruct** (7.5M+ downloads)
  ```python
  from huggingface_hub import HfApi
  api = HfApi()
  model_info = api.model_info("Qwen/Qwen2.5-3B-Instruct")
  print(f"Model: {model_info.modelId}")
  ```

---

### 0.5 Base Model İndirme ve Test

#### 0.5.1 MLX Formatında Model İndirme
- [x] Modeli MLX formatına dönüştür ve indir (4-bit quantized): ✅
  ```bash
  python -m mlx_lm.convert \
      --hf-path Qwen/Qwen2.5-3B-Instruct \
      --mlx-path ./models/base/qwen-2.5-3b-instruct \
      -q
  ```
- [x] İndirme süresini not et (internet hızına göre 10-30 dk) ✅ ~15 dakika
- [x] İndirilen dosyaları kontrol et: ✅ 14 dosya
  ```bash
  ls -la ./models/base/qwen-2.5-3b-instruct/
  ```
- [x] Model boyutunu kontrol et (~2GB olmalı): ✅ **1.6 GB** (4-bit quantized)
  ```bash
  du -sh ./models/base/qwen-2.5-3b-instruct/
  ```

#### 0.5.2 Hello World Testi
- [x] Basit inference testi yap: ✅
  ```bash
  python -m mlx_lm.generate \
      --model ./models/base/qwen-2.5-3b-instruct \
      --prompt "Merhaba, ben bir yapay zeka asistanıyım." \
      --max-tokens 100
  ```
- [x] Yanıtın mantıklı olduğunu doğrula ✅ "Merhaba! Türkçe olarak karşılığım Qwen oluyorum."
- [x] Token/saniye hızını not et (hedef: 30+ t/s) ✅ **57.2 t/s**

#### 0.5.3 Bellek Kullanımı Kontrolü
- [x] Activity Monitor'dan bellek kullanımını kontrol et ✅
- [x] Model yüklendiğinde ~3-4GB kullanılmalı ✅ **Peak memory: 1.829 GB**
- [x] Eğer fazla bellek kullanılıyorsa not al ✅ Bellek kullanımı optimal!
- [ ] Eğer fazla bellek kullanılıyorsa not al

---

### 0.6 Test Script'i Oluşturma

#### 0.6.1 Kurulum Doğrulama Script'i
- [x] `scripts/verify_setup.py` oluştur: ✅ Oluşturuldu
  ```python
  #!/usr/bin/env python3
  """EVO-TR Kurulum Doğrulama Script'i"""
  
  import sys
  from rich.console import Console
  from rich.table import Table
  
  console = Console()
  
  def check_import(module_name):
      try:
          __import__(module_name)
          return True, "✅"
      except ImportError as e:
          return False, f"❌ {e}"
  
  def main():
      console.print("\n[bold blue]🔍 EVO-TR Kurulum Kontrolü[/bold blue]\n")
      
      table = Table(title="Bağımlılık Durumu")
      table.add_column("Modül", style="cyan")
      table.add_column("Durum", style="green")
      
      modules = [
          "mlx", "mlx_lm", "transformers", 
          "huggingface_hub", "chromadb", 
          "sentence_transformers", "dotenv"
      ]
      
      all_ok = True
      for mod in modules:
          ok, status = check_import(mod)
          table.add_row(mod, status)
          if not ok:
              all_ok = False
      
      console.print(table)
      
      # MLX Device Check
      try:
          import mlx.core as mx
          device = str(mx.default_device())
          console.print(f"\n[bold]MLX Device:[/bold] {device}")
          if "gpu" in device:
              console.print("[green]✅ Metal GPU aktif[/green]")
          else:
              console.print("[yellow]⚠️ CPU modunda çalışıyor[/yellow]")
      except Exception as e:
          console.print(f"[red]❌ MLX Hatası: {e}[/red]")
      
      # .env Check
      import os
      if os.path.exists(".env"):
          console.print("\n[green]✅ .env dosyası mevcut[/green]")
          from dotenv import load_dotenv
          load_dotenv()
          if os.getenv("HF_TOKEN"):
              console.print("[green]✅ HF_TOKEN tanımlı[/green]")
          else:
              console.print("[red]❌ HF_TOKEN tanımlı değil[/red]")
              all_ok = False
      else:
          console.print("\n[red]❌ .env dosyası bulunamadı[/red]")
          all_ok = False
      
      # Model Check
      import os
      model_path = "./models/base/qwen-2.5-3b-instruct"
      if os.path.exists(model_path):
          console.print(f"\n[green]✅ Base model mevcut: {model_path}[/green]")
      else:
          console.print(f"\n[yellow]⚠️ Base model henüz indirilmemiş[/yellow]")
      
      # Final Status
      if all_ok:
          console.print("\n[bold green]🎉 Kurulum başarılı! Faz 1'e geçebilirsin.[/bold green]\n")
      else:
          console.print("\n[bold red]⚠️ Bazı sorunlar var. Yukarıdaki hataları düzelt.[/bold red]\n")
          sys.exit(1)
  
  if __name__ == "__main__":
      main()
  ```

- [x] Script'i çalıştırılabilir yap: ✅
  ```bash
  chmod +x scripts/verify_setup.py
  ```

---

## ✅ Faz Tamamlanma Kriterleri

Bu faz tamamlanmış sayılması için:

1. [x] `python3 --version` → 3.10+ ✅ **Python 3.11.14**
2. [x] `.venv` aktif ve çalışıyor ✅
3. [x] Tüm requirements kurulu ✅
4. [x] `.env` dosyasında `HF_TOKEN` var ✅
5. [x] `huggingface-cli whoami` çalışıyor ✅ **kaangml**
6. [x] Base model indirilmiş (~2GB) ✅ **1.63 GB**
7. [x] Hello World testi başarılı ✅
8. [x] `scripts/verify_setup.py` hatasız çalışıyor ✅
9. [x] Token/saniye hızı 30+ t/s ✅ **57.2 t/s**

---

## ⏭️ Sonraki Faz

Faz 0 tamamlandıktan sonra → **FAZ-1-ROUTER.md** dosyasına geç.

---

## 🐛 Olası Sorunlar ve Çözümleri

### MLX Kurulum Hatası
```
ERROR: Could not find a version that satisfies the requirement mlx
```
**Çözüm:** 
- macOS 13.5+ ve Apple Silicon olduğundan emin ol
- `pip install --upgrade pip` yap

### Metal Device Bulunamıyor
```
Default device: Device(cpu, 0)
```
**Çözüm:**
- Xcode Command Line Tools'u yeniden kur
- macOS'u güncelle

### HF Token Hatası
```
huggingface_hub.utils._errors.LocalEntryNotFoundError
```
**Çözüm:**
- Token'ın geçerli olduğunu kontrol et
- https://huggingface.co/settings/tokens adresinden yeni token oluştur

---

## 📊 Zaman Takibi

| Görev | Başlangıç | Bitiş | Süre |
|-------|-----------|-------|------|
| 0.1 Sistem Kontrolü | | | |
| 0.2 Dizin & Venv | | | |
| 0.3 Bağımlılıklar | | | |
| 0.4 HF Ayarları | | | |
| 0.5 Model İndirme | | | |
| 0.6 Test Script | | | |
| **TOPLAM** | | | |

---

*Bu faz tamamlandığında, "✅ FAZ 0 TAMAMLANDI" olarak işaretle.*
