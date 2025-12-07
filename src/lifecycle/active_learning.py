"""
EVO-TR: Active Learning System

Belirsizlik tespiti ve aktif öğrenme mekanizmaları.
Model ne zaman emin olmadığını tespit eder ve yardım ister.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum


class UncertaintyLevel(Enum):
    """Belirsizlik seviyeleri."""
    VERY_LOW = "very_low"      # 0.0 - 0.1
    LOW = "low"                 # 0.1 - 0.3
    MEDIUM = "medium"           # 0.3 - 0.5
    HIGH = "high"               # 0.5 - 0.7
    VERY_HIGH = "very_high"     # 0.7 - 1.0


class UncertaintyType(Enum):
    """Belirsizlik türleri."""
    INTENT_AMBIGUITY = "intent_ambiguity"           # Hangi adapter kullanılmalı?
    LOW_CONFIDENCE = "low_confidence"               # Router düşük güven skoru
    MULTIPLE_INTENTS = "multiple_intents"           # Birden fazla olası intent
    OUT_OF_DOMAIN = "out_of_domain"                 # Bilinen kategorilere uymuyor
    SHORT_QUERY = "short_query"                     # Çok kısa/belirsiz sorgu
    AMBIGUOUS_CONTEXT = "ambiguous_context"         # Bağlam belirsiz
    CONFLICTING_SIGNALS = "conflicting_signals"     # Çelişkili sinyaller


@dataclass
class UncertaintyRecord:
    """Belirsizlik kaydı."""
    id: str
    timestamp: str
    user_message: str
    uncertainty_type: str
    uncertainty_level: str
    confidence_score: float
    top_intents: List[Dict[str, float]]  # [{"intent": "x", "score": 0.8}, ...]
    details: Dict[str, Any]
    action_taken: Optional[str] = None
    user_response: Optional[str] = None
    resolved: bool = False


class UncertaintyDetector:
    """Belirsizlik tespit sistemi."""
    
    # Eşik değerleri
    CONFIDENCE_THRESHOLD = 0.6      # Bu altında belirsiz kabul edilir
    AMBIGUITY_MARGIN = 0.15         # İlk iki intent arası bu kadar yakınsa belirsiz
    MIN_QUERY_LENGTH = 5            # Bu altında çok kısa kabul edilir
    OOD_THRESHOLD = 0.4             # Out of domain eşiği
    
    def __init__(self, log_path: str = "./logs/active_learning"):
        self.log_path = Path(log_path)
        self.log_path.mkdir(parents=True, exist_ok=True)
        self.uncertainty_log: List[UncertaintyRecord] = []
        
        print(f"✅ UncertaintyDetector hazır | Log: {self.log_path}")
    
    def detect_uncertainty(
        self,
        user_message: str,
        router_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[UncertaintyRecord]]:
        """
        Belirsizlik tespit et.
        
        Returns:
            (is_uncertain, uncertainty_record)
        """
        context = context or {}
        
        # Router sonuçlarını al
        top_intent = router_result.get("intent", "general")
        confidence = router_result.get("confidence", 0.0)
        all_scores = router_result.get("all_scores", {})
        
        # Tüm belirsizlik kontrollerini yap
        uncertainties = []
        
        # 1. Düşük güven skoru
        if confidence < self.CONFIDENCE_THRESHOLD:
            uncertainties.append({
                "type": UncertaintyType.LOW_CONFIDENCE,
                "score": 1.0 - confidence,
                "details": {"confidence": confidence, "threshold": self.CONFIDENCE_THRESHOLD}
            })
        
        # 2. Çoklu intent (belirsizlik marjı)
        if len(all_scores) >= 2:
            sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_scores) >= 2:
                top1_score = sorted_scores[0][1]
                top2_score = sorted_scores[1][1]
                margin = top1_score - top2_score
                
                if margin < self.AMBIGUITY_MARGIN:
                    uncertainties.append({
                        "type": UncertaintyType.MULTIPLE_INTENTS,
                        "score": 1.0 - margin,
                        "details": {
                            "top_intents": sorted_scores[:3],
                            "margin": margin
                        }
                    })
        
        # 3. Kısa sorgu
        word_count = len(user_message.split())
        if word_count < self.MIN_QUERY_LENGTH:
            uncertainties.append({
                "type": UncertaintyType.SHORT_QUERY,
                "score": 1.0 - (word_count / self.MIN_QUERY_LENGTH),
                "details": {"word_count": word_count, "threshold": self.MIN_QUERY_LENGTH}
            })
        
        # 4. Out of domain (tüm skorlar düşük)
        if all_scores:
            max_score = max(all_scores.values())
            if max_score < self.OOD_THRESHOLD:
                uncertainties.append({
                    "type": UncertaintyType.OUT_OF_DOMAIN,
                    "score": 1.0 - max_score,
                    "details": {"max_score": max_score, "threshold": self.OOD_THRESHOLD}
                })
        
        # Belirsizlik var mı?
        if not uncertainties:
            return False, None
        
        # En yüksek belirsizliği bul
        primary_uncertainty = max(uncertainties, key=lambda x: x["score"])
        
        # Belirsizlik seviyesini belirle
        avg_uncertainty = sum(u["score"] for u in uncertainties) / len(uncertainties)
        uncertainty_level = self._score_to_level(avg_uncertainty)
        
        # Top intents listesi
        top_intents = [
            {"intent": intent, "score": round(score, 3)}
            for intent, score in sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Record oluştur
        record = UncertaintyRecord(
            id=f"unc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(user_message) % 10000:04d}",
            timestamp=datetime.now().isoformat(),
            user_message=user_message,
            uncertainty_type=primary_uncertainty["type"].value,
            uncertainty_level=uncertainty_level.value,
            confidence_score=confidence,
            top_intents=top_intents,
            details={
                "all_uncertainties": [
                    {"type": u["type"].value, "score": u["score"], **u["details"]}
                    for u in uncertainties
                ],
                "context": context
            }
        )
        
        self.uncertainty_log.append(record)
        
        return True, record
    
    def _score_to_level(self, score: float) -> UncertaintyLevel:
        """Skoru belirsizlik seviyesine çevir."""
        if score < 0.1:
            return UncertaintyLevel.VERY_LOW
        elif score < 0.3:
            return UncertaintyLevel.LOW
        elif score < 0.5:
            return UncertaintyLevel.MEDIUM
        elif score < 0.7:
            return UncertaintyLevel.HIGH
        else:
            return UncertaintyLevel.VERY_HIGH
    
    def generate_clarification_prompt(self, record: UncertaintyRecord) -> str:
        """Belirsizlik için açıklama sorusu oluştur."""
        uncertainty_type = record.uncertainty_type
        details = record.details
        top_intents = record.top_intents
        
        if uncertainty_type == UncertaintyType.LOW_CONFIDENCE.value:
            return (
                "Sorunuzu tam olarak anlayamadım. "
                "Lütfen daha detaylı açıklar mısınız?"
            )
        
        elif uncertainty_type == UncertaintyType.MULTIPLE_INTENTS.value:
            # En iyi 2-3 intent'i göster
            options = []
            for i, intent_info in enumerate(top_intents[:3], 1):
                intent = intent_info["intent"]
                intent_desc = self._intent_to_description(intent)
                options.append(f"{i}. {intent_desc}")
            
            options_text = "\n".join(options)
            return (
                f"Sorunuz birden fazla konuyla ilgili olabilir:\n{options_text}\n\n"
                "Hangisi hakkında yardım istiyorsunuz?"
            )
        
        elif uncertainty_type == UncertaintyType.SHORT_QUERY.value:
            return (
                "Sorunuz biraz kısa. "
                "Ne hakkında yardım istediğinizi daha detaylı açıklar mısınız?"
            )
        
        elif uncertainty_type == UncertaintyType.OUT_OF_DOMAIN.value:
            return (
                "Bu konu hakkında yeterli bilgim yok gibi görünüyor. "
                "Türkçe sohbet, Python programlama, matematik, bilim veya tarih "
                "konularında size daha iyi yardımcı olabilirim."
            )
        
        else:
            return (
                "Sorunuzu daha iyi anlamak istiyorum. "
                "Lütfen ne hakkında yardım istediğinizi açıklar mısınız?"
            )
    
    def _intent_to_description(self, intent: str) -> str:
        """Intent'i kullanıcı dostu açıklamaya çevir."""
        descriptions = {
            "turkish_chat": "🇹🇷 Türkçe sohbet",
            "coding_python": "🐍 Python programlama",
            "math": "🧮 Matematik",
            "science": "🔬 Bilim",
            "history": "📜 Tarih",
            "greeting": "👋 Selamlaşma",
            "farewell": "👋 Vedalaşma",
            "help": "❓ Yardım",
            "about": "ℹ️ Hakkında",
            "general": "💬 Genel sohbet"
        }
        return descriptions.get(intent, f"📌 {intent}")
    
    def resolve_uncertainty(
        self,
        record_id: str,
        user_response: str,
        resolved_intent: Optional[str] = None
    ) -> bool:
        """Belirsizliği çöz ve kaydet."""
        for record in self.uncertainty_log:
            if record.id == record_id:
                record.user_response = user_response
                record.resolved = True
                record.action_taken = f"resolved_to:{resolved_intent}" if resolved_intent else "user_clarified"
                return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Belirsizlik istatistikleri."""
        total = len(self.uncertainty_log)
        if total == 0:
            return {"total": 0, "message": "Henüz belirsizlik kaydı yok"}
        
        resolved = sum(1 for r in self.uncertainty_log if r.resolved)
        
        # Tip dağılımı
        type_counts = {}
        for record in self.uncertainty_log:
            utype = record.uncertainty_type
            type_counts[utype] = type_counts.get(utype, 0) + 1
        
        # Seviye dağılımı
        level_counts = {}
        for record in self.uncertainty_log:
            level = record.uncertainty_level
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            "total": total,
            "resolved": resolved,
            "resolution_rate": round(resolved / total * 100, 1),
            "by_type": type_counts,
            "by_level": level_counts,
            "avg_confidence": round(
                sum(r.confidence_score for r in self.uncertainty_log) / total, 3
            )
        }
    
    def save_log(self, filename: Optional[str] = None):
        """Log'u dosyaya kaydet."""
        if filename is None:
            filename = f"uncertainty_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        filepath = self.log_path / filename
        
        with open(filepath, "a", encoding="utf-8") as f:
            for record in self.uncertainty_log:
                f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        
        print(f"✅ {len(self.uncertainty_log)} belirsizlik kaydı kaydedildi: {filepath}")
        return filepath


class ActiveLearningManager:
    """
    Active Learning yöneticisi.
    
    Belirsiz örnekleri toplar ve eğitim için aday olarak işaretler.
    """
    
    def __init__(
        self,
        uncertainty_detector: Optional[UncertaintyDetector] = None,
        candidate_path: str = "./data/active_learning"
    ):
        self.detector = uncertainty_detector or UncertaintyDetector()
        self.candidate_path = Path(candidate_path)
        self.candidate_path.mkdir(parents=True, exist_ok=True)
        
        self.training_candidates: List[Dict[str, Any]] = []
        
        print(f"✅ ActiveLearningManager hazır | Candidates: {self.candidate_path}")
    
    def process_interaction(
        self,
        user_message: str,
        model_response: str,
        router_result: Dict[str, Any],
        feedback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Etkileşimi işle ve active learning için değerlendir.
        
        Returns:
            {
                "is_uncertain": bool,
                "uncertainty_record": Optional[UncertaintyRecord],
                "is_training_candidate": bool,
                "clarification_prompt": Optional[str]
            }
        """
        result = {
            "is_uncertain": False,
            "uncertainty_record": None,
            "is_training_candidate": False,
            "clarification_prompt": None
        }
        
        # Belirsizlik kontrolü
        is_uncertain, uncertainty_record = self.detector.detect_uncertainty(
            user_message=user_message,
            router_result=router_result
        )
        
        if is_uncertain:
            result["is_uncertain"] = True
            result["uncertainty_record"] = uncertainty_record
            result["clarification_prompt"] = self.detector.generate_clarification_prompt(
                uncertainty_record
            )
        
        # Eğitim adayı mı?
        if self._should_be_training_candidate(
            is_uncertain=is_uncertain,
            feedback=feedback,
            router_result=router_result
        ):
            candidate = {
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "model_response": model_response,
                "router_result": router_result,
                "is_uncertain": is_uncertain,
                "uncertainty_type": uncertainty_record.uncertainty_type if uncertainty_record else None,
                "feedback": feedback
            }
            self.training_candidates.append(candidate)
            result["is_training_candidate"] = True
        
        return result
    
    def _should_be_training_candidate(
        self,
        is_uncertain: bool,
        feedback: Optional[Dict[str, Any]],
        router_result: Dict[str, Any]
    ) -> bool:
        """Eğitim adayı olmalı mı?"""
        # Belirsiz örnekler her zaman aday
        if is_uncertain:
            return True
        
        # Olumsuz feedback varsa aday
        if feedback:
            ftype = feedback.get("feedback_type", "")
            if ftype in ["thumbs_down", "edit", "retry", "report"]:
                return True
        
        # Düşük güvenle doğru yapıldıysa ilginç örnek
        confidence = router_result.get("confidence", 0.0)
        if confidence < 0.7:
            return True
        
        return False
    
    def export_training_candidates(
        self,
        min_samples: int = 10,
        filename: Optional[str] = None
    ) -> Optional[Path]:
        """Eğitim adaylarını dışa aktar."""
        if len(self.training_candidates) < min_samples:
            print(f"⚠️ Yeterli aday yok ({len(self.training_candidates)}/{min_samples})")
            return None
        
        if filename is None:
            filename = f"candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        filepath = self.candidate_path / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            for candidate in self.training_candidates:
                f.write(json.dumps(candidate, ensure_ascii=False) + "\n")
        
        print(f"✅ {len(self.training_candidates)} aday dışa aktarıldı: {filepath}")
        return filepath
    
    def get_candidate_stats(self) -> Dict[str, Any]:
        """Aday istatistikleri."""
        total = len(self.training_candidates)
        if total == 0:
            return {"total": 0, "message": "Henüz aday yok"}
        
        uncertain_count = sum(1 for c in self.training_candidates if c.get("is_uncertain"))
        feedback_count = sum(1 for c in self.training_candidates if c.get("feedback"))
        
        # Uncertainty type dağılımı
        type_counts = {}
        for candidate in self.training_candidates:
            utype = candidate.get("uncertainty_type", "none")
            type_counts[utype] = type_counts.get(utype, 0) + 1
        
        return {
            "total": total,
            "uncertain": uncertain_count,
            "with_feedback": feedback_count,
            "by_uncertainty_type": type_counts,
            "ready_for_training": total >= 10
        }


# Test
if __name__ == "__main__":
    print("=" * 50)
    print("Active Learning Test")
    print("=" * 50)
    
    # Detector test
    detector = UncertaintyDetector()
    
    # Test 1: Düşük güven
    print("\n1. Düşük güven testi:")
    result = detector.detect_uncertainty(
        user_message="bu nedir?",
        router_result={
            "intent": "general",
            "confidence": 0.35,
            "all_scores": {"general": 0.35, "help": 0.30, "turkish_chat": 0.20}
        }
    )
    print(f"   Belirsiz: {result[0]}")
    if result[1]:
        print(f"   Tip: {result[1].uncertainty_type}")
        print(f"   Clarification: {detector.generate_clarification_prompt(result[1])}")
    
    # Test 2: Çoklu intent
    print("\n2. Çoklu intent testi:")
    result = detector.detect_uncertainty(
        user_message="Python'da pi sayısını nasıl hesaplarım?",
        router_result={
            "intent": "coding_python",
            "confidence": 0.75,
            "all_scores": {"coding_python": 0.42, "math": 0.38, "science": 0.15}
        }
    )
    print(f"   Belirsiz: {result[0]}")
    if result[1]:
        print(f"   Tip: {result[1].uncertainty_type}")
        print(f"   Clarification: {detector.generate_clarification_prompt(result[1])}")
    
    # Test 3: Kısa sorgu
    print("\n3. Kısa sorgu testi:")
    result = detector.detect_uncertainty(
        user_message="kod?",
        router_result={
            "intent": "coding_python",
            "confidence": 0.55,
            "all_scores": {"coding_python": 0.55, "help": 0.25}
        }
    )
    print(f"   Belirsiz: {result[0]}")
    if result[1]:
        print(f"   Tip: {result[1].uncertainty_type}")
    
    # Test 4: Emin sorgu (belirsizlik yok)
    print("\n4. Emin sorgu testi:")
    result = detector.detect_uncertainty(
        user_message="Python'da bir liste nasıl oluşturulur ve elemanları nasıl eklenir?",
        router_result={
            "intent": "coding_python",
            "confidence": 0.92,
            "all_scores": {"coding_python": 0.92, "help": 0.05}
        }
    )
    print(f"   Belirsiz: {result[0]}")
    
    # İstatistikler
    print("\n📊 İstatistikler:")
    stats = detector.get_statistics()
    print(f"   Toplam: {stats.get('total', 0)}")
    print(f"   Ortalama güven: {stats.get('avg_confidence', 0)}")
    
    # Active Learning Manager test
    print("\n" + "=" * 50)
    print("Active Learning Manager Test")
    print("=" * 50)
    
    manager = ActiveLearningManager(uncertainty_detector=detector)
    
    # İşlem testi
    result = manager.process_interaction(
        user_message="bu nasıl yapılır?",
        model_response="Neyi nasıl yapmak istediğinizi belirtir misiniz?",
        router_result={
            "intent": "help",
            "confidence": 0.45,
            "all_scores": {"help": 0.45, "general": 0.40}
        },
        feedback={"feedback_type": "thumbs_down"}
    )
    
    print(f"\nİşlem sonucu:")
    print(f"   Belirsiz: {result['is_uncertain']}")
    print(f"   Eğitim adayı: {result['is_training_candidate']}")
    if result['clarification_prompt']:
        print(f"   Clarification: {result['clarification_prompt']}")
    
    # Aday istatistikleri
    print("\n📊 Aday istatistikleri:")
    candidate_stats = manager.get_candidate_stats()
    print(f"   Toplam aday: {candidate_stats.get('total', 0)}")
    
    print("\n✅ Test tamamlandı!")
