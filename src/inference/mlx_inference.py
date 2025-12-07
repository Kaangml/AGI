"""
EVO-TR: MLX Inference Engine

MLX-LM ile text generation yönetimi.
"""

from typing import Dict, List, Optional, Any, Generator
from dataclasses import dataclass
import time
from mlx_lm import generate, stream_generate


@dataclass
class GenerationConfig:
    """Generation parametreleri."""
    max_tokens: int = 512


@dataclass
class GenerationResult:
    """Generation sonucu."""
    text: str
    tokens_generated: int
    generation_time: float
    tokens_per_second: float
    prompt_tokens: int


class MLXInference:
    """
    MLX tabanlı inference engine.
    
    Özellikler:
    - Chat format desteği
    - Configurable generation parametreleri
    - Performance metrikleri
    - System prompt yönetimi
    """
    
    # Intent'e göre system prompt'lar
    SYSTEM_PROMPTS = {
        "general_chat": """Sen EVO-TR, dostça ve yardımsever bir Türkçe asistansın. 
Kullanıcıyla samimi ama saygılı bir şekilde iletişim kur. 
Kısa ve öz yanıtlar ver.""",
        
        "turkish_culture": """Sen EVO-TR, Türk kültürü ve dili konusunda uzman bir asistansın.
Türkçe deyimler, atasözleri, gelenekler ve kültürel konularda detaylı bilgi ver.
Türkçe'nin inceliklerini açıkla.""",
        
        "code_python": """Sen EVO-TR, deneyimli bir Python geliştiricisisin.
Temiz, okunabilir ve iyi belgelenmiş kod yaz.
Kodları Türkçe açıklamalarla destekle.
Best practice'leri takip et.""",
        
        "code_debug": """Sen EVO-TR, hata ayıklama uzmanı bir Python geliştiricisisin.
Kodlardaki hataları tespit et ve düzelt.
Hatanın nedenini açıkla ve çözümü göster.
Türkçe açıklamalar kullan.""",
        
        "code_explain": """Sen EVO-TR, kod açıklama uzmanı bir Python geliştiricisisin.
Kodları satır satır veya blok blok açıkla.
Karmaşık kavramları basit Türkçe ile anlat.
Örneklerle destekle.""",
        
        "code_math": """Sen EVO-TR, matematik konusunda uzman bir asistansın.
Matematik problemlerini adım adım çöz.
Her adımı Türkçe açıkla.
Formülleri ve hesaplamaları göster.
Cebir, geometri, istatistik ve sözel problemlerde yardımcı ol.""",
        
        "science": """Sen EVO-TR, fizik, kimya ve biyoloji konularında uzman bir bilim asistanısın.
Bilimsel kavramları açık ve anlaşılır şekilde açıkla.
Örnekler ve benzetmeler kullan.
Formülleri ve denklemleri göster.
Hem Türkçe hem İngilizce bilim terimlerini kullan.""",
        
        "history": """Sen EVO-TR, Türk tarihi ve dünya tarihi konusunda uzman bir tarihçisin.
Tarihi olayları, dönemleri ve önemli kişileri detaylı şekilde anlat.
Kronolojik sıralama yap.
Neden-sonuç ilişkilerini açıkla.
Osmanlı, Cumhuriyet, Selçuklu ve Türk tarihi konularında özellikle bilgilisin.
Atatürk, Kurtuluş Savaşı ve Türk devrimleri hakkında kapsamlı bilgi ver.""",
        
        "memory_recall": """Sen EVO-TR, iyi bir hafızaya sahip bir asistansın.
Kullanıcı hakkında öğrendiğin bilgileri hatırla ve kullan.
Geçmiş konuşmalara referans ver.""",
        
        "general_knowledge": """Sen EVO-TR, geniş bilgi birikimine sahip bir asistansın.
Genel kültür sorularına doğru ve güncel yanıtlar ver.
Bilmediğin konularda dürüst ol."""
    }
    
    def __init__(
        self,
        default_config: Optional[GenerationConfig] = None
    ):
        """
        MLXInference başlat.
        
        Args:
            default_config: Varsayılan generation config
        """
        self.default_config = default_config or GenerationConfig()
        self._generation_count = 0
        self._total_tokens = 0
        self._total_time = 0.0
        
        print("✅ MLXInference hazır")
    
    def get_system_prompt(self, intent: str) -> str:
        """Intent için system prompt döndür."""
        return self.SYSTEM_PROMPTS.get(intent, self.SYSTEM_PROMPTS["general_chat"])
    
    def build_chat_prompt(
        self,
        tokenizer: Any,
        user_message: str,
        intent: str = "general_chat",
        chat_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[str] = None,
        custom_system_prompt: Optional[str] = None
    ) -> str:
        """
        Chat formatında prompt oluştur.
        
        Args:
            tokenizer: Tokenizer
            user_message: Kullanıcı mesajı
            intent: Intent kategorisi
            chat_history: Önceki mesajlar [{"role": "user/assistant", "content": "..."}]
            context: RAG context (ek bilgi)
            custom_system_prompt: Özel system prompt
        
        Returns:
            Formatlanmış prompt string
        """
        # System prompt
        system_prompt = custom_system_prompt or self.get_system_prompt(intent)
        
        # Context varsa system prompt'a ekle
        if context:
            system_prompt += f"\n\n📚 İlgili Bilgiler:\n{context}"
        
        # Mesajları hazırla
        messages = [{"role": "system", "content": system_prompt}]
        
        # Chat history ekle
        if chat_history:
            messages.extend(chat_history)
        
        # User mesajını ekle
        messages.append({"role": "user", "content": user_message})
        
        # Tokenizer ile format
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        return prompt
    
    def generate(
        self,
        model: Any,
        tokenizer: Any,
        prompt: str,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """
        Text generation yap.
        
        Args:
            model: MLX model
            tokenizer: Tokenizer
            prompt: Input prompt
            config: Generation config (optional)
        
        Returns:
            GenerationResult
        """
        cfg = config or self.default_config
        
        # Prompt token sayısı (yaklaşık)
        prompt_tokens = len(prompt) // 4
        
        start_time = time.time()
        
        # Generate
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=cfg.max_tokens,
            verbose=False
        )
        
        generation_time = time.time() - start_time
        
        # Token sayısı (yaklaşık)
        tokens_generated = len(response) // 4
        tokens_per_second = tokens_generated / generation_time if generation_time > 0 else 0
        
        # İstatistikleri güncelle
        self._generation_count += 1
        self._total_tokens += tokens_generated
        self._total_time += generation_time
        
        return GenerationResult(
            text=response,
            tokens_generated=tokens_generated,
            generation_time=generation_time,
            tokens_per_second=tokens_per_second,
            prompt_tokens=prompt_tokens
        )
    
    def generate_response(
        self,
        model: Any,
        tokenizer: Any,
        user_message: str,
        intent: str = "general_chat",
        chat_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> GenerationResult:
        """
        Tam yanıt oluştur (prompt building + generation).
        
        Args:
            model: MLX model
            tokenizer: Tokenizer
            user_message: Kullanıcı mesajı
            intent: Intent kategorisi
            chat_history: Önceki mesajlar
            context: RAG context
            config: Generation config
        
        Returns:
            GenerationResult
        """
        # Prompt oluştur
        prompt = self.build_chat_prompt(
            tokenizer=tokenizer,
            user_message=user_message,
            intent=intent,
            chat_history=chat_history,
            context=context
        )
        
        # Generate
        return self.generate(model, tokenizer, prompt, config)
    
    def generate_stream(
        self,
        model: Any,
        tokenizer: Any,
        prompt: str,
        config: Optional[GenerationConfig] = None
    ) -> Generator[str, None, None]:
        """
        Streaming text generation.
        
        Args:
            model: MLX model
            tokenizer: Tokenizer
            prompt: Input prompt
            config: Generation config (optional)
        
        Yields:
            Token strings one by one
        """
        cfg = config or self.default_config
        
        for response in stream_generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=cfg.max_tokens
        ):
            yield response.text
    
    def generate_response_stream(
        self,
        model: Any,
        tokenizer: Any,
        user_message: str,
        intent: str = "general_chat",
        chat_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[str] = None,
        config: Optional[GenerationConfig] = None
    ) -> Generator[str, None, None]:
        """
        Streaming yanıt oluştur (prompt building + streaming generation).
        
        Args:
            model: MLX model
            tokenizer: Tokenizer
            user_message: Kullanıcı mesajı
            intent: Intent kategorisi
            chat_history: Önceki mesajlar
            context: RAG context
            config: Generation config
        
        Yields:
            Token strings one by one
        """
        # Prompt oluştur
        prompt = self.build_chat_prompt(
            tokenizer=tokenizer,
            user_message=user_message,
            intent=intent,
            chat_history=chat_history,
            context=context
        )
        
        # Stream generate
        yield from self.generate_stream(model, tokenizer, prompt, config)
    
    def get_stats(self) -> Dict[str, Any]:
        """Inference istatistikleri."""
        avg_tokens_per_sec = self._total_tokens / self._total_time if self._total_time > 0 else 0
        
        return {
            "total_generations": self._generation_count,
            "total_tokens": self._total_tokens,
            "total_time": round(self._total_time, 2),
            "avg_tokens_per_second": round(avg_tokens_per_sec, 1)
        }
    
    def reset_stats(self) -> None:
        """İstatistikleri sıfırla."""
        self._generation_count = 0
        self._total_tokens = 0
        self._total_time = 0.0


# Test
if __name__ == "__main__":
    print("🧪 MLXInference Testi\n")
    
    from mlx_lm import load
    
    inference = MLXInference()
    
    # Model yükle
    print("📥 Model yükleniyor...")
    model, tokenizer = load("./models/base/qwen-2.5-3b-instruct")
    print("✅ Model hazır!\n")
    
    # Test 1: Genel sohbet
    print("=" * 50)
    print("Test 1: Genel Sohbet")
    print("=" * 50)
    
    result = inference.generate_response(
        model=model,
        tokenizer=tokenizer,
        user_message="Merhaba! Bugün nasılsın?",
        intent="general_chat"
    )
    
    print(f"Yanıt: {result.text}")
    print(f"Tokens: {result.tokens_generated}, Time: {result.generation_time:.2f}s")
    print(f"Speed: {result.tokens_per_second:.1f} tok/s")
    
    # Test 2: Kod yazma
    print("\n" + "=" * 50)
    print("Test 2: Python Kodu")
    print("=" * 50)
    
    result = inference.generate_response(
        model=model,
        tokenizer=tokenizer,
        user_message="Fibonacci dizisinin ilk 10 elemanını yazdıran Python kodu yaz.",
        intent="code_python"
    )
    
    print(f"Yanıt: {result.text}")
    print(f"Tokens: {result.tokens_generated}, Time: {result.generation_time:.2f}s")
    
    # Test 3: Context ile
    print("\n" + "=" * 50)
    print("Test 3: RAG Context ile")
    print("=" * 50)
    
    context = "Kullanıcının adı Kaan. Python'u çok sever."
    
    result = inference.generate_response(
        model=model,
        tokenizer=tokenizer,
        user_message="Benim hakkımda ne biliyorsun?",
        intent="memory_recall",
        context=context
    )
    
    print(f"Yanıt: {result.text}")
    
    # İstatistikler
    print("\n" + "=" * 50)
    print("📊 Inference İstatistikleri")
    print("=" * 50)
    stats = inference.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    print("\n✅ Test tamamlandı!")
