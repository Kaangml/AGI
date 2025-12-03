"""
EVO-TR: Ana Orkestrasyon Modülü

Tüm bileşenleri birleştiren ana sistem.
Router + LoRA Manager + Memory + Inference
"""

import sys
sys.path.insert(0, ".")

from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime
import json

from src.router.classifier import IntentClassifier
from src.experts.lora_manager import LoRAManager
from src.memory.memory_manager import MemoryManager
from src.inference.mlx_inference import MLXInference, GenerationConfig, GenerationResult


@dataclass
class ConversationTurn:
    """Tek bir konuşma dönüşü."""
    user_message: str
    assistant_response: str
    intent: str
    confidence: float
    adapter_used: Optional[str]
    generation_time: float
    tokens_generated: int
    timestamp: datetime


class EvoTR:
    """
    EVO-TR Ana Sistem.
    
    Akış:
    1. User Input alınır
    2. Router -> Intent classification
    3. LoRA Manager -> Uygun adapter yüklenir
    4. Memory -> İlgili bağlam alınır
    5. Inference -> Yanıt üretilir
    6. Memory -> Konuşma kaydedilir
    
    Özellikler:
    - Otomatik adapter seçimi
    - RAG ile zenginleştirilmiş yanıtlar
    - Konuşma geçmişi takibi
    - Performance metrikleri
    """
    
    def __init__(
        self,
        base_model_path: str = "./models/base/qwen-2.5-3b-instruct",
        adapters_dir: str = "./adapters",
        router_model_path: str = "./models/router/sentence_transformer",
        intents_path: str = "./data/intents",
        memory_path: str = "./data/chromadb/evo_main",
        memory_collection: str = "conversations",
        max_context_messages: int = 10,
        max_context_tokens: int = 1500,
        use_rag: bool = True,
        auto_adapter: bool = True,
        verbose: bool = True
    ):
        """
        EVO-TR başlat.
        
        Args:
            base_model_path: Base model dizini
            adapters_dir: Adapter'ların dizini
            router_model_path: Router model dizini
            intents_path: Intent dataset dizini
            memory_path: ChromaDB dizini
            memory_collection: Memory collection adı
            max_context_messages: Maksimum kısa süreli mesaj
            max_context_tokens: Maksimum kısa süreli token
            use_rag: RAG kullanılsın mı
            auto_adapter: Otomatik adapter seçimi
            verbose: Detaylı output
        """
        self.verbose = verbose
        self.use_rag = use_rag
        self.auto_adapter = auto_adapter
        
        self._log("🚀 EVO-TR başlatılıyor...")
        
        # 1. Router
        self._log("📡 Router yükleniyor...")
        self.router = IntentClassifier(
            model_path=router_model_path,
            dataset_path=f"{intents_path}/intent_dataset.json",
            mapping_path="./configs/intent_mapping.json"
        )
        
        # 2. LoRA Manager
        self._log("🔌 LoRA Manager yükleniyor...")
        self.lora_manager = LoRAManager(
            base_model_path=base_model_path,
            adapters_dir=adapters_dir,
            cache_adapters=True
        )
        
        # 3. Memory Manager
        self._log("🧠 Memory Manager yükleniyor...")
        self.memory = MemoryManager(
            persist_path=memory_path,
            collection_name=memory_collection,
            max_context_messages=max_context_messages,
            max_context_tokens=max_context_tokens,
            system_prompt="Sen EVO-TR, çok yetenekli bir Türkçe AI asistansın.",
            auto_save=True
        )
        
        # 4. Inference Engine
        self._log("⚡ Inference Engine yükleniyor...")
        self.inference = MLXInference()
        
        # State
        self._conversation_history: List[ConversationTurn] = []
        self._current_intent: Optional[str] = None
        
        self._log("✅ EVO-TR hazır!\n")
    
    def _log(self, message: str) -> None:
        """Verbose logging."""
        if self.verbose:
            print(message)
    
    def chat(
        self, 
        message: str,
        force_intent: Optional[str] = None,
        force_adapter: Optional[str] = None,
        include_rag: Optional[bool] = None
    ) -> str:
        """
        Ana chat fonksiyonu.
        
        Args:
            message: Kullanıcı mesajı
            force_intent: Intent'i zorla (otomatik yerine)
            force_adapter: Adapter'ı zorla
            include_rag: RAG kullanımını zorla
        
        Returns:
            Asistan yanıtı
        """
        start_time = datetime.now()
        
        # 1. Intent Classification
        if force_intent:
            intent = force_intent
            confidence = 1.0
        else:
            classification = self.router.predict(message)
            intent = classification["intent"]
            confidence = classification["confidence"]
        
        self._current_intent = intent
        self._log(f"🎯 Intent: {intent} ({confidence:.0%})")
        
        # 2. Adapter Seçimi
        if force_adapter:
            adapter_name = force_adapter
            if adapter_name in self.lora_manager.list_adapters():
                model, tokenizer = self.lora_manager.load_adapter(adapter_name)
            else:
                model, tokenizer = self.lora_manager.load_base_model()
        elif self.auto_adapter:
            model, tokenizer = self.lora_manager.load_for_intent(intent)
            adapter_name = self.lora_manager.get_current_adapter()
        else:
            model, tokenizer = self.lora_manager.get_model_and_tokenizer()
            adapter_name = self.lora_manager.get_current_adapter()
        
        self._log(f"🔌 Adapter: {adapter_name or 'base_model'}")
        
        # 3. RAG Context
        use_rag = include_rag if include_rag is not None else self.use_rag
        context = None
        
        if use_rag:
            context = self.memory.get_augmented_context(
                query=message,
                long_term_top_k=2
            )
            if context:
                self._log(f"📚 RAG: {len(context)} karakter bağlam bulundu")
        
        # 4. Mesajı hafızaya ekle (user)
        self.memory.add_user_message(message, intent=intent)
        
        # 5. Chat history al
        chat_history = []
        for msg in self.memory.short_term.get_messages()[:-1]:  # Son mesaj hariç
            chat_history.append(msg.to_chat_format())
        
        # 6. Inference
        result = self.inference.generate_response(
            model=model,
            tokenizer=tokenizer,
            user_message=message,
            intent=intent,
            chat_history=chat_history[-6:],  # Son 6 mesaj (3 tur)
            context=context
        )
        
        response = result.text
        
        # 7. Yanıtı hafızaya ekle (assistant)
        self.memory.add_assistant_message(response)
        
        # 8. Konuşma kaydı
        turn = ConversationTurn(
            user_message=message,
            assistant_response=response,
            intent=intent,
            confidence=confidence,
            adapter_used=adapter_name,
            generation_time=result.generation_time,
            tokens_generated=result.tokens_generated,
            timestamp=start_time
        )
        self._conversation_history.append(turn)
        
        self._log(f"⏱️ Generation: {result.generation_time:.2f}s, {result.tokens_generated} tokens\n")
        
        return response
    
    def get_conversation_history(self) -> List[ConversationTurn]:
        """Konuşma geçmişini döndür."""
        return self._conversation_history.copy()
    
    def clear_conversation(self) -> None:
        """Mevcut konuşmayı temizle."""
        self.memory.clear_short_term()
        self._conversation_history.clear()
        self._log("🧹 Konuşma temizlendi")
    
    def get_status(self) -> Dict[str, Any]:
        """Sistem durumu."""
        return {
            "current_intent": self._current_intent,
            "current_adapter": self.lora_manager.get_current_adapter(),
            "conversation_turns": len(self._conversation_history),
            "memory_stats": self.memory.get_stats(),
            "inference_stats": self.inference.get_stats(),
            "available_adapters": list(self.lora_manager.list_adapters().keys()),
            "use_rag": self.use_rag,
            "auto_adapter": self.auto_adapter
        }
    
    def search_memory(self, query: str, top_k: int = 5) -> List[Dict]:
        """Hafızada ara."""
        return self.memory.search_memory(query, top_k=top_k)
    
    def add_fact(self, fact: str, topic: Optional[str] = None) -> str:
        """Gerçek/bilgi ekle."""
        return self.memory.add_fact(fact, topic=topic)


# Test
if __name__ == "__main__":
    print("🧪 EVO-TR Orchestrator Testi\n")
    print("=" * 60)
    
    # EVO-TR başlat
    evo = EvoTR(verbose=True)
    
    # Status
    print("\n📊 Sistem Durumu:")
    status = evo.get_status()
    print(f"  Adapter'lar: {status['available_adapters']}")
    print(f"  RAG: {status['use_rag']}")
    print(f"  Auto-adapter: {status['auto_adapter']}")
    
    # Test konuşmaları
    test_messages = [
        "Merhaba! Nasılsın?",
        "Python'da liste nasıl sıralarım?",
        "Türk kahvesi nasıl yapılır?",
        "Az önce sorduğum soruyu hatırlıyor musun?"
    ]
    
    print("\n" + "=" * 60)
    print("💬 Test Konuşmaları")
    print("=" * 60)
    
    for msg in test_messages:
        print(f"\n👤 User: {msg}")
        response = evo.chat(msg)
        print(f"🤖 EVO-TR: {response[:300]}{'...' if len(response) > 300 else ''}")
        print("-" * 40)
    
    # Final durum
    print("\n" + "=" * 60)
    print("📊 Final Durum")
    print("=" * 60)
    
    status = evo.get_status()
    print(f"  Konuşma turları: {status['conversation_turns']}")
    print(f"  Inference stats: {status['inference_stats']}")
    
    print("\n✅ Test tamamlandı!")
