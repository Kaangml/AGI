"""
EVO-TR: Memory Module Unit Tests

Hafıza sistemi testleri.
"""

import pytest
import sys
import os
import shutil
from pathlib import Path

# Proje root'unu path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.chromadb_handler import MemoryHandler
from src.memory.context_buffer import ContextBuffer, Message
from src.memory.memory_manager import MemoryManager


# Test için geçici dizin
TEST_DB_PATH = "./data/chromadb/pytest_test"


def cleanup_test_db():
    """Test DB'yi temizle."""
    import time
    if Path(TEST_DB_PATH).exists():
        try:
            shutil.rmtree(TEST_DB_PATH)
        except:
            time.sleep(0.5)
            shutil.rmtree(TEST_DB_PATH, ignore_errors=True)


class TestContextBuffer:
    """ContextBuffer testleri."""
    
    def test_add_messages(self):
        """Mesaj ekleme testi."""
        buffer = ContextBuffer(max_messages=10, max_tokens=500)
        
        buffer.add_user_message("Merhaba!")
        buffer.add_assistant_message("Merhaba! Nasılsın?")
        
        assert buffer.message_count == 2
        assert buffer.get_last_user_message().content == "Merhaba!"
        assert buffer.get_last_assistant_message().content == "Merhaba! Nasılsın?"
    
    def test_message_limit(self):
        """Mesaj sayısı limiti testi."""
        buffer = ContextBuffer(max_messages=3, max_tokens=10000)
        
        for i in range(5):
            buffer.add_user_message(f"Mesaj {i}")
        
        assert buffer.message_count == 3
        assert "Mesaj 2" in buffer.get_messages()[0].content
    
    def test_token_limit(self):
        """Token limiti testi."""
        buffer = ContextBuffer(max_messages=100, max_tokens=50)
        
        buffer.add_user_message("A" * 100)  # ~25 token
        buffer.add_user_message("B" * 100)  # ~25 token
        buffer.add_user_message("C" * 100)  # ~25 token
        
        # Token limiti aşıldığında eski mesajlar silinmeli
        assert buffer.message_count < 3
    
    def test_chat_history_format(self):
        """Chat history format testi."""
        buffer = ContextBuffer(
            system_prompt="Sen bir asistansın."
        )
        
        buffer.add_user_message("Test")
        buffer.add_assistant_message("Yanıt")
        
        history = buffer.get_chat_history(include_system=True)
        
        assert len(history) == 3
        assert history[0]["role"] == "system"
        assert history[1]["role"] == "user"
        assert history[2]["role"] == "assistant"
    
    def test_conversation_pairs(self):
        """Konuşma çiftleri testi."""
        buffer = ContextBuffer()
        
        buffer.add_user_message("Soru 1")
        buffer.add_assistant_message("Cevap 1")
        buffer.add_user_message("Soru 2")
        buffer.add_assistant_message("Cevap 2")
        
        pairs = buffer.get_conversation_pairs()
        
        assert len(pairs) == 2
        assert pairs[0][0].content == "Soru 1"
        assert pairs[0][1].content == "Cevap 1"
    
    def test_clear(self):
        """Temizleme testi."""
        buffer = ContextBuffer()
        buffer.add_user_message("Test")
        buffer.clear()
        
        assert buffer.message_count == 0
    
    def test_intent_metadata(self):
        """Intent ve metadata testi."""
        buffer = ContextBuffer()
        
        buffer.add_user_message(
            "Python kodu yaz",
            intent="code_python",
            metadata={"topic": "programming"}
        )
        
        msg = buffer.get_last_user_message()
        assert msg.intent == "code_python"
        assert msg.metadata["topic"] == "programming"


class TestMemoryHandler:
    """MemoryHandler (ChromaDB) testleri."""
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Her test öncesi/sonrası temizlik."""
        import time
        import uuid
        
        # Her test için benzersiz path kullan
        self.test_path = f"./data/chromadb/pytest_{uuid.uuid4().hex[:8]}"
        
        yield
        
        # Test sonrası temizlik
        time.sleep(0.1)
        if Path(self.test_path).exists():
            shutil.rmtree(self.test_path, ignore_errors=True)
    
    def test_initialization(self):
        """Başlatma testi."""
        handler = MemoryHandler(
            persist_path=self.test_path,
            collection_name="test_init"
        )
        
        assert handler.collection.count() == 0
    
    def test_add_memory(self):
        """Hafıza ekleme testi."""
        handler = MemoryHandler(
            persist_path=self.test_path,
            collection_name="test_add"
        )
        
        doc_id = handler.add_memory("Test metin", memory_type="test")
        
        assert doc_id is not None
        assert handler.collection.count() == 1
    
    def test_add_conversation(self):
        """Konuşma ekleme testi."""
        handler = MemoryHandler(
            persist_path=self.test_path,
            collection_name="test_conv"
        )
        
        doc_id = handler.add_conversation(
            user_message="Merhaba",
            assistant_response="Selam!",
            intent="general_chat"
        )
        
        assert doc_id is not None
        
        # Metadata kontrolü
        results = handler.search("Merhaba", top_k=1)
        assert len(results) == 1
        assert results[0]["metadata"]["intent"] == "general_chat"
    
    def test_search(self):
        """Arama testi."""
        handler = MemoryHandler(
            persist_path=self.test_path,
            collection_name="test_search"
        )
        
        handler.add_memory("Python programlama dili", memory_type="fact")
        handler.add_memory("Türk kahvesi tarifi", memory_type="fact")
        handler.add_memory("JavaScript web geliştirme", memory_type="fact")
        
        results = handler.search("Python kod", top_k=2)
        
        assert len(results) >= 1
        assert "Python" in results[0]["text"]
    
    def test_search_by_type(self):
        """Tip bazlı arama testi."""
        handler = MemoryHandler(
            persist_path=self.test_path,
            collection_name="test_type"
        )
        
        handler.add_memory("Fakt 1", memory_type="fact")
        handler.add_memory("Tercih 1", memory_type="preference")
        
        fact_results = handler.search("", top_k=10, memory_type="fact")
        pref_results = handler.search("", top_k=10, memory_type="preference")
        
        # Her tipten sadece 1 olmalı
        fact_count = len([r for r in fact_results if r["metadata"]["type"] == "fact"])
        pref_count = len([r for r in pref_results if r["metadata"]["type"] == "preference"])
        
        assert fact_count == 1
        assert pref_count == 1
    
    def test_delete(self):
        """Silme testi."""
        handler = MemoryHandler(
            persist_path=self.test_path,
            collection_name="test_delete"
        )
        
        doc_id = handler.add_memory("Silinecek")
        assert handler.collection.count() == 1
        
        handler.delete(doc_id)
        assert handler.collection.count() == 0
    
    def test_clear_all(self):
        """Tümünü silme testi."""
        handler = MemoryHandler(
            persist_path=self.test_path,
            collection_name="test_clear"
        )
        
        handler.add_memory("Belge 1")
        handler.add_memory("Belge 2")
        handler.add_memory("Belge 3")
        
        count = handler.clear_all()
        
        assert count == 3
        assert handler.collection.count() == 0
    
    def test_get_relevant_context(self):
        """RAG context testi."""
        handler = MemoryHandler(
            persist_path=self.test_path,
            collection_name="test_context"
        )
        
        handler.add_conversation(
            user_message="Python'da liste sıralama",
            assistant_response="sorted() kullanabilirsiniz"
        )
        
        context = handler.get_relevant_context("liste sırala")
        
        assert "Hafıza" in context
        assert "sorted" in context
    
    def test_stats(self):
        """İstatistik testi."""
        handler = MemoryHandler(
            persist_path=self.test_path,
            collection_name="test_stats"
        )
        
        handler.add_memory("Fakt", memory_type="fact")
        handler.add_memory("Konuşma", memory_type="conversation")
        
        stats = handler.get_stats()
        
        assert stats["total_documents"] == 2
        assert stats["embedding_dim"] == 384
        assert "type_distribution" in stats


class TestMemoryManager:
    """MemoryManager (Unified) testleri."""
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Her test için benzersiz path."""
        import uuid
        self.test_path = f"./data/chromadb/pytest_{uuid.uuid4().hex[:8]}"
        
        yield
        
        import time
        time.sleep(0.1)
        if Path(self.test_path).exists():
            shutil.rmtree(self.test_path, ignore_errors=True)
    
    def test_initialization(self):
        """Başlatma testi."""
        manager = MemoryManager(
            persist_path=self.test_path,
            collection_name="test_init",
            system_prompt="Test prompt"
        )
        
        assert manager.short_term.system_prompt == "Test prompt"
        assert manager.auto_save == True
    
    def test_conversation_flow(self):
        """Konuşma akışı testi."""
        manager = MemoryManager(
            persist_path=self.test_path,
            collection_name="test_flow"
        )
        
        manager.add_user_message("Merhaba", intent="general_chat")
        manager.add_assistant_message("Selam!")
        
        # Kısa süreli hafızada olmalı
        assert manager.short_term.message_count == 2
        
        # Uzun süreli hafızaya kaydedilmeli (auto_save=True)
        stats = manager.get_stats()
        assert stats["long_term"]["total_documents"] == 1
    
    def test_auto_save_disabled(self):
        """Auto-save kapalı testi."""
        manager = MemoryManager(
            persist_path=self.test_path,
            collection_name="test_no_save",
            auto_save=False
        )
        
        manager.add_user_message("Test")
        manager.add_assistant_message("Yanıt")
        
        stats = manager.get_stats()
        assert stats["long_term"]["total_documents"] == 0
    
    def test_augmented_context(self):
        """RAG context testi."""
        manager = MemoryManager(
            persist_path=self.test_path,
            collection_name="test_aug"
        )
        
        manager.add_user_message("Benim adım Kaan", intent="general_chat")
        manager.add_assistant_message("Merhaba Kaan!")
        
        context = manager.get_augmented_context("adım ne")
        
        assert "Kaan" in context
    
    def test_add_fact(self):
        """Gerçek ekleme testi."""
        manager = MemoryManager(
            persist_path=self.test_path,
            collection_name="test_fact"
        )
        
        doc_id = manager.add_fact("Python 1991'de oluşturuldu", topic="programming")
        
        assert doc_id is not None
        
        results = manager.search_memory("Python ne zaman")
        assert len(results) >= 1
    
    def test_clear_short_term(self):
        """Kısa süreli temizleme testi."""
        manager = MemoryManager(
            persist_path=self.test_path,
            collection_name="test_clear_st"
        )
        
        manager.add_user_message("Test")
        manager.add_assistant_message("Yanıt")
        manager.clear_short_term()
        
        assert manager.short_term.message_count == 0
        # Uzun süreli hala durmalı
        assert manager.get_stats()["long_term"]["total_documents"] == 1
    
    def test_get_chat_messages(self):
        """Chat messages format testi."""
        manager = MemoryManager(
            persist_path=self.test_path,
            collection_name="test_chat",
            system_prompt="System"
        )
        
        manager.add_user_message("User msg")
        manager.add_assistant_message("Assistant msg")
        
        messages = manager.get_chat_messages()
        
        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"


class TestSemanticSimilarity:
    """Semantik benzerlik testleri."""
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        import uuid
        self.test_path = f"./data/chromadb/pytest_{uuid.uuid4().hex[:8]}"
        yield
        import time
        time.sleep(0.1)
        if Path(self.test_path).exists():
            shutil.rmtree(self.test_path, ignore_errors=True)
    
    def test_turkish_similarity(self):
        """Türkçe semantik benzerlik testi."""
        handler = MemoryHandler(
            persist_path=self.test_path,
            collection_name="test_tr_sim"
        )
        
        handler.add_memory("Merhaba, nasılsın?")
        handler.add_memory("Python programlama dili")
        handler.add_memory("Türk kahvesi tarifi")
        
        # "Selam" merhaba'ya benzer olmalı
        results = handler.search("Selam, ne haber?", top_k=3)
        
        assert results[0]["text"] == "Merhaba, nasılsın?"
        assert results[0]["similarity"] > 0.5
    
    def test_code_query_similarity(self):
        """Kod sorgusu benzerlik testi."""
        handler = MemoryHandler(
            persist_path=self.test_path,
            collection_name="test_code_sim"
        )
        
        handler.add_memory("Python'da for döngüsü nasıl kullanılır")
        handler.add_memory("JavaScript array metodları")
        handler.add_memory("Türk mutfağı yemekleri")
        
        results = handler.search("Python loop", top_k=3)
        
        # Python ile ilgili sonuç üstte olmalı
        assert "Python" in results[0]["text"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
