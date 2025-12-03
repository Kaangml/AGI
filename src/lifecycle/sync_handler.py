"""
EVO-TR Sync Handler
====================
Gündüz modu - Real-time chat loop ve session yönetimi.

Özellikler:
- Real-time conversation handling
- Session state management
- Graceful shutdown
- Logger entegrasyonu
"""

import time
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass, field

from .logger import EvoTRLogger, create_logger


@dataclass
class SessionState:
    """Session durumu"""
    session_id: str
    start_time: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    turn_count: int = 0
    last_intent: Optional[str] = None
    last_adapter: Optional[str] = None
    error_count: int = 0
    total_response_time_ms: float = 0.0
    
    @property
    def avg_response_time_ms(self) -> float:
        if self.turn_count == 0:
            return 0.0
        return self.total_response_time_ms / self.turn_count
    
    @property
    def duration_seconds(self) -> float:
        return (datetime.now() - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "is_active": self.is_active,
            "turn_count": self.turn_count,
            "last_intent": self.last_intent,
            "last_adapter": self.last_adapter,
            "error_count": self.error_count,
            "avg_response_time_ms": self.avg_response_time_ms,
            "duration_seconds": self.duration_seconds
        }


class SyncHandler:
    """
    Sync (Gündüz) modu handler.
    
    Real-time konuşma döngüsü yönetimi:
    - User input alma
    - Response üretimi (callback ile)
    - Session tracking
    - Error handling
    """
    
    def __init__(
        self,
        chat_callback: Callable[[str], Dict[str, Any]],
        logger: Optional[EvoTRLogger] = None,
        log_dir: str = "./logs",
        max_errors: int = 5,
        timeout_seconds: float = 60.0
    ):
        """
        Args:
            chat_callback: Ana chat fonksiyonu (EvoTR.chat gibi)
                          Input: user_message -> Output: {"response": str, "intent": str, ...}
            logger: EvoTRLogger instance (veya yeni oluşturulur)
            log_dir: Log dizini
            max_errors: Üst üste hata limiti (aşılırsa session sonlandırılır)
            timeout_seconds: Yanıt timeout süresi
        """
        self.chat_callback = chat_callback
        self.logger = logger or create_logger(log_dir)
        self.max_errors = max_errors
        self.timeout_seconds = timeout_seconds
        
        # Session state
        self.state = SessionState(session_id=self.logger.session_id)
        
        # Callbacks
        self._on_start_callbacks = []
        self._on_response_callbacks = []
        self._on_error_callbacks = []
        self._on_end_callbacks = []
        
        self.logger.log_system("SyncHandler initialized", {
            "max_errors": max_errors,
            "timeout_seconds": timeout_seconds
        })
    
    # ============ Event Callbacks ============
    
    def on_start(self, callback: Callable):
        """Session başlangıç callback'i ekle"""
        self._on_start_callbacks.append(callback)
        return callback
    
    def on_response(self, callback: Callable):
        """Response callback'i ekle"""
        self._on_response_callbacks.append(callback)
        return callback
    
    def on_error(self, callback: Callable):
        """Error callback'i ekle"""
        self._on_error_callbacks.append(callback)
        return callback
    
    def on_end(self, callback: Callable):
        """Session bitiş callback'i ekle"""
        self._on_end_callbacks.append(callback)
        return callback
    
    def _trigger_callbacks(self, callbacks: list, *args, **kwargs):
        """Callback'leri tetikle"""
        for cb in callbacks:
            try:
                cb(*args, **kwargs)
            except Exception as e:
                self.logger.log_error(f"Callback error: {e}")
    
    # ============ Chat Processing ============
    
    def process_message(self, user_input: str) -> Dict[str, Any]:
        """
        Tek bir mesaj işle.
        
        Returns:
            {
                "response": str,
                "intent": str,
                "confidence": float,
                "adapter": str | None,
                "memory_hits": int,
                "response_time_ms": float,
                "success": bool,
                "error": str | None
            }
        """
        start_time = time.time()
        
        try:
            # Chat callback'i çağır
            result = self.chat_callback(user_input)
            
            # Response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # State güncelle
            self.state.turn_count += 1
            self.state.total_response_time_ms += response_time_ms
            self.state.last_intent = result.get("intent", "unknown")
            self.state.last_adapter = result.get("adapter")
            self.state.error_count = 0  # Reset on success
            
            # Response dict oluştur
            response_data = {
                "response": result.get("response", ""),
                "intent": result.get("intent", "unknown"),
                "confidence": result.get("confidence", 0.0),
                "adapter": result.get("adapter"),
                "memory_hits": result.get("memory_hits", 0),
                "response_time_ms": response_time_ms,
                "success": True,
                "error": None
            }
            
            # Log conversation
            self.logger.log_conversation(
                user_input=user_input,
                assistant_response=response_data["response"],
                intent=response_data["intent"],
                confidence=response_data["confidence"],
                adapter_used=response_data["adapter"],
                memory_hits=response_data["memory_hits"],
                response_time_ms=response_time_ms,
                tokens_generated=result.get("tokens", 0),
                success=True
            )
            
            # Trigger callbacks
            self._trigger_callbacks(self._on_response_callbacks, response_data)
            
            return response_data
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            self.state.error_count += 1
            
            error_data = {
                "response": "",
                "intent": "error",
                "confidence": 0.0,
                "adapter": None,
                "memory_hits": 0,
                "response_time_ms": response_time_ms,
                "success": False,
                "error": str(e)
            }
            
            # Log error
            self.logger.log_error(f"Chat error: {e}", {
                "user_input": user_input[:100],
                "error_count": self.state.error_count
            })
            
            self.logger.log_conversation(
                user_input=user_input,
                assistant_response="",
                intent="error",
                confidence=0.0,
                response_time_ms=response_time_ms,
                success=False,
                error_message=str(e)
            )
            
            # Trigger callbacks
            self._trigger_callbacks(self._on_error_callbacks, e, error_data)
            
            # Check error limit
            if self.state.error_count >= self.max_errors:
                self.logger.log_error(f"Max error limit reached ({self.max_errors})")
                self.state.is_active = False
            
            return error_data
    
    # ============ Session Management ============
    
    def start_session(self):
        """Session'ı başlat"""
        self.state = SessionState(session_id=self.logger.session_id)
        self.logger.log_system("Session started")
        self._trigger_callbacks(self._on_start_callbacks, self.state)
    
    def end_session(self):
        """Session'ı sonlandır"""
        self.state.is_active = False
        stats = self.state.to_dict()
        self.logger.log_system("Session ended", stats)
        self.logger.end_session()
        self._trigger_callbacks(self._on_end_callbacks, stats)
        return stats
    
    def get_state(self) -> Dict:
        """Mevcut session durumunu al"""
        return self.state.to_dict()
    
    # ============ Interactive Loop ============
    
    def run_interactive(
        self,
        prompt: str = "You: ",
        exit_commands: list = None,
        welcome_message: str = None
    ):
        """
        İnteraktif chat döngüsü başlat.
        
        Args:
            prompt: Input prompt
            exit_commands: Çıkış komutları (default: ["quit", "exit", "/quit"])
            welcome_message: Karşılama mesajı
        """
        if exit_commands is None:
            exit_commands = ["quit", "exit", "/quit", "/exit", "q"]
        
        self.start_session()
        
        if welcome_message:
            print(welcome_message)
        
        print(f"Session started: {self.state.session_id}")
        print(f"Exit commands: {', '.join(exit_commands)}")
        print("-" * 50)
        
        try:
            while self.state.is_active:
                try:
                    user_input = input(prompt).strip()
                except EOFError:
                    break
                
                # Boş input
                if not user_input:
                    continue
                
                # Exit command
                if user_input.lower() in exit_commands:
                    print("Goodbye!")
                    break
                
                # Process message
                result = self.process_message(user_input)
                
                if result["success"]:
                    print(f"\nAssistant: {result['response']}")
                    print(f"  [{result['intent']} | {result['confidence']:.1%} | {result['response_time_ms']:.0f}ms]")
                else:
                    print(f"\nError: {result['error']}")
                
                print()
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
        
        finally:
            stats = self.end_session()
            print("-" * 50)
            print(f"Session stats: {stats['turn_count']} turns, "
                  f"{stats['avg_response_time_ms']:.0f}ms avg, "
                  f"{stats['duration_seconds']:.1f}s duration")


def create_sync_handler(
    chat_callback: Callable[[str], Dict[str, Any]],
    log_dir: str = "./logs"
) -> SyncHandler:
    """SyncHandler oluştur"""
    return SyncHandler(chat_callback=chat_callback, log_dir=log_dir)


if __name__ == "__main__":
    # Test için mock chat callback
    def mock_chat(user_input: str) -> Dict[str, Any]:
        return {
            "response": f"Mock response to: {user_input}",
            "intent": "general_chat",
            "confidence": 0.85,
            "adapter": None,
            "memory_hits": 0,
            "tokens": 10
        }
    
    handler = create_sync_handler(mock_chat)
    
    # Manuel test
    result = handler.process_message("Merhaba!")
    print(f"Result: {result}")
    
    stats = handler.get_state()
    print(f"State: {stats}")
    
    handler.end_session()
    print("SyncHandler test completed!")
