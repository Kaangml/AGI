"""
EVO-TR: LoRA Manager

LoRA adapter yönetimi - yükleme, değiştirme ve caching.
"""

from typing import Dict, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
import time
import mlx.core as mx
from mlx_lm import load


@dataclass
class AdapterInfo:
    """Adapter bilgileri."""
    name: str
    path: str
    intent: str
    description: str
    loaded: bool = False
    load_time: float = 0.0


class LoRAManager:
    """
    LoRA Adapter yönetimi.
    
    Özellikler:
    - Adapter registry (hangi intent -> hangi adapter)
    - Lazy loading (ihtiyaç olunca yükle)
    - Hot-swap (adapter değiştirme)
    - Caching (son kullanılan adapter'ı tut)
    """
    
    # Intent -> Adapter mapping
    ADAPTER_REGISTRY = {
        "general_chat": None,  # Base model kullan
        "turkish_culture": "tr_chat",
        "code_python": "python_coder",
        "code_debug": "python_coder",
        "code_explain": "python_coder",
        "code_math": "math_expert",  # Matematik uzmanı
        "science": "science_expert",  # Bilim uzmanı
        "memory_recall": None,  # Base model kullan
        "general_knowledge": None,  # Base model kullan
    }
    
    def __init__(
        self,
        base_model_path: str = "./models/base/qwen-2.5-3b-instruct",
        adapters_dir: str = "./adapters",
        cache_adapters: bool = True
    ):
        """
        LoRAManager başlat.
        
        Args:
            base_model_path: Base model dizini
            adapters_dir: Adapter'ların bulunduğu dizin
            cache_adapters: Adapter caching aktif mi
        """
        self.base_model_path = Path(base_model_path)
        self.adapters_dir = Path(adapters_dir)
        self.cache_adapters = cache_adapters
        
        # State
        self._model = None
        self._tokenizer = None
        self._current_adapter: Optional[str] = None
        self._adapter_cache: Dict[str, Tuple[Any, Any]] = {}
        
        # Adapter registry
        self._adapters: Dict[str, AdapterInfo] = {}
        self._discover_adapters()
        
        print(f"✅ LoRAManager hazır | Adapters: {list(self._adapters.keys())}")
    
    def _discover_adapters(self) -> None:
        """Mevcut adapter'ları keşfet."""
        if not self.adapters_dir.exists():
            return
        
        adapter_configs = {
            "tr_chat": {
                "intent": "turkish_culture",
                "description": "Türkçe sohbet ve kültür uzmanı"
            },
            "python_coder": {
                "intent": "code_python",
                "description": "Python kod yazma ve debug uzmanı"
            },
            "math_expert": {
                "intent": "code_math",
                "description": "Matematik problemleri çözme uzmanı"
            },
            "science_expert": {
                "intent": "science",
                "description": "Fizik, kimya, biyoloji uzmanı"
            }
        }
        
        for adapter_dir in self.adapters_dir.iterdir():
            if adapter_dir.is_dir():
                adapter_file = adapter_dir / "adapters.safetensors"
                if adapter_file.exists():
                    name = adapter_dir.name
                    config = adapter_configs.get(name, {
                        "intent": "unknown",
                        "description": f"{name} adapter"
                    })
                    
                    self._adapters[name] = AdapterInfo(
                        name=name,
                        path=str(adapter_dir),
                        intent=config["intent"],
                        description=config["description"]
                    )
    
    def get_adapter_for_intent(self, intent: str) -> Optional[str]:
        """
        Intent için uygun adapter adını döndür.
        
        Args:
            intent: Intent kategorisi
        
        Returns:
            Adapter adı veya None (base model için)
        """
        return self.ADAPTER_REGISTRY.get(intent)
    
    def load_base_model(self) -> Tuple[Any, Any]:
        """Base modeli yükle (adapter'sız)."""
        if self._model is not None and self._current_adapter is None:
            return self._model, self._tokenizer
        
        print("📥 Base model yükleniyor...")
        start = time.time()
        
        self._model, self._tokenizer = load(str(self.base_model_path))
        self._current_adapter = None
        
        load_time = time.time() - start
        print(f"✅ Base model hazır ({load_time:.2f}s)")
        
        return self._model, self._tokenizer
    
    def load_adapter(self, adapter_name: str) -> Tuple[Any, Any]:
        """
        Belirli bir adapter'ı yükle.
        
        Args:
            adapter_name: Adapter adı
        
        Returns:
            (model, tokenizer) tuple
        """
        if adapter_name not in self._adapters:
            raise ValueError(f"Adapter bulunamadı: {adapter_name}")
        
        # Zaten yüklü mü?
        if self._current_adapter == adapter_name:
            return self._model, self._tokenizer
        
        # Cache'de var mı?
        if self.cache_adapters and adapter_name in self._adapter_cache:
            print(f"📦 Cache'den yükleniyor: {adapter_name}")
            self._model, self._tokenizer = self._adapter_cache[adapter_name]
            self._current_adapter = adapter_name
            return self._model, self._tokenizer
        
        # Yeni yükle
        adapter_info = self._adapters[adapter_name]
        print(f"📥 Adapter yükleniyor: {adapter_name}")
        start = time.time()
        
        self._model, self._tokenizer = load(
            str(self.base_model_path),
            adapter_path=adapter_info.path
        )
        
        load_time = time.time() - start
        adapter_info.loaded = True
        adapter_info.load_time = load_time
        self._current_adapter = adapter_name
        
        # Cache'e ekle
        if self.cache_adapters:
            self._adapter_cache[adapter_name] = (self._model, self._tokenizer)
        
        print(f"✅ Adapter hazır: {adapter_name} ({load_time:.2f}s)")
        
        return self._model, self._tokenizer
    
    def load_for_intent(self, intent: str) -> Tuple[Any, Any]:
        """
        Intent'e göre uygun model/adapter yükle.
        
        Args:
            intent: Intent kategorisi
        
        Returns:
            (model, tokenizer) tuple
        """
        adapter_name = self.get_adapter_for_intent(intent)
        
        if adapter_name is None:
            return self.load_base_model()
        
        if adapter_name in self._adapters:
            return self.load_adapter(adapter_name)
        
        # Adapter bulunamadı, base model kullan
        print(f"⚠️ Adapter bulunamadı ({adapter_name}), base model kullanılıyor")
        return self.load_base_model()
    
    def get_current_adapter(self) -> Optional[str]:
        """Şu an yüklü adapter adını döndür."""
        return self._current_adapter
    
    def get_model_and_tokenizer(self) -> Tuple[Any, Any]:
        """Şu an yüklü model ve tokenizer'ı döndür."""
        if self._model is None:
            return self.load_base_model()
        return self._model, self._tokenizer
    
    def list_adapters(self) -> Dict[str, AdapterInfo]:
        """Mevcut adapter'ları listele."""
        return self._adapters.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """Manager durumu."""
        return {
            "base_model": str(self.base_model_path),
            "current_adapter": self._current_adapter,
            "available_adapters": list(self._adapters.keys()),
            "cached_adapters": list(self._adapter_cache.keys()),
            "model_loaded": self._model is not None
        }
    
    def clear_cache(self) -> None:
        """Adapter cache'ini temizle."""
        self._adapter_cache.clear()
        print("🧹 Adapter cache temizlendi")


# Test
if __name__ == "__main__":
    print("🧪 LoRAManager Testi\n")
    
    manager = LoRAManager()
    
    # Status
    print("\n📊 Manager Status:")
    status = manager.get_status()
    for k, v in status.items():
        print(f"  {k}: {v}")
    
    # Adapter listesi
    print("\n📦 Mevcut Adapter'lar:")
    for name, info in manager.list_adapters().items():
        print(f"  {name}: {info.description}")
    
    # Intent -> Adapter mapping
    print("\n🔗 Intent -> Adapter Mapping:")
    test_intents = ["general_chat", "turkish_culture", "code_python", "memory_recall"]
    for intent in test_intents:
        adapter = manager.get_adapter_for_intent(intent)
        print(f"  {intent} -> {adapter or 'base_model'}")
    
    # Base model yükle
    print("\n")
    model, tokenizer = manager.load_base_model()
    print(f"Current adapter: {manager.get_current_adapter()}")
    
    # Python adapter yükle
    print("\n")
    model, tokenizer = manager.load_for_intent("code_python")
    print(f"Current adapter: {manager.get_current_adapter()}")
    
    # Tekrar aynı adapter (cache'den)
    print("\n")
    model, tokenizer = manager.load_for_intent("code_debug")
    print(f"Current adapter: {manager.get_current_adapter()}")
    
    print("\n✅ Test tamamlandı!")
