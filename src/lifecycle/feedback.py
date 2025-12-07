"""
EVO-TR: Feedback Collection System

Kullanıcı geri bildirimlerini toplama ve yönetme.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib


class FeedbackType(Enum):
    """Feedback türleri."""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    EDIT = "edit"
    RETRY = "retry"
    REPORT = "report"


class FeedbackCategory(Enum):
    """Feedback kategorileri."""
    HELPFUL = "helpful"
    ACCURATE = "accurate"
    IRRELEVANT = "irrelevant"
    INCORRECT = "incorrect"
    OFFENSIVE = "offensive"
    TOO_LONG = "too_long"
    TOO_SHORT = "too_short"
    OTHER = "other"


@dataclass
class FeedbackEntry:
    """Tek bir feedback kaydı."""
    id: Optional[str] = None
    session_id: str = ""
    message_id: str = ""
    user_message: str = ""
    assistant_response: str = ""
    intent: str = ""
    adapter_used: str = ""
    confidence: float = 0.0
    feedback_type: str = ""  # FeedbackType value
    feedback_category: Optional[str] = None  # FeedbackCategory value
    rating: Optional[int] = None  # 1-5 scale
    comment: Optional[str] = None
    corrected_response: Optional[str] = None  # User correction
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.id is None:
            # Generate unique ID
            content = f"{self.session_id}:{self.message_id}:{datetime.now().isoformat()}"
            self.id = hashlib.md5(content.encode()).hexdigest()[:16]
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class FeedbackDatabase:
    """SQLite tabanlı feedback veritabanı."""
    
    def __init__(self, db_path: str = "./data/feedback.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Veritabanı tablolarını oluştur."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Feedback tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                intent TEXT,
                adapter_used TEXT,
                confidence REAL,
                feedback_type TEXT NOT NULL,
                feedback_category TEXT,
                rating INTEGER,
                comment TEXT,
                corrected_response TEXT,
                timestamp TEXT NOT NULL,
                processed INTEGER DEFAULT 0,
                used_for_training INTEGER DEFAULT 0
            )
        """)
        
        # İndeksler
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session ON feedback(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_intent ON feedback(intent)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processed ON feedback(processed)")
        
        # Aggregated stats tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_stats (
                date TEXT PRIMARY KEY,
                total_count INTEGER DEFAULT 0,
                positive_count INTEGER DEFAULT 0,
                negative_count INTEGER DEFAULT 0,
                avg_confidence REAL,
                top_intents TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        print(f"✅ FeedbackDatabase hazır | Path: {self.db_path}")
    
    def add_feedback(self, entry: FeedbackEntry) -> str:
        """Feedback ekle."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO feedback (
                id, session_id, message_id, user_message, assistant_response,
                intent, adapter_used, confidence, feedback_type, feedback_category,
                rating, comment, corrected_response, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.id, entry.session_id, entry.message_id,
            entry.user_message, entry.assistant_response,
            entry.intent, entry.adapter_used, entry.confidence,
            entry.feedback_type, entry.feedback_category,
            entry.rating, entry.comment, entry.corrected_response,
            entry.timestamp
        ))
        
        conn.commit()
        conn.close()
        
        return entry.id
    
    def get_feedback(self, feedback_id: str) -> Optional[FeedbackEntry]:
        """ID ile feedback al."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM feedback WHERE id = ?", (feedback_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_entry(row)
        return None
    
    def get_session_feedback(self, session_id: str) -> List[FeedbackEntry]:
        """Session'a ait tüm feedback'leri al."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM feedback WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_entry(row) for row in rows]
    
    def get_unprocessed_feedback(self, limit: int = 100) -> List[FeedbackEntry]:
        """İşlenmemiş feedback'leri al."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM feedback WHERE processed = 0 ORDER BY timestamp LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_entry(row) for row in rows]
    
    def get_negative_feedback(self, limit: int = 100) -> List[FeedbackEntry]:
        """Negatif feedback'leri al (eğitim için)."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM feedback 
            WHERE feedback_type IN ('thumbs_down', 'report') 
            AND used_for_training = 0
            ORDER BY timestamp 
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_entry(row) for row in rows]
    
    def get_corrected_responses(self, limit: int = 100) -> List[FeedbackEntry]:
        """Düzeltilmiş yanıtları al (eğitim için çok değerli)."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM feedback 
            WHERE corrected_response IS NOT NULL 
            AND corrected_response != ''
            AND used_for_training = 0
            ORDER BY timestamp 
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_entry(row) for row in rows]
    
    def mark_as_processed(self, feedback_ids: List[str]) -> int:
        """Feedback'leri işlenmiş olarak işaretle."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        placeholders = ",".join(["?" for _ in feedback_ids])
        cursor.execute(
            f"UPDATE feedback SET processed = 1 WHERE id IN ({placeholders})",
            feedback_ids
        )
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected
    
    def mark_as_used_for_training(self, feedback_ids: List[str]) -> int:
        """Feedback'leri eğitimde kullanıldı olarak işaretle."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        placeholders = ",".join(["?" for _ in feedback_ids])
        cursor.execute(
            f"UPDATE feedback SET used_for_training = 1 WHERE id IN ({placeholders})",
            feedback_ids
        )
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected
    
    def get_stats(self) -> Dict[str, Any]:
        """Genel istatistikler."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM feedback")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback_type = 'thumbs_up'")
        positive = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback_type = 'thumbs_down'")
        negative = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM feedback WHERE corrected_response IS NOT NULL")
        corrections = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(confidence) FROM feedback")
        avg_confidence = cursor.fetchone()[0] or 0.0
        
        # By intent
        cursor.execute("""
            SELECT intent, COUNT(*) as cnt 
            FROM feedback 
            GROUP BY intent 
            ORDER BY cnt DESC 
            LIMIT 5
        """)
        top_intents = cursor.fetchall()
        
        # By feedback type
        cursor.execute("""
            SELECT feedback_type, COUNT(*) as cnt 
            FROM feedback 
            GROUP BY feedback_type
        """)
        by_type = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "corrections": corrections,
            "positive_rate": positive / total if total > 0 else 0,
            "avg_confidence": round(avg_confidence, 3),
            "top_intents": dict(top_intents),
            "by_type": by_type
        }
    
    def _row_to_entry(self, row) -> FeedbackEntry:
        """Database row'unu FeedbackEntry'ye çevir."""
        return FeedbackEntry(
            id=row[0],
            session_id=row[1],
            message_id=row[2],
            user_message=row[3],
            assistant_response=row[4],
            intent=row[5],
            adapter_used=row[6],
            confidence=row[7],
            feedback_type=row[8],
            feedback_category=row[9],
            rating=row[10],
            comment=row[11],
            corrected_response=row[12],
            timestamp=row[13]
        )


class FeedbackCollector:
    """
    Feedback toplama yöneticisi.
    
    Web API ve Orchestrator ile entegre çalışır.
    """
    
    def __init__(self, db_path: str = "./data/feedback.db"):
        self.db = FeedbackDatabase(db_path)
        self._session_id = None
    
    def set_session(self, session_id: str):
        """Aktif session'ı ayarla."""
        self._session_id = session_id
    
    def collect_thumbs_up(
        self,
        message_id: str,
        user_message: str,
        assistant_response: str,
        intent: str = "",
        adapter_used: str = "",
        confidence: float = 0.0
    ) -> str:
        """Pozitif feedback topla."""
        entry = FeedbackEntry(
            session_id=self._session_id or "default",
            message_id=message_id,
            user_message=user_message,
            assistant_response=assistant_response,
            intent=intent,
            adapter_used=adapter_used,
            confidence=confidence,
            feedback_type=FeedbackType.THUMBS_UP.value
        )
        return self.db.add_feedback(entry)
    
    def collect_thumbs_down(
        self,
        message_id: str,
        user_message: str,
        assistant_response: str,
        intent: str = "",
        adapter_used: str = "",
        confidence: float = 0.0,
        category: Optional[str] = None,
        comment: Optional[str] = None
    ) -> str:
        """Negatif feedback topla."""
        entry = FeedbackEntry(
            session_id=self._session_id or "default",
            message_id=message_id,
            user_message=user_message,
            assistant_response=assistant_response,
            intent=intent,
            adapter_used=adapter_used,
            confidence=confidence,
            feedback_type=FeedbackType.THUMBS_DOWN.value,
            feedback_category=category,
            comment=comment
        )
        return self.db.add_feedback(entry)
    
    def collect_correction(
        self,
        message_id: str,
        user_message: str,
        assistant_response: str,
        corrected_response: str,
        intent: str = "",
        adapter_used: str = "",
        confidence: float = 0.0
    ) -> str:
        """Düzeltme feedback'i topla."""
        entry = FeedbackEntry(
            session_id=self._session_id or "default",
            message_id=message_id,
            user_message=user_message,
            assistant_response=assistant_response,
            intent=intent,
            adapter_used=adapter_used,
            confidence=confidence,
            feedback_type=FeedbackType.EDIT.value,
            corrected_response=corrected_response
        )
        return self.db.add_feedback(entry)
    
    def collect_retry(
        self,
        message_id: str,
        user_message: str,
        assistant_response: str,
        intent: str = "",
        adapter_used: str = "",
        confidence: float = 0.0
    ) -> str:
        """Retry (implicit negatif) feedback topla."""
        entry = FeedbackEntry(
            session_id=self._session_id or "default",
            message_id=message_id,
            user_message=user_message,
            assistant_response=assistant_response,
            intent=intent,
            adapter_used=adapter_used,
            confidence=confidence,
            feedback_type=FeedbackType.RETRY.value
        )
        return self.db.add_feedback(entry)
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri al."""
        return self.db.get_stats()
    
    def get_training_candidates(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Eğitim için aday verileri al.
        
        Öncelik:
        1. Düzeltilmiş yanıtlar (en değerli)
        2. Negatif feedback'ler (iyileştirme için)
        """
        candidates = []
        
        # Düzeltilmiş yanıtlar
        corrections = self.db.get_corrected_responses(limit // 2)
        for entry in corrections:
            candidates.append({
                "type": "correction",
                "priority": 1,  # Highest
                "user_message": entry.user_message,
                "original_response": entry.assistant_response,
                "corrected_response": entry.corrected_response,
                "intent": entry.intent,
                "feedback_id": entry.id
            })
        
        # Negatif feedback'ler
        negatives = self.db.get_negative_feedback(limit // 2)
        for entry in negatives:
            candidates.append({
                "type": "negative",
                "priority": 2,
                "user_message": entry.user_message,
                "response": entry.assistant_response,
                "category": entry.feedback_category,
                "comment": entry.comment,
                "intent": entry.intent,
                "feedback_id": entry.id
            })
        
        # Önceliğe göre sırala
        candidates.sort(key=lambda x: x["priority"])
        
        return candidates


# Test
if __name__ == "__main__":
    print("🧪 Feedback System Testi\n")
    
    # Test database
    db = FeedbackDatabase("./data/test_feedback.db")
    collector = FeedbackCollector("./data/test_feedback.db")
    collector.set_session("test_session_001")
    
    # Test feedback'ler
    print("1. Thumbs Up ekleniyor...")
    id1 = collector.collect_thumbs_up(
        message_id="msg_001",
        user_message="Python'da liste nasıl sıralanır?",
        assistant_response="Python'da liste sıralamak için sorted() veya list.sort() kullanabilirsiniz.",
        intent="code_python",
        adapter_used="python_coder",
        confidence=0.85
    )
    print(f"   ✅ ID: {id1}")
    
    print("\n2. Thumbs Down ekleniyor...")
    id2 = collector.collect_thumbs_down(
        message_id="msg_002",
        user_message="2 + 2 kaç eder?",
        assistant_response="5",
        intent="code_math",
        adapter_used="math_expert",
        confidence=0.90,
        category="incorrect",
        comment="Yanlış cevap, doğrusu 4"
    )
    print(f"   ✅ ID: {id2}")
    
    print("\n3. Düzeltme ekleniyor...")
    id3 = collector.collect_correction(
        message_id="msg_003",
        user_message="Atatürk ne zaman doğdu?",
        assistant_response="Atatürk 1880'de doğdu.",
        corrected_response="Atatürk 1881'de Selanik'te doğdu.",
        intent="history",
        adapter_used="history_expert",
        confidence=0.75
    )
    print(f"   ✅ ID: {id3}")
    
    print("\n4. İstatistikler:")
    stats = collector.get_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    print("\n5. Eğitim adayları:")
    candidates = collector.get_training_candidates(10)
    for c in candidates:
        print(f"   - [{c['type']}] {c['user_message'][:50]}...")
    
    print("\n✅ Test tamamlandı!")
