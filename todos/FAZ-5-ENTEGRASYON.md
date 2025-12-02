# 🔗 FAZ 5: Sistem Entegrasyonu (The Orchestration)

**Durum:** ⬜ Başlanmadı  
**Tahmini Süre:** 2-3 gün  
**Öncelik:** 🟠 Yüksek  
**Bağımlılık:** Faz 0, 1, 2, 3, 4 tamamlanmış olmalı

---

## 🎯 Faz Hedefi

Tüm bileşenleri (Router, LoRA Adaptörleri, Hafıza Sistemi) birleştirerek çalışan bir uçtan uca sistem oluşturmak. Kullanıcı mesajı girdiğinde otomatik olarak doğru adaptöre yönlendirilecek ve hafıza ile zenginleştirilmiş yanıt üretilecek.

---

## 🏗️ Mimari Genel Bakış

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EVO-TR ORCHESTRATOR                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │  USER INPUT     │───▶│     ROUTER      │───▶│   ADAPTER SELECTION     │  │
│  │                 │    │  (Intent Class) │    │                         │  │
│  │  "Python'da    │    │                 │    │  ┌─────────────────────┐ │  │
│  │   liste nasıl  │    │  Intent:        │    │  │ adapter_tr_chat     │ │  │
│  │   sıralarım?"  │    │  code_python    │    │  ├─────────────────────┤ │  │
│  │                 │    │  Confidence:   │───▶│  │ adapter_python_coder│◀│  │
│  │                 │    │  0.94          │    │  ├─────────────────────┤ │  │
│  └─────────────────┘    └─────────────────┘    │  │ base_model          │ │  │
│                                                │  └─────────────────────┘ │  │
│                                                └─────────────────────────┘  │
│                                                           │                 │
│  ┌─────────────────────────────────────────────────────────▼───────────────┐│
│  │                        INFERENCE ENGINE                                 ││
│  │  ┌───────────────────────────────────────────────────────────────────┐  ││
│  │  │                    MLX-LM Server                                  │  ││
│  │  │                                                                   │  ││
│  │  │  Base Model: Qwen-2.5-3B-Instruct                                │  ││
│  │  │  Active Adapter: adapter_python_coder                            │  ││
│  │  │  Device: MPS (Apple Silicon)                                     │  ││
│  │  │                                                                   │  ││
│  │  │  ┌─────────────────────────────────────────────────────────────┐ │  ││
│  │  │  │ Augmented Prompt:                                           │ │  ││
│  │  │  │                                                             │ │  ││
│  │  │  │ [Hafızadan]: Kullanıcı Python projesi yapıyor              │ │  ││
│  │  │  │ [Geçmiş]: Son 3 soru da kod ile ilgiliydi                  │ │  ││
│  │  │  │ [Soru]: Python'da liste nasıl sıralarım?                   │ │  ││
│  │  │  └─────────────────────────────────────────────────────────────┘ │  ││
│  │  └───────────────────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                           │                 │
│  ┌─────────────────────────────────────────────────────────▼───────────────┐│
│  │                         RESPONSE + LOGGING                              ││
│  │                                                                         ││
│  │  Response: "Python'da listeyi sıralamak için sorted() veya .sort()..." ││
│  │                                                                         ││
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       ││
│  │  │ Context Buffer   │  │ ChromaDB Memory  │  │ Log File         │       ││
│  │  │ (Güncel mesaj    │  │ (Önemli bilgiler │  │ (Tüm sohbet      │       ││
│  │  │  eklendi)        │  │  kaydedildi)     │  │  kaydedildi)     │       ││
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Detaylı Görev Listesi

### 5.1 LoRA Manager Geliştirme

#### 5.1.1 Adapter Registry
- [ ] `configs/adapters.json` oluştur:
  ```json
  {
    "adapters": {
      "adapter_tr_chat": {
        "path": "./adapters/tr_chat",
        "description": "Türkçe sohbet ve kültür uzmanı",
        "intents": ["general_chat", "turkish_culture"],
        "priority": 1
      },
      "adapter_python_coder": {
        "path": "./adapters/python_coder",
        "description": "Python programlama uzmanı",
        "intents": ["code_python", "code_debug", "code_explain"],
        "priority": 1
      },
      "base_model": {
        "path": null,
        "description": "Temel model (adapter yok)",
        "intents": ["general_knowledge", "memory_recall"],
        "priority": 0
      }
    },
    "default_adapter": "base_model",
    "cache_adapters": true,
    "max_cached_adapters": 2
  }
  ```

#### 5.1.2 LoRA Manager Class
- [ ] `src/experts/lora_manager.py` oluştur:
  ```python
  """
  EVO-TR LoRA Yöneticisi
  
  Adaptörlerin yüklenmesi, değiştirilmesi ve cache yönetimi.
  """
  
  import json
  from pathlib import Path
  from typing import Dict, Optional, Tuple, Any
  from collections import OrderedDict
  import time
  
  import mlx.core as mx
  from mlx_lm import load
  
  
  class LoRAManager:
      """LoRA adaptör yöneticisi"""
      
      def __init__(
          self,
          base_model_path: str = "./models/base/qwen-2.5-3b-instruct",
          adapters_config_path: str = "./configs/adapters.json",
          max_cache_size: int = 2
      ):
          self.base_model_path = base_model_path
          self.max_cache_size = max_cache_size
          
          # Config yükle
          with open(adapters_config_path, "r") as f:
              self.config = json.load(f)
          
          # Adapter cache (LRU-style)
          self._adapter_cache: OrderedDict = OrderedDict()
          
          # Base model ve tokenizer (her zaman yüklü)
          self._base_model = None
          self._tokenizer = None
          self._current_adapter: Optional[str] = None
          
          print(f"✅ LoRAManager başlatıldı")
          print(f"   Kayıtlı adapter sayısı: {len(self.config['adapters'])}")
      
      def _ensure_base_model_loaded(self) -> None:
          """Base model'in yüklü olduğundan emin ol"""
          if self._base_model is None:
              print(f"📥 Base model yükleniyor: {self.base_model_path}")
              start = time.time()
              self._base_model, self._tokenizer = load(self.base_model_path)
              elapsed = time.time() - start
              print(f"✅ Base model yüklendi ({elapsed:.1f}s)")
      
      def get_model(
          self, 
          adapter_id: str
      ) -> Tuple[Any, Any, str]:
          """
          Belirtilen adapter ile model döndür.
          
          Args:
              adapter_id: Adapter ID (örn: "adapter_python_coder")
              
          Returns:
              (model, tokenizer, adapter_id)
          """
          self._ensure_base_model_loaded()
          
          # Base model isteniyorsa direkt döndür
          if adapter_id == "base_model" or adapter_id is None:
              self._current_adapter = None
              return self._base_model, self._tokenizer, "base_model"
          
          # Adapter config kontrolü
          if adapter_id not in self.config["adapters"]:
              print(f"⚠️ Bilinmeyen adapter: {adapter_id}, base_model kullanılıyor")
              return self._base_model, self._tokenizer, "base_model"
          
          adapter_config = self.config["adapters"][adapter_id]
          adapter_path = adapter_config.get("path")
          
          if not adapter_path:
              return self._base_model, self._tokenizer, "base_model"
          
          # Cache'de var mı?
          if adapter_id in self._adapter_cache:
              # LRU: En son erişileni sona taşı
              self._adapter_cache.move_to_end(adapter_id)
              model = self._adapter_cache[adapter_id]
              self._current_adapter = adapter_id
              return model, self._tokenizer, adapter_id
          
          # Cache'de yok, yükle
          print(f"📥 Adapter yükleniyor: {adapter_id}")
          start = time.time()
          
          model, _ = load(
              self.base_model_path,
              adapter_path=adapter_path
          )
          
          elapsed = time.time() - start
          print(f"✅ Adapter yüklendi ({elapsed:.1f}s)")
          
          # Cache'e ekle
          self._adapter_cache[adapter_id] = model
          
          # Cache boyutu aşıldıysa en eskiyi kaldır
          while len(self._adapter_cache) > self.max_cache_size:
              oldest = next(iter(self._adapter_cache))
              del self._adapter_cache[oldest]
              print(f"🗑️ Cache'den kaldırıldı: {oldest}")
          
          self._current_adapter = adapter_id
          return model, self._tokenizer, adapter_id
      
      def get_adapter_for_intent(self, intent: str) -> str:
          """Intent'e göre adapter ID döndür"""
          for adapter_id, config in self.config["adapters"].items():
              if intent in config.get("intents", []):
                  return adapter_id
          
          return self.config.get("default_adapter", "base_model")
      
      def list_adapters(self) -> Dict:
          """Tüm adaptörleri listele"""
          return {
              adapter_id: {
                  "description": config.get("description"),
                  "intents": config.get("intents", []),
                  "cached": adapter_id in self._adapter_cache
              }
              for adapter_id, config in self.config["adapters"].items()
          }
      
      def get_current_adapter(self) -> Optional[str]:
          """Şu an aktif adapter'ı döndür"""
          return self._current_adapter
      
      def clear_cache(self) -> int:
          """Cache'i temizle"""
          count = len(self._adapter_cache)
          self._adapter_cache.clear()
          return count
      
      def get_stats(self) -> Dict:
          """Manager istatistikleri"""
          return {
              "base_model_loaded": self._base_model is not None,
              "current_adapter": self._current_adapter,
              "cached_adapters": list(self._adapter_cache.keys()),
              "cache_size": len(self._adapter_cache),
              "max_cache_size": self.max_cache_size
          }
  
  
  # Singleton
  _lora_manager: Optional[LoRAManager] = None
  
  
  def get_lora_manager() -> LoRAManager:
      """Global LoRAManager instance"""
      global _lora_manager
      if _lora_manager is None:
          _lora_manager = LoRAManager()
      return _lora_manager
  ```

---

### 5.2 Inference Engine Geliştirme

#### 5.2.1 MLX Inference Wrapper
- [ ] `src/inference/mlx_inference.py` oluştur:
  ```python
  """
  EVO-TR Inference Engine
  
  MLX-LM tabanlı text generation.
  """
  
  from typing import Optional, Generator, Dict, Any
  from dataclasses import dataclass
  import time
  
  from mlx_lm import generate
  from mlx_lm.utils import generate_step
  
  
  @dataclass
  class GenerationConfig:
      """Generation parametreleri"""
      max_tokens: int = 512
      temperature: float = 0.7
      top_p: float = 0.9
      repetition_penalty: float = 1.1
      stop_tokens: tuple = ("<|im_end|>", "\n\n\n")
  
  
  class InferenceEngine:
      """MLX tabanlı inference engine"""
      
      def __init__(self, default_config: Optional[GenerationConfig] = None):
          self.default_config = default_config or GenerationConfig()
      
      def generate(
          self,
          model: Any,
          tokenizer: Any,
          prompt: str,
          config: Optional[GenerationConfig] = None,
          stream: bool = False
      ) -> str | Generator[str, None, None]:
          """
          Text generation.
          
          Args:
              model: MLX model
              tokenizer: Tokenizer
              prompt: Input prompt
              config: Generation config
              stream: Streaming output
              
          Returns:
              Generated text or generator
          """
          cfg = config or self.default_config
          
          if stream:
              return self._generate_stream(model, tokenizer, prompt, cfg)
          else:
              return self._generate_full(model, tokenizer, prompt, cfg)
      
      def _generate_full(
          self,
          model: Any,
          tokenizer: Any,
          prompt: str,
          config: GenerationConfig
      ) -> str:
          """Tam yanıt üret"""
          start_time = time.time()
          
          response = generate(
              model,
              tokenizer,
              prompt=prompt,
              max_tokens=config.max_tokens,
              temp=config.temperature,
              top_p=config.top_p,
              repetition_penalty=config.repetition_penalty,
              verbose=False
          )
          
          # Stop token'ları temizle
          for stop in config.stop_tokens:
              if stop in response:
                  response = response.split(stop)[0]
          
          elapsed = time.time() - start_time
          tokens = len(tokenizer.encode(response))
          
          # Debug bilgisi
          print(f"   ⏱️ {elapsed:.2f}s, {tokens} tokens, {tokens/elapsed:.1f} t/s")
          
          return response.strip()
      
      def _generate_stream(
          self,
          model: Any,
          tokenizer: Any,
          prompt: str,
          config: GenerationConfig
      ) -> Generator[str, None, None]:
          """Streaming generation"""
          # Token encode
          input_ids = tokenizer.encode(prompt, return_tensors="np")
          
          generated_tokens = []
          
          for token in generate_step(
              model,
              input_ids,
              max_tokens=config.max_tokens,
              temp=config.temperature,
              top_p=config.top_p
          ):
              generated_tokens.append(token)
              
              # Token'ı decode et
              text = tokenizer.decode(generated_tokens)
              
              # Stop token kontrolü
              should_stop = False
              for stop in config.stop_tokens:
                  if stop in text:
                      text = text.split(stop)[0]
                      should_stop = True
                      break
              
              yield text
              
              if should_stop:
                  break
      
      def format_chat_prompt(
          self,
          user_message: str,
          system_prompt: Optional[str] = None,
          context: Optional[str] = None
      ) -> str:
          """
          Qwen chat formatında prompt oluştur.
          
          Args:
              user_message: Kullanıcı mesajı
              system_prompt: System prompt
              context: Ek context (hafıza, geçmiş)
          """
          parts = []
          
          # System prompt
          if system_prompt:
              parts.append(f"<|im_start|>system\n{system_prompt}<|im_end|>")
          
          # Context (hafızadan gelen)
          if context:
              parts.append(f"<|im_start|>system\n{context}<|im_end|>")
          
          # User message
          parts.append(f"<|im_start|>user\n{user_message}<|im_end|>")
          
          # Assistant prefix
          parts.append("<|im_start|>assistant\n")
          
          return "\n".join(parts)
  
  
  # Singleton
  _inference_engine: Optional[InferenceEngine] = None
  
  
  def get_inference_engine() -> InferenceEngine:
      """Global InferenceEngine instance"""
      global _inference_engine
      if _inference_engine is None:
          _inference_engine = InferenceEngine()
      return _inference_engine
  ```

---

### 5.3 Ana Orchestrator Geliştirme

#### 5.3.1 Orchestrator Class
- [ ] `src/orchestrator.py` oluştur:
  ```python
  """
  EVO-TR Orchestrator
  
  Tüm bileşenleri birleştiren ana orkestrasyon katmanı.
  """
  
  from typing import Optional, Dict, Any
  from dataclasses import dataclass
  from datetime import datetime
  import json
  
  from .router.classifier import get_classifier
  from .experts.lora_manager import get_lora_manager
  from .memory.rag_pipeline import get_rag_pipeline
  from .inference.mlx_inference import get_inference_engine, GenerationConfig
  
  
  @dataclass
  class Response:
      """Orchestrator yanıtı"""
      text: str
      intent: str
      confidence: float
      adapter_used: str
      processing_time: float
      memory_results: int
  
  
  class Orchestrator:
      """
      EVO-TR Ana Orkestratörü
      
      Kullanıcı mesajını alır, router ile yönlendirir,
      hafızadan context alır, uygun adapter ile yanıt üretir.
      """
      
      DEFAULT_SYSTEM_PROMPT = """Sen EVO-TR, modüler ve sürekli öğrenen bir yapay zeka asistanısın.
  Türkçe konuşuyorsun ve kullanıcıya yardımcı olmak için eğitildin.
  Yanıtların doğal, samimi ve bilgilendirici olmalı."""
      
      def __init__(
          self,
          system_prompt: Optional[str] = None,
          generation_config: Optional[GenerationConfig] = None,
          use_memory: bool = True,
          use_router: bool = True
      ):
          self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
          self.generation_config = generation_config or GenerationConfig()
          self.use_memory = use_memory
          self.use_router = use_router
          
          # Bileşenler
          self.router = get_classifier() if use_router else None
          self.lora_manager = get_lora_manager()
          self.rag = get_rag_pipeline() if use_memory else None
          self.inference = get_inference_engine()
          
          print("✅ Orchestrator başlatıldı")
      
      def chat(
          self,
          user_message: str,
          force_adapter: Optional[str] = None,
          save_to_memory: bool = True
      ) -> Response:
          """
          Kullanıcı mesajına yanıt üret.
          
          Args:
              user_message: Kullanıcı mesajı
              force_adapter: Zorla belirli adapter kullan
              save_to_memory: Hafızaya kaydet
              
          Returns:
              Response objesi
          """
          import time
          start_time = time.time()
          
          # 1. Router ile intent belirleme
          if force_adapter:
              intent = "forced"
              confidence = 1.0
              adapter_id = force_adapter
          elif self.use_router:
              route_result = self.router.predict(user_message)
              intent = route_result["intent"]
              confidence = route_result["confidence"]
              adapter_id = route_result["adapter_id"]
          else:
              intent = "unknown"
              confidence = 0.0
              adapter_id = "base_model"
          
          print(f"🎯 Intent: {intent} (conf: {confidence:.2f}) → {adapter_id}")
          
          # 2. Hafızadan context al
          memory_context = ""
          memory_count = 0
          
          if self.use_memory and self.rag:
              memory_results = self.rag.retrieve(user_message)
              memory_count = len(memory_results)
              
              if memory_results:
                  memory_context = self.rag.format_retrieved_context(memory_results)
                  print(f"📚 Hafızadan {memory_count} sonuç bulundu")
          
          # 3. Uygun model/adapter yükle
          model, tokenizer, used_adapter = self.lora_manager.get_model(adapter_id)
          
          # 4. Prompt oluştur
          full_context = memory_context if memory_context else None
          prompt = self.inference.format_chat_prompt(
              user_message=user_message,
              system_prompt=self.system_prompt,
              context=full_context
          )
          
          # 5. Yanıt üret
          print("🤖 Yanıt üretiliyor...")
          response_text = self.inference.generate(
              model=model,
              tokenizer=tokenizer,
              prompt=prompt,
              config=self.generation_config
          )
          
          # 6. Hafızaya kaydet
          if self.use_memory and self.rag and save_to_memory:
              self.rag.process_response(
                  user_query=user_message,
                  model_response=response_text,
                  save_to_memory=True
              )
          
          processing_time = time.time() - start_time
          
          return Response(
              text=response_text,
              intent=intent,
              confidence=confidence,
              adapter_used=used_adapter,
              processing_time=processing_time,
              memory_results=memory_count
          )
      
      def get_status(self) -> Dict:
          """Sistem durumu"""
          return {
              "router": "active" if self.use_router else "disabled",
              "memory": "active" if self.use_memory else "disabled",
              "lora_manager": self.lora_manager.get_stats(),
              "rag": self.rag.get_stats() if self.rag else None
          }
      
      def reset_session(self) -> None:
          """Session sıfırla (kısa süreli hafızayı temizle)"""
          if self.rag:
              self.rag.buffer.clear()
          print("✅ Session sıfırlandı")
  
  
  # Singleton
  _orchestrator: Optional[Orchestrator] = None
  
  
  def get_orchestrator() -> Orchestrator:
      """Global Orchestrator instance"""
      global _orchestrator
      if _orchestrator is None:
          _orchestrator = Orchestrator()
      return _orchestrator
  ```

---

### 5.4 CLI Interface Geliştirme

#### 5.4.1 Interactive Chat CLI
- [ ] `src/cli.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """
  EVO-TR Interactive Chat CLI
  """
  
  import sys
  from rich.console import Console
  from rich.panel import Panel
  from rich.markdown import Markdown
  from rich.table import Table
  
  from orchestrator import get_orchestrator
  
  console = Console()
  
  
  def print_help():
      """Yardım mesajı"""
      help_text = """
  **EVO-TR Komutları:**
  
  - `/help` - Bu yardım mesajını göster
  - `/status` - Sistem durumunu göster
  - `/adapters` - Mevcut adaptörleri listele
  - `/adapter <id>` - Adapter değiştir (örn: /adapter adapter_python_coder)
  - `/memory` - Hafıza istatistikleri
  - `/clear` - Kısa süreli hafızayı temizle
  - `/exit` veya `/quit` - Çıkış
      """
      console.print(Markdown(help_text))
  
  
  def print_status(orchestrator):
      """Sistem durumu"""
      status = orchestrator.get_status()
      
      table = Table(title="Sistem Durumu")
      table.add_column("Bileşen", style="cyan")
      table.add_column("Durum", style="green")
      
      table.add_row("Router", status["router"])
      table.add_row("Memory", status["memory"])
      table.add_row("Aktif Adapter", status["lora_manager"]["current_adapter"] or "base_model")
      table.add_row("Cache", f"{status['lora_manager']['cache_size']} adapter")
      
      console.print(table)
  
  
  def print_adapters(orchestrator):
      """Adapter listesi"""
      adapters = orchestrator.lora_manager.list_adapters()
      
      table = Table(title="Mevcut Adaptörler")
      table.add_column("ID", style="cyan")
      table.add_column("Açıklama", style="white")
      table.add_column("Intent'ler", style="yellow")
      table.add_column("Cache", style="green")
      
      for adapter_id, info in adapters.items():
          table.add_row(
              adapter_id,
              info["description"],
              ", ".join(info["intents"][:3]),
              "✅" if info["cached"] else "❌"
          )
      
      console.print(table)
  
  
  def main():
      console.print(Panel(
          "[bold blue]🤖 EVO-TR Interactive Chat[/bold blue]\n"
          "Modüler ve Sürekli Öğrenen YZ Asistanı\n\n"
          "[dim]Yardım için /help yazın. Çıkmak için /exit yazın.[/dim]",
          expand=False
      ))
      
      # Orchestrator'ı başlat
      console.print("\n[yellow]⏳ Sistem başlatılıyor...[/yellow]\n")
      orchestrator = get_orchestrator()
      console.print("[green]✅ Sistem hazır![/green]\n")
      
      force_adapter = None
      
      while True:
          try:
              # Prompt
              adapter_label = f"[{force_adapter}]" if force_adapter else ""
              user_input = console.input(f"[bold cyan]Sen{adapter_label}:[/bold cyan] ")
              
              if not user_input.strip():
                  continue
              
              # Komut kontrolü
              if user_input.startswith("/"):
                  cmd = user_input.lower().split()
                  
                  if cmd[0] in ["/exit", "/quit"]:
                      console.print("\n[yellow]👋 Görüşürüz![/yellow]\n")
                      break
                  
                  elif cmd[0] == "/help":
                      print_help()
                  
                  elif cmd[0] == "/status":
                      print_status(orchestrator)
                  
                  elif cmd[0] == "/adapters":
                      print_adapters(orchestrator)
                  
                  elif cmd[0] == "/adapter":
                      if len(cmd) > 1:
                          force_adapter = cmd[1] if cmd[1] != "auto" else None
                          console.print(f"[green]✅ Adapter: {force_adapter or 'auto'}[/green]")
                      else:
                          console.print("[yellow]Kullanım: /adapter <id> veya /adapter auto[/yellow]")
                  
                  elif cmd[0] == "/memory":
                      if orchestrator.rag:
                          stats = orchestrator.rag.get_stats()
                          console.print(f"Hafıza: {stats['memory_stats']['total_memories']} kayıt")
                          console.print(f"Buffer: {stats['buffer_stats']['message_count']} mesaj")
                  
                  elif cmd[0] == "/clear":
                      orchestrator.reset_session()
                      console.print("[green]✅ Session temizlendi[/green]")
                  
                  else:
                      console.print(f"[red]❌ Bilinmeyen komut: {cmd[0]}[/red]")
                  
                  continue
              
              # Normal mesaj - yanıt üret
              response = orchestrator.chat(
                  user_message=user_input,
                  force_adapter=force_adapter
              )
              
              # Yanıtı göster
              console.print()
              console.print(Panel(
                  response.text,
                  title=f"[bold green]EVO-TR[/bold green] "
                        f"[dim]({response.adapter_used}, {response.processing_time:.1f}s)[/dim]",
                  expand=False
              ))
              console.print()
              
          except KeyboardInterrupt:
              console.print("\n[yellow]Ctrl+C - Çıkmak için /exit yazın[/yellow]")
              continue
          except Exception as e:
              console.print(f"[red]❌ Hata: {e}[/red]")
              continue
  
  
  if __name__ == "__main__":
      main()
  ```

---

### 5.5 Entegrasyon Testleri

#### 5.5.1 Uçtan Uca Test Script
- [ ] `scripts/test_e2e.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """Uçtan uca entegrasyon testi"""
  
  from rich.console import Console
  from rich.table import Table
  
  from src.orchestrator import get_orchestrator
  
  console = Console()
  
  TEST_CASES = [
      # (mesaj, beklenen_intent, açıklama)
      ("Merhaba, nasılsın?", "general_chat", "Selamlaşma"),
      ("Python'da liste nasıl sıralarım?", "code_python", "Kod sorusu"),
      ("Bu hata ne demek: IndexError", "code_debug", "Debug sorusu"),
      ("Atatürk hakkında bilgi ver", "turkish_culture", "Kültür sorusu"),
      ("Daha önce sana ne söyledim?", "memory_recall", "Hafıza sorusu"),
  ]
  
  
  def main():
      console.print("\n[bold blue]🧪 EVO-TR Uçtan Uca Test[/bold blue]\n")
      
      orchestrator = get_orchestrator()
      
      results = []
      
      for message, expected_intent, description in TEST_CASES:
          console.print(f"\n[cyan]Test:[/cyan] {description}")
          console.print(f"[dim]Mesaj: {message}[/dim]")
          
          try:
              response = orchestrator.chat(message, save_to_memory=False)
              
              intent_match = response.intent == expected_intent
              has_response = len(response.text) > 10
              
              results.append({
                  "description": description,
                  "intent_match": intent_match,
                  "has_response": has_response,
                  "adapter": response.adapter_used,
                  "time": response.processing_time
              })
              
              status = "✅" if (intent_match and has_response) else "❌"
              console.print(f"{status} Intent: {response.intent} (beklenen: {expected_intent})")
              console.print(f"   Adapter: {response.adapter_used}")
              console.print(f"   Süre: {response.processing_time:.2f}s")
              console.print(f"   Yanıt: {response.text[:100]}...")
              
          except Exception as e:
              results.append({
                  "description": description,
                  "intent_match": False,
                  "has_response": False,
                  "error": str(e)
              })
              console.print(f"[red]❌ Hata: {e}[/red]")
      
      # Özet
      console.print("\n" + "="*60 + "\n")
      
      table = Table(title="Test Özeti")
      table.add_column("Test", style="cyan")
      table.add_column("Intent", style="yellow")
      table.add_column("Yanıt", style="green")
      table.add_column("Süre", style="magenta")
      
      success = 0
      for r in results:
          intent = "✅" if r.get("intent_match") else "❌"
          response = "✅" if r.get("has_response") else "❌"
          time_str = f"{r.get('time', 0):.1f}s" if "time" in r else "N/A"
          
          table.add_row(r["description"], intent, response, time_str)
          
          if r.get("intent_match") and r.get("has_response"):
              success += 1
      
      console.print(table)
      console.print(f"\n[bold]Başarı: {success}/{len(results)} ({100*success/len(results):.0f}%)[/bold]\n")
  
  
  if __name__ == "__main__":
      main()
  ```

#### 5.5.2 Performance Test
- [ ] `scripts/test_performance.py` oluştur
- [ ] Latency ölçümleri
- [ ] Memory kullanımı ölçümleri
- [ ] Throughput testleri

---

### 5.6 Logging Sistemi

#### 5.6.1 Structured Logger
- [ ] `src/lifecycle/logger.py` oluştur:
  ```python
  """
  EVO-TR Logging Sistemi
  """
  
  import json
  import logging
  from datetime import datetime
  from pathlib import Path
  from typing import Optional, Dict, Any
  
  
  class ConversationLogger:
      """Konuşma loglama"""
      
      def __init__(self, log_dir: str = "./logs/conversations"):
          self.log_dir = Path(log_dir)
          self.log_dir.mkdir(parents=True, exist_ok=True)
          
          # Günlük dosya adı
          self.current_date = datetime.now().strftime("%Y-%m-%d")
          self.log_file = self.log_dir / f"{self.current_date}.jsonl"
      
      def log_interaction(
          self,
          user_message: str,
          response_text: str,
          intent: str,
          confidence: float,
          adapter_used: str,
          processing_time: float,
          metadata: Optional[Dict] = None
      ) -> None:
          """Etkileşimi logla"""
          entry = {
              "timestamp": datetime.now().isoformat(),
              "user_message": user_message,
              "response": response_text,
              "intent": intent,
              "confidence": confidence,
              "adapter": adapter_used,
              "processing_time": processing_time,
              "metadata": metadata or {}
          }
          
          with open(self.log_file, "a", encoding="utf-8") as f:
              f.write(json.dumps(entry, ensure_ascii=False) + "\n")
      
      def get_daily_logs(self, date: Optional[str] = None) -> list:
          """Günlük logları getir"""
          target_date = date or self.current_date
          log_file = self.log_dir / f"{target_date}.jsonl"
          
          if not log_file.exists():
              return []
          
          logs = []
          with open(log_file, "r", encoding="utf-8") as f:
              for line in f:
                  logs.append(json.loads(line))
          
          return logs
  
  
  # Singleton
  _logger: Optional[ConversationLogger] = None
  
  
  def get_conversation_logger() -> ConversationLogger:
      global _logger
      if _logger is None:
          _logger = ConversationLogger()
      return _logger
  ```

---

## ✅ Faz Tamamlanma Kriterleri

1. [ ] LoRA Manager adapter'ları yönetebiliyor
2. [ ] Inference Engine yanıt üretebiliyor
3. [ ] Orchestrator tüm bileşenleri birleştiriyor
4. [ ] CLI interface çalışıyor
5. [ ] Router → Adapter → Response akışı çalışıyor
6. [ ] Hafıza entegrasyonu aktif
7. [ ] E2E testler %80+ başarılı
8. [ ] Logging sistemi çalışıyor

---

## ⏭️ Sonraki Faz

Faz 5 tamamlandıktan sonra → **FAZ-6-YASAM-DONGUSU.md** dosyasına geç.

---

## 🐛 Olası Sorunlar ve Çözümleri

### Adapter Değiştirme Yavaş
**Çözüm:** Cache mekanizmasını aktif et, sık kullanılan adapter'ları önbellekte tut

### Memory Overflow
**Çözüm:** Generation config'de max_tokens düşür, batch size=1 kullan

### Intent Yanlış Tahmin
**Çözüm:** /adapter komutu ile manuel override yap, router eğitim verisini güncelle

---

## 📊 Zaman Takibi

| Görev | Başlangıç | Bitiş | Süre |
|-------|-----------|-------|------|
| 5.1 LoRA Manager | | | |
| 5.2 Inference Engine | | | |
| 5.3 Orchestrator | | | |
| 5.4 CLI Interface | | | |
| 5.5 E2E Testler | | | |
| 5.6 Logging | | | |
| **TOPLAM** | | | |

---

*Bu faz tamamlandığında, "✅ FAZ 5 TAMAMLANDI" olarak işaretle.*
