"""
EVO-TR Lifecycle Logger
========================
Structured logging sistemi - JSON format ile conversation tracking.

Özellikler:
- JSON formatında log kayıtları
- Log rotasyonu (günlük dosyalar)
- Conversation tracking (session bazlı)
- Performance metrikleri
- Error/warning kategorileri
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import gzip
import shutil


class LogLevel(Enum):
    """Log seviyeleri"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Log kategorileri"""
    SYSTEM = "system"
    CONVERSATION = "conversation"
    ROUTER = "router"
    MEMORY = "memory"
    INFERENCE = "inference"
    LORA = "lora"
    PERFORMANCE = "performance"
    ERROR = "error"


@dataclass
class ConversationEntry:
    """Tek bir konuşma kaydı"""
    timestamp: str
    session_id: str
    turn_id: int
    user_input: str
    assistant_response: str
    intent: str
    confidence: float
    adapter_used: Optional[str]
    memory_hits: int
    response_time_ms: float
    tokens_generated: int
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PerformanceEntry:
    """Performance metrik kaydı"""
    timestamp: str
    session_id: str
    operation: str
    duration_ms: float
    memory_mb: Optional[float] = None
    tokens_per_second: Optional[float] = None
    details: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class EvoTRLogger:
    """
    EVO-TR için merkezi logging sistemi.
    
    Özellikler:
    - JSON formatında structured logging
    - Günlük log rotasyonu
    - Session-based conversation tracking
    - Thread-safe yazma operasyonları
    """
    
    def __init__(
        self,
        log_dir: str = "./logs",
        session_id: Optional[str] = None,
        max_file_size_mb: int = 10,
        compress_old: bool = True
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Session ID
        self.session_id = session_id or self._generate_session_id()
        
        # Settings
        self.max_file_size_mb = max_file_size_mb
        self.compress_old = compress_old
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Conversation tracking
        self.turn_count = 0
        self.session_start = datetime.now()
        
        # Log files
        self._init_log_files()
        
        # Initial log
        self.log_system("Logger initialized", {
            "session_id": self.session_id,
            "log_dir": str(self.log_dir)
        })
    
    def _generate_session_id(self) -> str:
        """Unique session ID oluştur"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
    
    def _init_log_files(self):
        """Log dosyalarını hazırla"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Ana log dosyası
        self.main_log_file = self.log_dir / f"evotr_{today}.jsonl"
        
        # Conversation log dosyası
        self.conv_log_file = self.log_dir / f"conversations_{today}.jsonl"
        
        # Performance log dosyası
        self.perf_log_file = self.log_dir / f"performance_{today}.jsonl"
        
        # Error log dosyası
        self.error_log_file = self.log_dir / f"errors_{today}.jsonl"
        
        # Eski logları rotate et
        self._rotate_logs_if_needed()
    
    def _rotate_logs_if_needed(self):
        """Büyük log dosyalarını rotate et"""
        for log_file in [self.main_log_file, self.conv_log_file, 
                         self.perf_log_file, self.error_log_file]:
            if log_file.exists():
                size_mb = log_file.stat().st_size / (1024 * 1024)
                if size_mb > self.max_file_size_mb:
                    self._rotate_file(log_file)
    
    def _rotate_file(self, log_file: Path):
        """Tek bir log dosyasını rotate et"""
        timestamp = datetime.now().strftime("%H%M%S")
        rotated = log_file.with_suffix(f".{timestamp}.jsonl")
        shutil.move(str(log_file), str(rotated))
        
        if self.compress_old:
            with open(rotated, 'rb') as f_in:
                with gzip.open(str(rotated) + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            rotated.unlink()
    
    def _write_log(self, file_path: Path, entry: Dict):
        """Thread-safe log yazma"""
        with self._lock:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def _create_base_entry(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        details: Optional[Dict] = None
    ) -> Dict:
        """Base log entry oluştur"""
        return {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "level": level.value,
            "category": category.value,
            "message": message,
            "details": details or {}
        }
    
    # ============ General Logging ============
    
    def log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        details: Optional[Dict] = None
    ):
        """Genel log metodu"""
        entry = self._create_base_entry(level, category, message, details)
        self._write_log(self.main_log_file, entry)
        
        # Error seviyesi için ayrı dosyaya da yaz
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self._write_log(self.error_log_file, entry)
    
    def log_debug(self, message: str, details: Optional[Dict] = None):
        self.log(LogLevel.DEBUG, LogCategory.SYSTEM, message, details)
    
    def log_info(self, message: str, details: Optional[Dict] = None):
        self.log(LogLevel.INFO, LogCategory.SYSTEM, message, details)
    
    def log_warning(self, message: str, details: Optional[Dict] = None):
        self.log(LogLevel.WARNING, LogCategory.SYSTEM, message, details)
    
    def log_error(self, message: str, details: Optional[Dict] = None):
        self.log(LogLevel.ERROR, LogCategory.ERROR, message, details)
    
    def log_system(self, message: str, details: Optional[Dict] = None):
        self.log(LogLevel.INFO, LogCategory.SYSTEM, message, details)
    
    # ============ Conversation Logging ============
    
    def log_conversation(
        self,
        user_input: str,
        assistant_response: str,
        intent: str,
        confidence: float,
        adapter_used: Optional[str] = None,
        memory_hits: int = 0,
        response_time_ms: float = 0.0,
        tokens_generated: int = 0,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> ConversationEntry:
        """Konuşma kaydı logla"""
        self.turn_count += 1
        
        entry = ConversationEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            turn_id=self.turn_count,
            user_input=user_input,
            assistant_response=assistant_response,
            intent=intent,
            confidence=confidence,
            adapter_used=adapter_used,
            memory_hits=memory_hits,
            response_time_ms=response_time_ms,
            tokens_generated=tokens_generated,
            success=success,
            error_message=error_message
        )
        
        self._write_log(self.conv_log_file, entry.to_dict())
        
        # Ana loga da özet yaz
        self.log(
            LogLevel.INFO,
            LogCategory.CONVERSATION,
            f"Turn {self.turn_count}: {intent} ({confidence:.2%})",
            {
                "user_preview": user_input[:50] + "..." if len(user_input) > 50 else user_input,
                "response_time_ms": response_time_ms,
                "success": success
            }
        )
        
        return entry
    
    # ============ Performance Logging ============
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        memory_mb: Optional[float] = None,
        tokens_per_second: Optional[float] = None,
        details: Optional[Dict] = None
    ) -> PerformanceEntry:
        """Performance metrik logla"""
        entry = PerformanceEntry(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            operation=operation,
            duration_ms=duration_ms,
            memory_mb=memory_mb,
            tokens_per_second=tokens_per_second,
            details=details
        )
        
        self._write_log(self.perf_log_file, entry.to_dict())
        
        return entry
    
    # ============ Specialized Logging ============
    
    def log_router(self, intent: str, confidence: float, latency_ms: float):
        """Router operasyonu logla"""
        self.log(
            LogLevel.INFO,
            LogCategory.ROUTER,
            f"Classified as {intent}",
            {
                "intent": intent,
                "confidence": confidence,
                "latency_ms": latency_ms
            }
        )
    
    def log_memory(self, operation: str, hits: int, query_preview: str):
        """Memory operasyonu logla"""
        self.log(
            LogLevel.INFO,
            LogCategory.MEMORY,
            f"Memory {operation}: {hits} hits",
            {
                "operation": operation,
                "hits": hits,
                "query_preview": query_preview[:30]
            }
        )
    
    def log_inference(
        self,
        adapter: Optional[str],
        tokens: int,
        duration_ms: float
    ):
        """Inference operasyonu logla"""
        tps = (tokens / duration_ms * 1000) if duration_ms > 0 else 0
        self.log(
            LogLevel.INFO,
            LogCategory.INFERENCE,
            f"Generated {tokens} tokens at {tps:.1f} t/s",
            {
                "adapter": adapter,
                "tokens": tokens,
                "duration_ms": duration_ms,
                "tokens_per_second": tps
            }
        )
        
        self.log_performance(
            "inference",
            duration_ms,
            tokens_per_second=tps,
            details={"adapter": adapter, "tokens": tokens}
        )
    
    def log_lora(self, operation: str, adapter_name: str, details: Optional[Dict] = None):
        """LoRA operasyonu logla"""
        self.log(
            LogLevel.INFO,
            LogCategory.LORA,
            f"LoRA {operation}: {adapter_name}",
            details
        )
    
    # ============ Session Management ============
    
    def get_session_stats(self) -> Dict:
        """Session istatistikleri"""
        duration = (datetime.now() - self.session_start).total_seconds()
        return {
            "session_id": self.session_id,
            "start_time": self.session_start.isoformat(),
            "duration_seconds": duration,
            "total_turns": self.turn_count,
            "turns_per_minute": (self.turn_count / duration * 60) if duration > 0 else 0
        }
    
    def end_session(self):
        """Session'ı sonlandır"""
        stats = self.get_session_stats()
        self.log_system("Session ended", stats)
    
    # ============ Log Reading ============
    
    def read_conversations(
        self,
        date: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Konuşma loglarını oku"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        log_file = self.log_dir / f"conversations_{date}.jsonl"
        if not log_file.exists():
            return []
        
        conversations = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if session_id is None or entry.get("session_id") == session_id:
                        conversations.append(entry)
                        if len(conversations) >= limit:
                            break
                except json.JSONDecodeError:
                    continue
        
        return conversations
    
    def read_errors(
        self,
        date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Error loglarını oku"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        log_file = self.log_dir / f"errors_{date}.jsonl"
        if not log_file.exists():
            return []
        
        errors = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    errors.append(json.loads(line))
                    if len(errors) >= limit:
                        break
                except json.JSONDecodeError:
                    continue
        
        return errors
    
    def get_daily_summary(self, date: Optional[str] = None) -> Dict:
        """Günlük özet rapor"""
        conversations = self.read_conversations(date, limit=10000)
        
        if not conversations:
            return {"date": date, "total_turns": 0}
        
        # İstatistikler
        total_turns = len(conversations)
        successful = sum(1 for c in conversations if c.get("success", True))
        
        # Intent dağılımı
        intent_counts = {}
        for c in conversations:
            intent = c.get("intent", "unknown")
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Response time istatistikleri
        response_times = [c.get("response_time_ms", 0) for c in conversations]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "total_turns": total_turns,
            "successful_turns": successful,
            "success_rate": successful / total_turns if total_turns > 0 else 0,
            "intent_distribution": intent_counts,
            "avg_response_time_ms": avg_response_time,
            "unique_sessions": len(set(c.get("session_id") for c in conversations))
        }


# Convenience function
def create_logger(
    log_dir: str = "./logs",
    session_id: Optional[str] = None
) -> EvoTRLogger:
    """Logger oluştur"""
    return EvoTRLogger(log_dir=log_dir, session_id=session_id)


if __name__ == "__main__":
    # Test
    logger = create_logger()
    
    # Genel log
    logger.log_info("Test message", {"key": "value"})
    
    # Conversation log
    logger.log_conversation(
        user_input="Merhaba, nasılsın?",
        assistant_response="İyiyim, teşekkür ederim!",
        intent="general_chat",
        confidence=0.95,
        adapter_used="tr_chat",
        memory_hits=0,
        response_time_ms=150.5,
        tokens_generated=12
    )
    
    # Performance log
    logger.log_performance(
        operation="inference",
        duration_ms=150.5,
        tokens_per_second=80.0
    )
    
    # Session stats
    stats = logger.get_session_stats()
    print(f"Session stats: {stats}")
    
    # Daily summary
    summary = logger.get_daily_summary()
    print(f"Daily summary: {summary}")
    
    logger.end_session()
    print("Logger test completed!")
