"""
EVO-TR: ChromaDB Handler

Uzun süreli hafıza yönetimi için ChromaDB entegrasyonu.
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
from pathlib import Path


class MemoryHandler:
    """
    ChromaDB tabanlı uzun süreli hafıza yönetimi.
    
    Özellikler:
    - Persistent storage (kalıcı depolama)
    - Semantic search (anlamsal arama)
    - Metadata filtreleme
    - Türkçe/İngilizce destek
    """
    
    def __init__(
        self, 
        persist_path: str = "./data/chromadb",
        collection_name: str = "evo_memory",
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        MemoryHandler başlat.
        
        Args:
            persist_path: ChromaDB veritabanı yolu
            collection_name: Collection adı
            embedding_model: Sentence-transformer model adı
        """
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        
        # ChromaDB client
        self.client = chromadb.PersistentClient(path=str(self.persist_path))
        
        # Embedding modeli yükle
        self._embedding_model = SentenceTransformer(embedding_model)
        self._embedding_dim = self._embedding_model.get_sentence_embedding_dimension()
        
        # Collection oluştur/al
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Cosine similarity
        )
        
        print(f"✅ MemoryHandler hazır | Collection: {collection_name} | Docs: {self.collection.count()}")
    
    def _generate_id(self) -> str:
        """Benzersiz ID üret."""
        return str(uuid.uuid4())[:8]
    
    def _get_embedding(self, text: str) -> List[float]:
        """Metin için embedding vektörü üret."""
        return self._embedding_model.encode(text).tolist()
    
    def add_memory(
        self, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None,
        memory_type: str = "conversation"
    ) -> str:
        """
        Yeni hafıza ekle.
        
        Args:
            text: Kaydedilecek metin
            metadata: Ek bilgiler (intent, topic, vb.)
            memory_type: Hafıza tipi (conversation, fact, preference, code)
        
        Returns:
            Oluşturulan belge ID'si
        """
        doc_id = self._generate_id()
        
        # Metadata hazırla
        meta = {
            "type": memory_type,
            "timestamp": datetime.now().isoformat(),
            "text_length": len(text)
        }
        
        if metadata:
            meta.update(metadata)
        
        # Embedding oluştur ve ekle
        embedding = self._get_embedding(text)
        
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[meta]
        )
        
        return doc_id
    
    def add_conversation(
        self, 
        user_message: str, 
        assistant_response: str,
        intent: Optional[str] = None,
        topic: Optional[str] = None
    ) -> str:
        """
        Konuşma çiftini hafızaya ekle.
        
        Args:
            user_message: Kullanıcı mesajı
            assistant_response: Asistan yanıtı
            intent: Tespit edilen intent
            topic: Konu başlığı
        
        Returns:
            Belge ID'si
        """
        # Konuşmayı birleştir (arama için)
        combined_text = f"Kullanıcı: {user_message}\nAsistan: {assistant_response}"
        
        metadata = {
            "user_message": user_message[:500],  # Kırp (metadata limiti)
            "assistant_response": assistant_response[:500],
        }
        
        if intent:
            metadata["intent"] = intent
        if topic:
            metadata["topic"] = topic
        
        return self.add_memory(
            text=combined_text,
            metadata=metadata,
            memory_type="conversation"
        )
    
    def search(
        self, 
        query: str, 
        top_k: int = 3,
        memory_type: Optional[str] = None,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Semantik arama yap.
        
        Args:
            query: Arama sorgusu
            top_k: Döndürülecek maksimum sonuç sayısı
            memory_type: Filtrelenecek hafıza tipi
            min_score: Minimum benzerlik skoru (0-1)
        
        Returns:
            Bulunan belgeler listesi
        """
        # Embedding oluştur
        query_embedding = self._get_embedding(query)
        
        # Where filtresi
        where_filter = None
        if memory_type:
            where_filter = {"type": memory_type}
        
        # Arama yap
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Sonuçları formatla
        formatted_results = []
        
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                # Distance'ı similarity'ye çevir (cosine distance -> similarity)
                distance = results["distances"][0][i]
                similarity = 1 - distance  # Cosine distance için
                
                if similarity >= min_score:
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "text": doc,
                        "metadata": results["metadatas"][0][i],
                        "similarity": round(similarity, 3)
                    })
        
        return formatted_results
    
    def get_relevant_context(
        self, 
        query: str, 
        top_k: int = 3,
        max_tokens: int = 500
    ) -> str:
        """
        Sorgu için ilgili bağlam oluştur (RAG için).
        
        Args:
            query: Kullanıcı sorgusu
            top_k: Maksimum belge sayısı
            max_tokens: Maksimum karakter (yaklaşık token)
        
        Returns:
            Formatlanmış bağlam metni
        """
        results = self.search(query, top_k=top_k)
        
        if not results:
            return ""
        
        context_parts = []
        total_chars = 0
        
        for i, result in enumerate(results, 1):
            text = result["text"]
            meta = result["metadata"]
            sim = result["similarity"]
            
            # Kısa versiyon oluştur
            if len(text) > 300:
                text = text[:300] + "..."
            
            part = f"[Hafıza {i}] (Benzerlik: {sim:.0%})\n{text}"
            
            if total_chars + len(part) > max_tokens * 4:  # ~4 char/token
                break
            
            context_parts.append(part)
            total_chars += len(part)
        
        if context_parts:
            return "📚 İlgili Hafıza:\n" + "\n\n".join(context_parts)
        
        return ""
    
    def delete(self, doc_id: str) -> bool:
        """Belge sil."""
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            print(f"⚠️ Silme hatası: {e}")
            return False
    
    def clear_all(self) -> int:
        """Tüm hafızayı temizle."""
        count = self.collection.count()
        
        # Collection'ı yeniden oluştur
        collection_name = self.collection.name
        self.client.delete_collection(collection_name)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"🧹 {count} belge silindi")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Hafıza istatistikleri."""
        count = self.collection.count()
        
        stats = {
            "total_documents": count,
            "collection_name": self.collection.name,
            "persist_path": str(self.persist_path),
            "embedding_dim": self._embedding_dim
        }
        
        # Tip dağılımı
        if count > 0:
            all_docs = self.collection.get(include=["metadatas"])
            type_counts = {}
            for meta in all_docs["metadatas"]:
                t = meta.get("type", "unknown")
                type_counts[t] = type_counts.get(t, 0) + 1
            stats["type_distribution"] = type_counts
        
        return stats


# Test
if __name__ == "__main__":
    print("🧪 MemoryHandler Testi\n")
    
    handler = MemoryHandler(
        persist_path="./data/chromadb/test",
        collection_name="test_memory"
    )
    
    # Temiz başla
    handler.clear_all()
    
    # Konuşmalar ekle
    handler.add_conversation(
        user_message="Merhaba, benim adım Kaan",
        assistant_response="Merhaba Kaan! Tanıştığımıza memnun oldum. Sana nasıl yardımcı olabilirim?",
        intent="general_chat"
    )
    
    handler.add_conversation(
        user_message="Python'da bir liste nasıl sıralarım?",
        assistant_response="Python'da liste sıralamak için sorted() veya list.sort() kullanabilirsin.",
        intent="code_python"
    )
    
    handler.add_conversation(
        user_message="Türk kahvesi nasıl yapılır?",
        assistant_response="Türk kahvesi için ince çekilmiş kahve, su ve isteğe göre şeker kullanılır...",
        intent="turkish_culture"
    )
    
    # Arama testi
    print("\n🔍 Arama: 'Python liste'")
    results = handler.search("Python liste", top_k=2)
    for r in results:
        print(f"  [{r['similarity']:.0%}] {r['text'][:100]}...")
    
    print("\n🔍 Arama: 'kahve'")
    results = handler.search("kahve", top_k=2)
    for r in results:
        print(f"  [{r['similarity']:.0%}] {r['text'][:100]}...")
    
    print("\n🔍 Arama: 'adım ne'")
    results = handler.search("benim adım ne", top_k=2)
    for r in results:
        print(f"  [{r['similarity']:.0%}] {r['text'][:100]}...")
    
    # Context testi
    print("\n📚 RAG Context için 'Python sıralama':")
    context = handler.get_relevant_context("Python sıralama")
    print(context)
    
    # İstatistikler
    print("\n📊 İstatistikler:")
    stats = handler.get_stats()
    print(f"  Toplam belge: {stats['total_documents']}")
    print(f"  Embedding boyutu: {stats['embedding_dim']}")
    if 'type_distribution' in stats:
        print(f"  Tip dağılımı: {stats['type_distribution']}")
    
    # Temizlik
    handler.clear_all()
    print("\n✅ Test tamamlandı!")
