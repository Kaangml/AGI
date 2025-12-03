"""
EVO-TR: Unified Memory Manager

Kısa ve uzun süreli hafızayı birleştiren ana hafıza yöneticisi.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from .chromadb_handler import MemoryHandler
from .context_buffer import ContextBuffer, Message


class MemoryManager:
    """
    Birleşik hafıza yönetimi.
    
    İki katmanlı hafıza sistemi:
    1. Kısa süreli (ContextBuffer): Son N mesaj, anlık bağlam
    2. Uzun süreli (ChromaDB): Kalıcı hafıza, semantik arama
    
    Özellikler:
    - Otomatik hafıza senkronizasyonu
    - RAG için bağlam oluşturma
    - Intent-bazlı hafıza filtreleme
    """
    
    def __init__(
        self,
        persist_path: str = "./data/chromadb",
        collection_name: str = "evo_memory",
        max_context_messages: int = 10,
        max_context_tokens: int = 1500,
        system_prompt: Optional[str] = None,
        auto_save: bool = True
    ):
        """
        MemoryManager başlat.
        
        Args:
            persist_path: ChromaDB veritabanı yolu
            collection_name: Collection adı
            max_context_messages: Maksimum kısa süreli mesaj sayısı
            max_context_tokens: Maksimum kısa süreli token
            system_prompt: Sabit system prompt
            auto_save: Her konuşmayı otomatik uzun süreli hafızaya kaydet
        """
        # Uzun süreli hafıza
        self.long_term = MemoryHandler(
            persist_path=persist_path,
            collection_name=collection_name
        )
        
        # Kısa süreli hafıza
        self.short_term = ContextBuffer(
            max_messages=max_context_messages,
            max_tokens=max_context_tokens,
            system_prompt=system_prompt
        )
        
        self.auto_save = auto_save
        self._pending_user_message: Optional[Message] = None
        
        print(f"✅ MemoryManager hazır | Auto-save: {auto_save}")
    
    def add_user_message(
        self, 
        content: str, 
        intent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Kullanıcı mesajı ekle.
        
        Args:
            content: Mesaj içeriği
            intent: Tespit edilen intent
            metadata: Ek bilgiler
        """
        self.short_term.add_user_message(
            content=content,
            intent=intent,
            metadata=metadata
        )
        
        # Pending olarak sakla (assistant yanıtı gelince birlikte kaydedilecek)
        if self.auto_save:
            self._pending_user_message = self.short_term.get_last_user_message()
    
    def add_assistant_message(
        self, 
        content: str,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Asistan mesajı ekle.
        
        Args:
            content: Mesaj içeriği
            metadata: Ek bilgiler
        
        Returns:
            Uzun süreli hafıza ID'si (auto_save=True ise)
        """
        self.short_term.add_assistant_message(
            content=content,
            metadata=metadata
        )
        
        # Uzun süreli hafızaya kaydet
        if self.auto_save and self._pending_user_message:
            doc_id = self.long_term.add_conversation(
                user_message=self._pending_user_message.content,
                assistant_response=content,
                intent=self._pending_user_message.intent,
                topic=self._pending_user_message.metadata.get("topic")
            )
            self._pending_user_message = None
            return doc_id
        
        return None
    
    def get_augmented_context(
        self, 
        query: str,
        include_long_term: bool = True,
        long_term_top_k: int = 2,
        min_similarity: float = 0.4
    ) -> str:
        """
        RAG için zenginleştirilmiş bağlam oluştur.
        
        Args:
            query: Kullanıcı sorgusu
            include_long_term: Uzun süreli hafıza dahil edilsin mi
            long_term_top_k: Kaç uzun süreli hafıza döndürülsün
            min_similarity: Minimum benzerlik skoru
        
        Returns:
            Formatlanmış bağlam metni
        """
        context_parts = []
        
        # 1. Uzun süreli hafızadan ilgili bilgiler
        if include_long_term:
            long_term_context = self.long_term.get_relevant_context(
                query=query,
                top_k=long_term_top_k
            )
            if long_term_context:
                context_parts.append(long_term_context)
        
        # 2. Kısa süreli hafızadan son konuşmalar
        recent_pairs = self.short_term.get_conversation_pairs()[-2:]  # Son 2 çift
        
        if recent_pairs:
            recent_context = "💬 Son Konuşmalar:\n"
            for user_msg, asst_msg in recent_pairs:
                recent_context += f"Kullanıcı: {user_msg.content[:100]}...\n" if len(user_msg.content) > 100 else f"Kullanıcı: {user_msg.content}\n"
                recent_context += f"Asistan: {asst_msg.content[:100]}...\n\n" if len(asst_msg.content) > 100 else f"Asistan: {asst_msg.content}\n\n"
            context_parts.append(recent_context.strip())
        
        return "\n\n".join(context_parts) if context_parts else ""
    
    def get_chat_messages(self, include_system: bool = True) -> List[Dict]:
        """
        LLM için chat mesajları formatı.
        
        Returns:
            [{"role": "...", "content": "..."}] formatında liste
        """
        return self.short_term.get_chat_history(include_system=include_system)
    
    def search_memory(
        self, 
        query: str, 
        top_k: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Uzun süreli hafızada ara.
        
        Args:
            query: Arama sorgusu
            top_k: Maksimum sonuç sayısı
            memory_type: Hafıza tipi filtresi
        
        Returns:
            Bulunan belgeler
        """
        return self.long_term.search(
            query=query,
            top_k=top_k,
            memory_type=memory_type
        )
    
    def add_fact(self, fact: str, topic: Optional[str] = None) -> str:
        """
        Gerçek/bilgi ekle (konuşma dışı).
        
        Args:
            fact: Kaydedilecek bilgi
            topic: Konu başlığı
        
        Returns:
            Belge ID'si
        """
        return self.long_term.add_memory(
            text=fact,
            metadata={"topic": topic} if topic else None,
            memory_type="fact"
        )
    
    def add_preference(self, preference: str) -> str:
        """
        Kullanıcı tercihi ekle.
        
        Args:
            preference: Tercih açıklaması
        
        Returns:
            Belge ID'si
        """
        return self.long_term.add_memory(
            text=preference,
            memory_type="preference"
        )
    
    def set_system_prompt(self, prompt: str) -> None:
        """System prompt ayarla."""
        self.short_term.set_system_prompt(prompt)
    
    def clear_short_term(self) -> None:
        """Kısa süreli hafızayı temizle (yeni konuşma başlat)."""
        self.short_term.clear()
        self._pending_user_message = None
        print("🧹 Kısa süreli hafıza temizlendi")
    
    def clear_long_term(self) -> int:
        """Uzun süreli hafızayı temizle."""
        count = self.long_term.clear_all()
        print(f"🧹 Uzun süreli hafıza temizlendi ({count} belge)")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Hafıza istatistikleri."""
        long_term_stats = self.long_term.get_stats()
        
        return {
            "short_term": {
                "message_count": self.short_term.message_count,
                "total_tokens": self.short_term.total_tokens,
                "max_messages": self.short_term.max_messages,
                "max_tokens": self.short_term.max_tokens
            },
            "long_term": long_term_stats,
            "auto_save": self.auto_save
        }
    
    def get_status_summary(self) -> str:
        """Durum özeti (debugging için)."""
        stats = self.get_stats()
        
        lines = [
            "🧠 Memory Manager Durumu",
            "",
            "📝 Kısa Süreli Hafıza:",
            f"   Mesaj: {stats['short_term']['message_count']}/{stats['short_term']['max_messages']}",
            f"   Token: ~{stats['short_term']['total_tokens']}/{stats['short_term']['max_tokens']}",
            "",
            "💾 Uzun Süreli Hafıza:",
            f"   Toplam belge: {stats['long_term']['total_documents']}",
            f"   Embedding dim: {stats['long_term']['embedding_dim']}"
        ]
        
        if "type_distribution" in stats["long_term"]:
            dist = stats["long_term"]["type_distribution"]
            lines.append(f"   Dağılım: {dist}")
        
        return "\n".join(lines)


# Test
if __name__ == "__main__":
    print("🧪 MemoryManager Testi\n")
    
    # Manager oluştur
    manager = MemoryManager(
        persist_path="./data/chromadb/test",
        collection_name="test_unified",
        max_context_messages=10,
        max_context_tokens=1000,
        system_prompt="Sen EVO-TR, çok yetenekli bir asistansın.",
        auto_save=True
    )
    
    # Temiz başla
    manager.clear_short_term()
    manager.clear_long_term()
    
    # Konuşma simülasyonu
    print("💬 Konuşma simülasyonu başlıyor...\n")
    
    # Konuşma 1
    manager.add_user_message("Merhaba, benim adım Kaan", intent="general_chat")
    manager.add_assistant_message("Merhaba Kaan! Tanıştığımıza memnun oldum.")
    
    # Konuşma 2
    manager.add_user_message("Python'da liste nasıl sıralarım?", intent="code_python")
    manager.add_assistant_message("sorted() veya list.sort() kullanabilirsin.")
    
    # Konuşma 3
    manager.add_user_message("En sevdiğim renk mavi", intent="general_chat")
    manager.add_assistant_message("Güzel! Mavi huzur verici bir renk.")
    
    # Gerçek ekle
    manager.add_fact("Kaan'ın en sevdiği programlama dili Python.", topic="preferences")
    
    # Durum
    print(manager.get_status_summary())
    
    # RAG context testi
    print("\n📚 RAG Context testi: 'adım neydi'")
    context = manager.get_augmented_context("benim adım neydi")
    print(context)
    
    # Hafıza araması
    print("\n🔍 Hafıza araması: 'Python'")
    results = manager.search_memory("Python", top_k=2)
    for r in results:
        print(f"  [{r['similarity']:.0%}] {r['text'][:80]}...")
    
    # Chat messages
    print("\n💬 Chat Messages (LLM için):")
    for msg in manager.get_chat_messages():
        preview = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
        print(f"  [{msg['role']}] {preview}")
    
    # Temizlik
    manager.clear_long_term()
    print("\n✅ Test tamamlandı!")
