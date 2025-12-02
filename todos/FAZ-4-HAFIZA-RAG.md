# 🧠 FAZ 4: Hafıza ve RAG Sistemi (The Hippocampus)

**Durum:** ⬜ Başlanmadı  
**Tahmini Süre:** 2-3 gün  
**Öncelik:** 🟠 Yüksek  
**Bağımlılık:** Faz 0, 1, 2, 3 tamamlanmış olmalı

---

## 🎯 Faz Hedefi

Modelin geçmiş konuşmaları hatırlamasını ve kullanıcı hakkında bilgi biriktirmesini sağlayan hafıza sistemi oluşturmak. Bu sistem RAG (Retrieval-Augmented Generation) kullanarak uzun süreli hafıza sağlar.

---

## 🏗️ Mimari Genel Bakış

```
┌──────────────────────────────────────────────────────────────┐
│                     KULLANICI MESAJI                         │
│              "Dün sana söylediğim proje adı neydi?"          │
└─────────────────────────┬────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────────┐   ┌─────────────────────────────────┐
│   KISA SÜRELİ HAFIZA    │   │     UZUN SÜRELİ HAFIZA (RAG)    │
│  (Context Buffer)       │   │                                 │
│                         │   │  ┌─────────────────────────────┐│
│  • Son 10-20 mesaj      │   │  │       ChromaDB              ││
│  • Session-based        │   │  │    (Vector Database)        ││
│  • RAM'de tutulur       │   │  │                             ││
│                         │   │  │  ┌───────────────────────┐  ││
│  [Usr] Merhaba          │   │  │  │  Turkish Embeddings   │  ││
│  [Bot] Selam!           │   │  │  │  (Sentence-BERT-TR)   │  ││
│  [Usr] Proje adı X      │   │  │  └───────────────────────┘  ││
│  [Bot] Tamam, not ettim │   │  │                             ││
│                         │   │  │  Persistent Storage         ││
└─────────────────────────┘   │  │  ./data/chromadb/           ││
                              │  └─────────────────────────────┘│
                              └─────────────────────────────────┘
                                            │
                                            ▼
                              ┌─────────────────────────────────┐
                              │         RETRIEVAL               │
                              │                                 │
                              │  Query: "proje adı"             │
                              │  ────────────────────           │
                              │  Top-3 Results:                 │
                              │  1. "Proje adı: EVO-TR" (0.92)  │
                              │  2. "Proje kapsamı..." (0.78)   │
                              │  3. "Kaan'ın projesi" (0.71)    │
                              └─────────────────────────────────┘
                                            │
                                            ▼
                              ┌─────────────────────────────────┐
                              │       AUGMENTED PROMPT          │
                              │                                 │
                              │  [Context from memory]          │
                              │  Proje adı: EVO-TR              │
                              │                                 │
                              │  [User question]                │
                              │  Dün söylediğim proje adı?      │
                              │                                 │
                              │  [Model response]               │
                              │  EVO-TR projesinden bahsetmiştiniz.│
                              └─────────────────────────────────┘
```

---

## 📋 Detaylı Görev Listesi

### 4.1 ChromaDB Kurulumu

#### 4.1.1 Bağımlılık Kontrolü
- [ ] ChromaDB'nin requirements.txt'te olduğunu doğrula
- [ ] Kurulumu test et:
  ```bash
  python -c "import chromadb; print(chromadb.__version__)"
  ```

#### 4.1.2 Persistent Storage Dizini
- [ ] `data/chromadb/` dizinini oluştur
- [ ] Yazma izinlerini kontrol et
- [ ] .gitignore'da olduğundan emin ol

#### 4.1.3 ChromaDB Client Test
- [ ] `scripts/test_chromadb.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """ChromaDB bağlantı testi"""
  
  import chromadb
  from chromadb.config import Settings
  
  # Persistent client oluştur
  client = chromadb.PersistentClient(
      path="./data/chromadb",
      settings=Settings(anonymized_telemetry=False)
  )
  
  # Test collection oluştur
  collection = client.get_or_create_collection(
      name="test_collection",
      metadata={"description": "Test collection"}
  )
  
  # Veri ekle
  collection.add(
      documents=["Bu bir test dokümanıdır.", "Merhaba dünya!"],
      metadatas=[{"type": "test"}, {"type": "greeting"}],
      ids=["doc1", "doc2"]
  )
  
  # Sorgula
  results = collection.query(
      query_texts=["selamlama"],
      n_results=1
  )
  
  print("✅ ChromaDB çalışıyor!")
  print(f"Query sonucu: {results['documents']}")
  
  # Temizle
  client.delete_collection("test_collection")
  print("✅ Test collection silindi")
  ```
- [ ] Testi çalıştır ve doğrula

---

### 4.2 Embedding Model Kurulumu

#### 4.2.1 Türkçe Embedding Model Seçimi
- [ ] Aşağıdaki modelleri değerlendir:

| Model | Boyut | Türkçe Performansı | Önerilen |
|-------|-------|-------------------|----------|
| `emrecan/bert-base-turkish-cased-mean-nli-stsb-tr` | 438MB | ⭐⭐⭐⭐⭐ | ✅ En iyi |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 420MB | ⭐⭐⭐⭐ | Alternatif |
| `intfloat/multilingual-e5-small` | 117MB | ⭐⭐⭐ | Hafif alternatif |

#### 4.2.2 Model İndirme
- [ ] `scripts/download_embedding_model.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """Türkçe embedding modelini indir"""
  
  from sentence_transformers import SentenceTransformer
  from pathlib import Path
  
  MODEL_NAME = "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr"
  OUTPUT_PATH = Path("./models/embeddings/turkish-sbert")
  
  def main():
      print(f"📥 Model indiriliyor: {MODEL_NAME}")
      
      model = SentenceTransformer(MODEL_NAME)
      
      OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
      model.save(str(OUTPUT_PATH))
      
      print(f"✅ Kaydedildi: {OUTPUT_PATH}")
      
      # Test
      test_sentences = [
          "Merhaba, nasılsın?",
          "Selam, ne haber?",
          "Python programlama dili"
      ]
      
      embeddings = model.encode(test_sentences)
      print(f"✅ Embedding boyutu: {embeddings.shape}")
  
  if __name__ == "__main__":
      main()
  ```
- [ ] Script'i çalıştır
- [ ] Model boyutunu not et

#### 4.2.3 Embedding Test
- [ ] Benzerlik testi yap:
  ```python
  from sentence_transformers import SentenceTransformer, util
  
  model = SentenceTransformer("./models/embeddings/turkish-sbert")
  
  sentences = [
      "Merhaba, nasılsın?",
      "Selam, ne haber?",
      "Python'da liste nasıl oluşturulur?"
  ]
  
  embeddings = model.encode(sentences)
  
  # Benzerlik matrisi
  for i, s1 in enumerate(sentences):
      for j, s2 in enumerate(sentences):
          sim = util.cos_sim(embeddings[i], embeddings[j])
          print(f"'{s1[:30]}' <-> '{s2[:30]}': {sim.item():.3f}")
  ```

---

### 4.3 ChromaDB Handler Geliştirme

#### 4.3.1 Memory Handler Class
- [ ] `src/memory/chromadb_handler.py` oluştur:
  ```python
  """
  EVO-TR Hafıza Sistemi: ChromaDB Handler
  
  Uzun süreli hafıza yönetimi için vektör veritabanı işlemleri.
  """
  
  import json
  import uuid
  from datetime import datetime
  from pathlib import Path
  from typing import List, Dict, Optional, Any
  
  import chromadb
  from chromadb.config import Settings
  from sentence_transformers import SentenceTransformer
  
  
  class MemoryHandler:
      """ChromaDB tabanlı uzun süreli hafıza yöneticisi"""
      
      def __init__(
          self,
          persist_dir: str = "./data/chromadb",
          embedding_model_path: str = "./models/embeddings/turkish-sbert",
          collection_name: str = "evo_tr_memory"
      ):
          """
          Args:
              persist_dir: ChromaDB kalıcı depolama dizini
              embedding_model_path: Embedding model yolu
              collection_name: Collection adı
          """
          self.persist_dir = Path(persist_dir)
          self.persist_dir.mkdir(parents=True, exist_ok=True)
          
          # ChromaDB client
          self.client = chromadb.PersistentClient(
              path=str(self.persist_dir),
              settings=Settings(anonymized_telemetry=False)
          )
          
          # Embedding model
          self.embedding_model = SentenceTransformer(embedding_model_path)
          
          # Collection
          self.collection = self.client.get_or_create_collection(
              name=collection_name,
              metadata={"description": "EVO-TR Long-term Memory"}
          )
          
          print(f"✅ MemoryHandler başlatıldı. Collection: {collection_name}")
          print(f"   Mevcut kayıt sayısı: {self.collection.count()}")
      
      def add_memory(
          self,
          text: str,
          metadata: Optional[Dict[str, Any]] = None,
          memory_type: str = "general"
      ) -> str:
          """
          Hafızaya yeni bilgi ekle.
          
          Args:
              text: Kaydedilecek metin
              metadata: Ek bilgiler (tarih, kategori, vb.)
              memory_type: Hafıza tipi (general, user_info, conversation, fact)
              
          Returns:
              Oluşturulan belge ID'si
          """
          doc_id = str(uuid.uuid4())
          
          # Varsayılan metadata
          default_metadata = {
              "type": memory_type,
              "created_at": datetime.now().isoformat(),
              "text_length": len(text)
          }
          
          if metadata:
              default_metadata.update(metadata)
          
          # Embedding oluştur ve ekle
          embedding = self.embedding_model.encode([text])[0].tolist()
          
          self.collection.add(
              documents=[text],
              embeddings=[embedding],
              metadatas=[default_metadata],
              ids=[doc_id]
          )
          
          return doc_id
      
      def search(
          self,
          query: str,
          top_k: int = 3,
          min_score: float = 0.5,
          filter_metadata: Optional[Dict] = None
      ) -> List[Dict]:
          """
          Hafızada arama yap.
          
          Args:
              query: Arama sorgusu
              top_k: Döndürülecek maksimum sonuç sayısı
              min_score: Minimum benzerlik skoru
              filter_metadata: Metadata filtresi
              
          Returns:
              Bulunan belgelerin listesi
          """
          # Query embedding
          query_embedding = self.embedding_model.encode([query])[0].tolist()
          
          # Arama
          results = self.collection.query(
              query_embeddings=[query_embedding],
              n_results=top_k,
              where=filter_metadata
          )
          
          # Sonuçları formatla
          formatted_results = []
          
          if results and results['documents'] and results['documents'][0]:
              for i, doc in enumerate(results['documents'][0]):
                  # Distance'ı similarity'ye çevir (ChromaDB L2 distance kullanır)
                  distance = results['distances'][0][i] if results['distances'] else 0
                  # L2 distance -> cosine similarity yaklaşımı
                  similarity = 1 / (1 + distance)
                  
                  if similarity >= min_score:
                      formatted_results.append({
                          "id": results['ids'][0][i],
                          "text": doc,
                          "score": similarity,
                          "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                      })
          
          return formatted_results
      
      def get_by_id(self, doc_id: str) -> Optional[Dict]:
          """ID ile belge getir"""
          result = self.collection.get(ids=[doc_id])
          
          if result and result['documents']:
              return {
                  "id": doc_id,
                  "text": result['documents'][0],
                  "metadata": result['metadatas'][0] if result['metadatas'] else {}
              }
          return None
      
      def delete(self, doc_id: str) -> bool:
          """Belge sil"""
          try:
              self.collection.delete(ids=[doc_id])
              return True
          except Exception:
              return False
      
      def update(self, doc_id: str, new_text: str, new_metadata: Optional[Dict] = None) -> bool:
          """Belge güncelle"""
          try:
              existing = self.get_by_id(doc_id)
              if not existing:
                  return False
              
              # Yeni embedding
              embedding = self.embedding_model.encode([new_text])[0].tolist()
              
              # Metadata güncelle
              metadata = existing.get("metadata", {})
              metadata["updated_at"] = datetime.now().isoformat()
              if new_metadata:
                  metadata.update(new_metadata)
              
              self.collection.update(
                  ids=[doc_id],
                  documents=[new_text],
                  embeddings=[embedding],
                  metadatas=[metadata]
              )
              return True
          except Exception:
              return False
      
      def get_stats(self) -> Dict:
          """Hafıza istatistikleri"""
          count = self.collection.count()
          
          # Tip bazlı dağılım
          type_counts = {}
          if count > 0:
              all_docs = self.collection.get()
              for meta in all_docs.get('metadatas', []):
                  mem_type = meta.get('type', 'unknown')
                  type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
          
          return {
              "total_memories": count,
              "type_distribution": type_counts,
              "persist_dir": str(self.persist_dir)
          }
      
      def clear_all(self) -> int:
          """Tüm hafızayı temizle (DİKKAT!)"""
          count = self.collection.count()
          
          # Collection'ı sil ve yeniden oluştur
          collection_name = self.collection.name
          self.client.delete_collection(collection_name)
          self.collection = self.client.create_collection(
              name=collection_name,
              metadata={"description": "EVO-TR Long-term Memory"}
          )
          
          return count
  
  
  # Singleton instance
  _memory_handler: Optional[MemoryHandler] = None
  
  
  def get_memory_handler() -> MemoryHandler:
      """Global MemoryHandler instance döndür"""
      global _memory_handler
      if _memory_handler is None:
          _memory_handler = MemoryHandler()
      return _memory_handler
  ```

#### 4.3.2 Memory Handler Testleri
- [ ] `tests/test_memory.py` oluştur:
  ```python
  """Memory Handler testleri"""
  
  import pytest
  from src.memory.chromadb_handler import MemoryHandler
  
  
  @pytest.fixture
  def memory_handler():
      """Test için geçici memory handler"""
      handler = MemoryHandler(
          persist_dir="./data/chromadb_test",
          collection_name="test_memory"
      )
      yield handler
      # Temizlik
      handler.clear_all()
  
  
  class TestMemoryHandler:
      
      def test_add_memory(self, memory_handler):
          """Hafızaya ekleme testi"""
          doc_id = memory_handler.add_memory(
              "Kullanıcının adı Kaan.",
              memory_type="user_info"
          )
          assert doc_id is not None
          assert len(doc_id) > 0
      
      def test_search(self, memory_handler):
          """Arama testi"""
          # Veri ekle
          memory_handler.add_memory("Proje adı EVO-TR.", memory_type="fact")
          memory_handler.add_memory("Kaan Python seviyor.", memory_type="user_info")
          
          # Ara
          results = memory_handler.search("proje adı ne?", top_k=1)
          assert len(results) > 0
          assert "EVO-TR" in results[0]["text"]
      
      def test_get_by_id(self, memory_handler):
          """ID ile getirme testi"""
          doc_id = memory_handler.add_memory("Test verisi")
          result = memory_handler.get_by_id(doc_id)
          assert result is not None
          assert result["text"] == "Test verisi"
      
      def test_delete(self, memory_handler):
          """Silme testi"""
          doc_id = memory_handler.add_memory("Silinecek veri")
          assert memory_handler.delete(doc_id) == True
          assert memory_handler.get_by_id(doc_id) is None
      
      def test_stats(self, memory_handler):
          """İstatistik testi"""
          memory_handler.add_memory("Veri 1", memory_type="fact")
          memory_handler.add_memory("Veri 2", memory_type="user_info")
          
          stats = memory_handler.get_stats()
          assert stats["total_memories"] == 2
  ```

---

### 4.4 Kısa Süreli Hafıza (Context Buffer)

#### 4.4.1 Context Buffer Class
- [ ] `src/memory/context_buffer.py` oluştur:
  ```python
  """
  EVO-TR Kısa Süreli Hafıza: Context Buffer
  
  Son N mesajı bellekte tutar ve context olarak sağlar.
  """
  
  from collections import deque
  from dataclasses import dataclass, field
  from datetime import datetime
  from typing import List, Optional, Dict
  
  
  @dataclass
  class Message:
      """Tek bir mesaj"""
      role: str  # "user" veya "assistant"
      content: str
      timestamp: datetime = field(default_factory=datetime.now)
      metadata: Dict = field(default_factory=dict)
  
  
  class ContextBuffer:
      """
      Son N mesajı tutan kısa süreli hafıza.
      
      Session-based çalışır, yeniden başlatıldığında sıfırlanır.
      """
      
      def __init__(
          self,
          max_messages: int = 20,
          max_tokens: int = 4096
      ):
          """
          Args:
              max_messages: Maksimum mesaj sayısı
              max_tokens: Maksimum token sayısı (tahmini)
          """
          self.max_messages = max_messages
          self.max_tokens = max_tokens
          self.messages: deque = deque(maxlen=max_messages)
          self.session_id: str = datetime.now().strftime("%Y%m%d_%H%M%S")
      
      def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
          """Yeni mesaj ekle"""
          message = Message(
              role=role,
              content=content,
              metadata=metadata or {}
          )
          self.messages.append(message)
          
          # Token kontrolü (basit yaklaşım: 4 karakter = 1 token)
          self._trim_to_token_limit()
      
      def _trim_to_token_limit(self) -> None:
          """Token limitini aşarsa eski mesajları kaldır"""
          total_chars = sum(len(m.content) for m in self.messages)
          estimated_tokens = total_chars / 4
          
          while estimated_tokens > self.max_tokens and len(self.messages) > 2:
              self.messages.popleft()
              total_chars = sum(len(m.content) for m in self.messages)
              estimated_tokens = total_chars / 4
      
      def get_messages(self, last_n: Optional[int] = None) -> List[Message]:
          """Mesajları getir"""
          if last_n:
              return list(self.messages)[-last_n:]
          return list(self.messages)
      
      def get_formatted_context(self, format_type: str = "chat") -> str:
          """
          Formatlanmış context döndür.
          
          Args:
              format_type: "chat", "qwen", "simple"
          """
          if format_type == "chat":
              lines = []
              for msg in self.messages:
                  role_label = "Kullanıcı" if msg.role == "user" else "Asistan"
                  lines.append(f"{role_label}: {msg.content}")
              return "\n".join(lines)
          
          elif format_type == "qwen":
              # Qwen chat format
              formatted = []
              for msg in self.messages:
                  if msg.role == "user":
                      formatted.append(f"<|im_start|>user\n{msg.content}<|im_end|>")
                  else:
                      formatted.append(f"<|im_start|>assistant\n{msg.content}<|im_end|>")
              return "\n".join(formatted)
          
          else:  # simple
              return "\n\n".join(m.content for m in self.messages)
      
      def get_last_user_message(self) -> Optional[str]:
          """Son kullanıcı mesajını döndür"""
          for msg in reversed(self.messages):
              if msg.role == "user":
                  return msg.content
          return None
      
      def get_last_assistant_message(self) -> Optional[str]:
          """Son asistan mesajını döndür"""
          for msg in reversed(self.messages):
              if msg.role == "assistant":
                  return msg.content
          return None
      
      def clear(self) -> None:
          """Buffer'ı temizle"""
          self.messages.clear()
          self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
      
      def get_stats(self) -> Dict:
          """Buffer istatistikleri"""
          total_chars = sum(len(m.content) for m in self.messages)
          return {
              "session_id": self.session_id,
              "message_count": len(self.messages),
              "max_messages": self.max_messages,
              "estimated_tokens": total_chars / 4,
              "max_tokens": self.max_tokens
          }
      
      def export_session(self) -> List[Dict]:
          """Session'ı export et"""
          return [
              {
                  "role": msg.role,
                  "content": msg.content,
                  "timestamp": msg.timestamp.isoformat(),
                  "metadata": msg.metadata
              }
              for msg in self.messages
          ]
  
  
  # Singleton
  _context_buffer: Optional[ContextBuffer] = None
  
  
  def get_context_buffer() -> ContextBuffer:
      """Global ContextBuffer instance"""
      global _context_buffer
      if _context_buffer is None:
          _context_buffer = ContextBuffer()
      return _context_buffer
  ```

---

### 4.5 RAG Pipeline Geliştirme

#### 4.5.1 RAG Orchestrator
- [ ] `src/memory/rag_pipeline.py` oluştur:
  ```python
  """
  EVO-TR RAG Pipeline
  
  Kullanıcı sorusunu alır, hafızada arama yapar ve zenginleştirilmiş context döndürür.
  """
  
  from typing import List, Dict, Optional, Tuple
  from .chromadb_handler import get_memory_handler, MemoryHandler
  from .context_buffer import get_context_buffer, ContextBuffer
  
  
  class RAGPipeline:
      """Retrieval-Augmented Generation Pipeline"""
      
      def __init__(
          self,
          memory_handler: Optional[MemoryHandler] = None,
          context_buffer: Optional[ContextBuffer] = None,
          top_k: int = 3,
          min_relevance: float = 0.5,
          max_context_tokens: int = 1024
      ):
          self.memory = memory_handler or get_memory_handler()
          self.buffer = context_buffer or get_context_buffer()
          self.top_k = top_k
          self.min_relevance = min_relevance
          self.max_context_tokens = max_context_tokens
      
      def retrieve(self, query: str) -> List[Dict]:
          """
          Hafızadan ilgili bilgileri getir.
          
          Args:
              query: Kullanıcı sorusu
              
          Returns:
              İlgili belgelerin listesi
          """
          results = self.memory.search(
              query=query,
              top_k=self.top_k,
              min_score=self.min_relevance
          )
          return results
      
      def format_retrieved_context(self, results: List[Dict]) -> str:
          """Getirilen sonuçları context string'e çevir"""
          if not results:
              return ""
          
          lines = ["[Hafızadan hatırlanan bilgiler:]"]
          for i, result in enumerate(results, 1):
              lines.append(f"{i}. {result['text']}")
          
          return "\n".join(lines)
      
      def build_augmented_prompt(
          self,
          user_query: str,
          include_memory: bool = True,
          include_history: bool = True,
          system_prompt: Optional[str] = None
      ) -> str:
          """
          Zenginleştirilmiş prompt oluştur.
          
          Args:
              user_query: Kullanıcı sorusu
              include_memory: Uzun süreli hafızayı dahil et
              include_history: Kısa süreli geçmişi dahil et
              system_prompt: Opsiyonel system prompt
              
          Returns:
              Model'e gönderilecek tam prompt
          """
          parts = []
          
          # System prompt
          if system_prompt:
              parts.append(f"[System]: {system_prompt}")
          
          # Uzun süreli hafıza (RAG)
          if include_memory:
              retrieved = self.retrieve(user_query)
              if retrieved:
                  memory_context = self.format_retrieved_context(retrieved)
                  parts.append(memory_context)
          
          # Kısa süreli geçmiş
          if include_history and len(self.buffer.messages) > 0:
              history = self.buffer.get_formatted_context(format_type="chat")
              if history:
                  parts.append(f"[Sohbet geçmişi:]\n{history}")
          
          # Kullanıcı sorusu
          parts.append(f"[Kullanıcı]: {user_query}")
          
          return "\n\n".join(parts)
      
      def process_response(
          self,
          user_query: str,
          model_response: str,
          save_to_memory: bool = True
      ) -> None:
          """
          Yanıtı işle ve hafızaya kaydet.
          
          Args:
              user_query: Kullanıcı sorusu
              model_response: Model yanıtı
              save_to_memory: Uzun süreli hafızaya kaydet
          """
          # Kısa süreli hafızaya ekle
          self.buffer.add_message("user", user_query)
          self.buffer.add_message("assistant", model_response)
          
          # Uzun süreli hafızaya önemli bilgileri kaydet
          if save_to_memory:
              self._extract_and_save_info(user_query, model_response)
      
      def _extract_and_save_info(self, query: str, response: str) -> None:
          """
          Konuşmadan önemli bilgileri çıkar ve kaydet.
          
          TODO: NER, keyword extraction eklenebilir
          """
          # Basit yaklaşım: "benim adım X" gibi pattern'ları yakala
          import re
          
          # İsim pattern'ı
          name_patterns = [
              r"benim ad[ıi]m (\w+)",
              r"ben (\w+)",
              r"ad[ıi]m (\w+)"
          ]
          
          combined_text = f"{query} {response}".lower()
          
          for pattern in name_patterns:
              match = re.search(pattern, combined_text)
              if match:
                  name = match.group(1).title()
                  self.memory.add_memory(
                      f"Kullanıcının adı: {name}",
                      metadata={"extracted_type": "user_name"},
                      memory_type="user_info"
                  )
                  break
          
          # Proje adı pattern'ı
          project_patterns = [
              r"proje(?:nin)? ad[ıi] (\w+)",
              r"(\w+) projes[ıi]"
          ]
          
          for pattern in project_patterns:
              match = re.search(pattern, combined_text)
              if match:
                  project = match.group(1).upper()
                  self.memory.add_memory(
                      f"Proje adı: {project}",
                      metadata={"extracted_type": "project_name"},
                      memory_type="fact"
                  )
                  break
      
      def get_stats(self) -> Dict:
          """Pipeline istatistikleri"""
          return {
              "memory_stats": self.memory.get_stats(),
              "buffer_stats": self.buffer.get_stats(),
              "config": {
                  "top_k": self.top_k,
                  "min_relevance": self.min_relevance,
                  "max_context_tokens": self.max_context_tokens
              }
          }
  
  
  # Singleton
  _rag_pipeline: Optional[RAGPipeline] = None
  
  
  def get_rag_pipeline() -> RAGPipeline:
      """Global RAGPipeline instance"""
      global _rag_pipeline
      if _rag_pipeline is None:
          _rag_pipeline = RAGPipeline()
      return _rag_pipeline
  ```

---

### 4.6 Entegrasyon ve Test

#### 4.6.1 Memory Demo Script
- [ ] `scripts/demo_memory.py` oluştur:
  ```python
  #!/usr/bin/env python3
  """Hafıza sistemi demo"""
  
  from rich.console import Console
  from rich.panel import Panel
  from rich.table import Table
  
  from src.memory.rag_pipeline import get_rag_pipeline
  from src.memory.chromadb_handler import get_memory_handler
  
  console = Console()
  
  def main():
      console.print("\n[bold blue]🧠 EVO-TR Hafıza Sistemi Demo[/bold blue]\n")
      
      # RAG Pipeline al
      rag = get_rag_pipeline()
      memory = get_memory_handler()
      
      # Başlangıç durumu
      stats = rag.get_stats()
      console.print(f"Mevcut hafıza: {stats['memory_stats']['total_memories']} kayıt\n")
      
      # Demo konuşma
      conversations = [
          ("Merhaba, benim adım Kaan.", "Merhaba Kaan! Size nasıl yardımcı olabilirim?"),
          ("EVO-TR projesi üzerinde çalışıyorum.", "EVO-TR projesi hakkında not aldım. Proje ile ilgili nasıl yardımcı olabilirim?"),
          ("Python'da LoRA eğitimi yapacağım.", "LoRA eğitimi için size yardımcı olabilirim. Hangi model üzerinde çalışıyorsunuz?"),
      ]
      
      console.print("[yellow]📝 Demo konuşmalar ekleniyor...[/yellow]\n")
      
      for user_msg, assistant_msg in conversations:
          console.print(f"[cyan]Kullanıcı:[/cyan] {user_msg}")
          console.print(f"[green]Asistan:[/green] {assistant_msg}\n")
          
          rag.process_response(user_msg, assistant_msg, save_to_memory=True)
      
      # Hafıza araması
      console.print("\n[yellow]🔍 Hafıza araması yapılıyor...[/yellow]\n")
      
      test_queries = [
          "Kullanıcının adı ne?",
          "Hangi proje üzerinde çalışıyoruz?",
          "Ne yapmak istiyor?"
      ]
      
      for query in test_queries:
          console.print(f"[cyan]Soru:[/cyan] {query}")
          
          results = memory.search(query, top_k=2)
          
          if results:
              for r in results:
                  console.print(f"   → {r['text']} (skor: {r['score']:.2f})")
          else:
              console.print("   → Sonuç bulunamadı")
          
          console.print()
      
      # Augmented prompt örneği
      console.print("\n[yellow]📄 Augmented Prompt örneği:[/yellow]\n")
      
      test_question = "Daha önce sana söylediğim proje adı neydi?"
      augmented = rag.build_augmented_prompt(test_question)
      
      console.print(Panel(augmented, title="Zenginleştirilmiş Prompt", expand=False))
      
      # Final stats
      console.print("\n[yellow]📊 Final İstatistikler:[/yellow]\n")
      
      final_stats = rag.get_stats()
      
      table = Table(title="Hafıza Durumu")
      table.add_column("Metrik", style="cyan")
      table.add_column("Değer", style="green")
      
      table.add_row("Toplam Kayıt", str(final_stats['memory_stats']['total_memories']))
      table.add_row("Buffer Mesaj", str(final_stats['buffer_stats']['message_count']))
      table.add_row("Session ID", final_stats['buffer_stats']['session_id'])
      
      console.print(table)
  
  
  if __name__ == "__main__":
      main()
  ```

#### 4.6.2 Entegrasyon Testi
- [ ] `tests/test_rag_pipeline.py` oluştur
- [ ] Uçtan uca test senaryoları yaz
- [ ] Latency testleri ekle

---

## ✅ Faz Tamamlanma Kriterleri

1. [ ] ChromaDB persistent storage çalışıyor
2. [ ] Türkçe embedding model yüklendi
3. [ ] MemoryHandler tüm CRUD operasyonlarını destekliyor
4. [ ] ContextBuffer son N mesajı tutuyor
5. [ ] RAG Pipeline hafızadan retrieval yapabiliyor
6. [ ] Augmented prompt oluşturuluyor
7. [ ] Demo script başarıyla çalışıyor
8. [ ] Search latency < 100ms

---

## ⏭️ Sonraki Faz

Faz 4 tamamlandıktan sonra → **FAZ-5-ENTEGRASYON.md** dosyasına geç.

---

## 🐛 Olası Sorunlar ve Çözümleri

### ChromaDB Yazma Hatası
**Çözüm:** Dizin izinlerini kontrol et, disk alanını kontrol et

### Embedding Model Yavaş
**Çözüm:** Batch processing kullan, daha küçük model seç

### Search Sonuçları İlgisiz
**Çözüm:** min_score threshold'u artır, Türkçe-spesifik model kullan

---

## 📊 Zaman Takibi

| Görev | Başlangıç | Bitiş | Süre |
|-------|-----------|-------|------|
| 4.1 ChromaDB Kurulum | | | |
| 4.2 Embedding Model | | | |
| 4.3 Memory Handler | | | |
| 4.4 Context Buffer | | | |
| 4.5 RAG Pipeline | | | |
| 4.6 Test & Demo | | | |
| **TOPLAM** | | | |

---

*Bu faz tamamlandığında, "✅ FAZ 4 TAMAMLANDI" olarak işaretle.*
