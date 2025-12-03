"""
EVO-TR: Context Buffer

Kısa süreli hafıza - son N mesajı token limiti dahilinde tutar.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Message:
    """Tek bir mesaj."""
    role: str  # "user" veya "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    intent: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Dict'e dönüştür."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "intent": self.intent,
            "metadata": self.metadata
        }
    
    def to_chat_format(self) -> Dict:
        """Chat format için sadece role ve content."""
        return {"role": self.role, "content": self.content}
    
    @property
    def token_estimate(self) -> int:
        """Yaklaşık token sayısı (4 karakter = 1 token)."""
        return len(self.content) // 4 + 1


class ContextBuffer:
    """
    Kısa süreli hafıza yönetimi.
    
    Özellikler:
    - Son N mesajı tutar
    - Token limiti kontrolü
    - Sliding window mantığı
    - Chat format export
    """
    
    def __init__(
        self,
        max_messages: int = 20,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None
    ):
        """
        ContextBuffer başlat.
        
        Args:
            max_messages: Maksimum mesaj sayısı
            max_tokens: Maksimum token (yaklaşık)
            system_prompt: Sabit system prompt
        """
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self._messages: List[Message] = []
    
    def add_user_message(
        self, 
        content: str, 
        intent: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """Kullanıcı mesajı ekle."""
        message = Message(
            role="user",
            content=content,
            intent=intent,
            metadata=metadata or {}
        )
        self._add_message(message)
    
    def add_assistant_message(
        self, 
        content: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """Asistan mesajı ekle."""
        message = Message(
            role="assistant",
            content=content,
            metadata=metadata or {}
        )
        self._add_message(message)
    
    def _add_message(self, message: Message) -> None:
        """Mesaj ekle ve limitleri kontrol et."""
        self._messages.append(message)
        self._enforce_limits()
    
    def _enforce_limits(self) -> None:
        """Mesaj sayısı ve token limitlerini uygula."""
        # Mesaj sayısı limiti
        while len(self._messages) > self.max_messages:
            self._messages.pop(0)
        
        # Token limiti
        while self.total_tokens > self.max_tokens and len(self._messages) > 1:
            self._messages.pop(0)
    
    @property
    def total_tokens(self) -> int:
        """Toplam yaklaşık token sayısı."""
        system_tokens = len(self.system_prompt) // 4 if self.system_prompt else 0
        message_tokens = sum(m.token_estimate for m in self._messages)
        return system_tokens + message_tokens
    
    @property
    def message_count(self) -> int:
        """Mesaj sayısı."""
        return len(self._messages)
    
    def get_messages(self) -> List[Message]:
        """Tüm mesajları getir."""
        return self._messages.copy()
    
    def get_chat_history(self, include_system: bool = True) -> List[Dict]:
        """
        Chat format için mesaj listesi.
        
        Args:
            include_system: System prompt dahil edilsin mi
        
        Returns:
            [{"role": "...", "content": "..."}] formatında liste
        """
        messages = []
        
        if include_system and self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        for msg in self._messages:
            messages.append(msg.to_chat_format())
        
        return messages
    
    def get_last_n_messages(self, n: int) -> List[Message]:
        """Son N mesajı getir."""
        return self._messages[-n:] if n < len(self._messages) else self._messages.copy()
    
    def get_last_user_message(self) -> Optional[Message]:
        """Son kullanıcı mesajını getir."""
        for msg in reversed(self._messages):
            if msg.role == "user":
                return msg
        return None
    
    def get_last_assistant_message(self) -> Optional[Message]:
        """Son asistan mesajını getir."""
        for msg in reversed(self._messages):
            if msg.role == "assistant":
                return msg
        return None
    
    def get_conversation_pairs(self) -> List[Tuple[Message, Message]]:
        """User-Assistant mesaj çiftlerini getir."""
        pairs = []
        i = 0
        while i < len(self._messages) - 1:
            if self._messages[i].role == "user" and self._messages[i+1].role == "assistant":
                pairs.append((self._messages[i], self._messages[i+1]))
                i += 2
            else:
                i += 1
        return pairs
    
    def set_system_prompt(self, prompt: str) -> None:
        """System prompt ayarla."""
        self.system_prompt = prompt
    
    def clear(self) -> None:
        """Tüm mesajları temizle."""
        self._messages.clear()
    
    def get_context_summary(self) -> str:
        """Bağlam özeti (debugging için)."""
        lines = [
            f"📝 Context Buffer Durumu:",
            f"   Mesaj sayısı: {self.message_count}/{self.max_messages}",
            f"   Toplam token: ~{self.total_tokens}/{self.max_tokens}",
            f"   System prompt: {'✅' if self.system_prompt else '❌'}"
        ]
        
        if self._messages:
            lines.append("   Son 3 mesaj:")
            for msg in self._messages[-3:]:
                preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                lines.append(f"     [{msg.role}] {preview}")
        
        return "\n".join(lines)
    
    def export_to_json(self) -> str:
        """JSON formatında export."""
        data = {
            "max_messages": self.max_messages,
            "max_tokens": self.max_tokens,
            "system_prompt": self.system_prompt,
            "messages": [m.to_dict() for m in self._messages]
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "ContextBuffer":
        """JSON'dan import."""
        data = json.loads(json_str)
        buffer = cls(
            max_messages=data["max_messages"],
            max_tokens=data["max_tokens"],
            system_prompt=data.get("system_prompt")
        )
        
        for msg_data in data.get("messages", []):
            msg = Message(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                intent=msg_data.get("intent"),
                metadata=msg_data.get("metadata", {})
            )
            buffer._messages.append(msg)
        
        return buffer


# Test
if __name__ == "__main__":
    print("🧪 ContextBuffer Testi\n")
    
    # Buffer oluştur
    buffer = ContextBuffer(
        max_messages=10,
        max_tokens=500,
        system_prompt="Sen EVO-TR, Türkçe ve Python konusunda uzman bir asistansın."
    )
    
    # Mesajlar ekle
    buffer.add_user_message("Merhaba!", intent="general_chat")
    buffer.add_assistant_message("Merhaba! Size nasıl yardımcı olabilirim?")
    
    buffer.add_user_message("Python'da liste sıralama nasıl yapılır?", intent="code_python")
    buffer.add_assistant_message("Python'da liste sıralamak için sorted() fonksiyonu veya list.sort() metodu kullanabilirsiniz.")
    
    buffer.add_user_message("Örnek kod gösterir misin?", intent="code_python")
    buffer.add_assistant_message("Tabii! İşte örnekler:\n\n```python\n# sorted() ile\nmy_list = [3, 1, 4, 1, 5]\nsorted_list = sorted(my_list)\n\n# sort() ile\nmy_list.sort()\n```")
    
    # Durum özeti
    print(buffer.get_context_summary())
    
    # Chat history
    print("\n💬 Chat History:")
    for msg in buffer.get_chat_history():
        preview = msg['content'][:60] + "..." if len(msg['content']) > 60 else msg['content']
        print(f"  [{msg['role']}] {preview}")
    
    # Son mesajlar
    print(f"\n📨 Son user mesajı: {buffer.get_last_user_message().content[:50]}...")
    print(f"📨 Son assistant mesajı: {buffer.get_last_assistant_message().content[:50]}...")
    
    # Çiftler
    print(f"\n🔗 Konuşma çifti sayısı: {len(buffer.get_conversation_pairs())}")
    
    # Token limiti testi
    print("\n⚡ Token limiti testi - çok uzun mesaj ekleniyor...")
    buffer.add_user_message("A" * 2000)  # 500 token'dan fazla
    print(buffer.get_context_summary())
    
    print("\n✅ Test tamamlandı!")
