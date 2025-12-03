"""
EVO-TR Async Processor
=======================
Gece modu - Log analizi, bilgi çıkarımı ve self-improvement.

Özellikler:
- Günlük log analizi
- Başarısız yanıtların tespiti
- Pattern/trend analizi
- Bilgi çıkarımı (facts extraction)
- ChromaDB'ye yeni bilgi yazımı
- Eğitim verisi önerileri
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import Counter
from enum import Enum

from .logger import EvoTRLogger, create_logger


class AnalysisType(Enum):
    """Analiz türleri"""
    DAILY_SUMMARY = "daily_summary"
    ERROR_ANALYSIS = "error_analysis"
    PATTERN_DETECTION = "pattern_detection"
    KNOWLEDGE_EXTRACTION = "knowledge_extraction"
    TRAINING_SUGGESTIONS = "training_suggestions"


@dataclass
class FailedConversation:
    """Başarısız konuşma kaydı"""
    timestamp: str
    session_id: str
    user_input: str
    error_message: str
    intent: str
    confidence: float
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "user_input": self.user_input,
            "error_message": self.error_message,
            "intent": self.intent,
            "confidence": self.confidence
        }


@dataclass
class ConversationPattern:
    """Konuşma pattern'i"""
    pattern_type: str
    description: str
    frequency: int
    examples: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "pattern_type": self.pattern_type,
            "description": self.description,
            "frequency": self.frequency,
            "examples": self.examples[:5]  # İlk 5 örnek
        }


@dataclass
class ExtractedFact:
    """Çıkarılan bilgi"""
    fact_text: str
    source_query: str
    confidence: float
    category: str
    
    def to_dict(self) -> Dict:
        return {
            "fact_text": self.fact_text,
            "source_query": self.source_query,
            "confidence": self.confidence,
            "category": self.category
        }


@dataclass
class TrainingSuggestion:
    """Eğitim verisi önerisi"""
    category: str
    reason: str
    example_queries: List[str]
    priority: int  # 1-5 (5 en yüksek)
    
    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "reason": self.reason,
            "example_queries": self.example_queries,
            "priority": self.priority
        }


@dataclass
class AnalysisReport:
    """Analiz raporu"""
    date: str
    analysis_type: str
    generated_at: str
    summary: Dict[str, Any]
    details: Dict[str, Any]
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "date": self.date,
            "analysis_type": self.analysis_type,
            "generated_at": self.generated_at,
            "summary": self.summary,
            "details": self.details,
            "recommendations": self.recommendations
        }


class AsyncProcessor:
    """
    Async (Gece) modu processor.
    
    Görevler:
    - Günlük logları analiz et
    - Başarısız yanıtları tespit et
    - Pattern ve trendleri bul
    - Yeni bilgi çıkar
    - Eğitim verisi öner
    """
    
    def __init__(
        self,
        log_dir: str = "./logs",
        memory_handler = None,
        output_dir: str = "./logs/analysis"
    ):
        self.log_dir = Path(log_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_handler = memory_handler
        self.logger = create_logger(log_dir)
        
        # Analysis results
        self.reports: List[AnalysisReport] = []
    
    # ============ Log Reading ============
    
    def _read_jsonl(self, file_path: Path) -> List[Dict]:
        """JSONL dosyasını oku"""
        if not file_path.exists():
            return []
        
        entries = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries
    
    def get_conversations(self, date: str) -> List[Dict]:
        """Belirli bir günün konuşmalarını al"""
        file_path = self.log_dir / f"conversations_{date}.jsonl"
        return self._read_jsonl(file_path)
    
    def get_errors(self, date: str) -> List[Dict]:
        """Belirli bir günün hatalarını al"""
        file_path = self.log_dir / f"errors_{date}.jsonl"
        return self._read_jsonl(file_path)
    
    def get_main_logs(self, date: str) -> List[Dict]:
        """Belirli bir günün ana loglarını al"""
        file_path = self.log_dir / f"evotr_{date}.jsonl"
        return self._read_jsonl(file_path)
    
    # ============ Analysis Functions ============
    
    def analyze_daily_logs(self, date: Optional[str] = None) -> AnalysisReport:
        """
        Günlük log analizi.
        
        Analiz edilen metrikler:
        - Toplam konuşma sayısı
        - Başarı oranı
        - Intent dağılımı
        - Ortalama response time
        - Error pattern'leri
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        conversations = self.get_conversations(date)
        errors = self.get_errors(date)
        
        # Temel istatistikler
        total = len(conversations)
        successful = sum(1 for c in conversations if c.get("success", True))
        failed = total - successful
        
        # Intent dağılımı
        intent_counts = Counter(c.get("intent", "unknown") for c in conversations)
        
        # Response time istatistikleri
        response_times = [c.get("response_time_ms", 0) for c in conversations]
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        max_response = max(response_times) if response_times else 0
        
        # Adapter kullanımı
        adapter_counts = Counter(c.get("adapter_used") for c in conversations)
        
        # Session sayısı
        sessions = set(c.get("session_id") for c in conversations)
        
        summary = {
            "total_conversations": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "unique_sessions": len(sessions),
            "avg_response_time_ms": avg_response,
            "max_response_time_ms": max_response,
            "error_count": len(errors)
        }
        
        details = {
            "intent_distribution": dict(intent_counts),
            "adapter_usage": dict(adapter_counts),
            "hourly_distribution": self._get_hourly_distribution(conversations)
        }
        
        recommendations = self._generate_recommendations(summary, details, conversations)
        
        report = AnalysisReport(
            date=date,
            analysis_type=AnalysisType.DAILY_SUMMARY.value,
            generated_at=datetime.now().isoformat(),
            summary=summary,
            details=details,
            recommendations=recommendations
        )
        
        self.reports.append(report)
        self._save_report(report)
        
        return report
    
    def _get_hourly_distribution(self, conversations: List[Dict]) -> Dict[int, int]:
        """Saatlik dağılım"""
        hourly = Counter()
        for c in conversations:
            try:
                ts = datetime.fromisoformat(c.get("timestamp", ""))
                hourly[ts.hour] += 1
            except:
                pass
        return dict(sorted(hourly.items()))
    
    def _generate_recommendations(
        self,
        summary: Dict,
        details: Dict,
        conversations: List[Dict]
    ) -> List[str]:
        """Öneriler oluştur"""
        recommendations = []
        
        # Başarı oranı düşükse
        if summary.get("success_rate", 1) < 0.9:
            recommendations.append(
                f"Başarı oranı düşük ({summary['success_rate']:.1%}). "
                "Error loglarını inceleyip hata pattern'lerini tespit edin."
            )
        
        # Response time yüksekse
        if summary.get("avg_response_time_ms", 0) > 2000:
            recommendations.append(
                f"Ortalama yanıt süresi yüksek ({summary['avg_response_time_ms']:.0f}ms). "
                "Model cache'ini veya batch size'ı optimize edin."
            )
        
        # Belirli intent çok düşükse
        intents = details.get("intent_distribution", {})
        total = sum(intents.values())
        if total > 0:
            for intent, count in intents.items():
                if count / total < 0.05 and intent not in ["error", "unknown"]:
                    recommendations.append(
                        f"'{intent}' kategorisi az kullanılıyor (%{count/total*100:.1f}). "
                        "Router eşiklerini kontrol edin."
                    )
        
        # Genel öneri
        if not recommendations:
            recommendations.append("Sistem stabil çalışıyor. Düzenli izlemeye devam edin.")
        
        return recommendations
    
    def find_failed_conversations(self, date: Optional[str] = None) -> List[FailedConversation]:
        """Başarısız konuşmaları bul"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        conversations = self.get_conversations(date)
        
        failed = []
        for c in conversations:
            if not c.get("success", True):
                failed.append(FailedConversation(
                    timestamp=c.get("timestamp", ""),
                    session_id=c.get("session_id", ""),
                    user_input=c.get("user_input", ""),
                    error_message=c.get("error_message", "Unknown error"),
                    intent=c.get("intent", "unknown"),
                    confidence=c.get("confidence", 0.0)
                ))
        
        return failed
    
    def detect_patterns(self, date: Optional[str] = None) -> List[ConversationPattern]:
        """Konuşma pattern'lerini tespit et"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        conversations = self.get_conversations(date)
        patterns = []
        
        # Pattern 1: Tekrarlayan soru tipleri
        question_types = self._categorize_questions([c.get("user_input", "") for c in conversations])
        for q_type, examples in question_types.items():
            if len(examples) >= 3:
                patterns.append(ConversationPattern(
                    pattern_type="repeated_question_type",
                    description=f"Sık sorulan soru tipi: {q_type}",
                    frequency=len(examples),
                    examples=examples
                ))
        
        # Pattern 2: Düşük güvenlik skorlu intent'ler
        low_conf = [c for c in conversations if c.get("confidence", 1.0) < 0.6]
        if low_conf:
            patterns.append(ConversationPattern(
                pattern_type="low_confidence_routing",
                description="Düşük güvenlikle yönlendirilen sorgular",
                frequency=len(low_conf),
                examples=[c.get("user_input", "")[:50] for c in low_conf]
            ))
        
        # Pattern 3: Uzun yanıt süreleri
        slow = [c for c in conversations if c.get("response_time_ms", 0) > 3000]
        if slow:
            patterns.append(ConversationPattern(
                pattern_type="slow_responses",
                description="Yavaş yanıt verilen sorgular (>3s)",
                frequency=len(slow),
                examples=[c.get("user_input", "")[:50] for c in slow]
            ))
        
        return patterns
    
    def _categorize_questions(self, questions: List[str]) -> Dict[str, List[str]]:
        """Soruları kategorize et"""
        categories = {
            "what": [],
            "how": [],
            "why": [],
            "code": [],
            "greeting": [],
            "other": []
        }
        
        for q in questions:
            q_lower = q.lower()
            if q_lower.startswith(("ne ", "nedir", "neyin")):
                categories["what"].append(q)
            elif q_lower.startswith(("nasıl", "how")):
                categories["how"].append(q)
            elif q_lower.startswith(("neden", "niye", "why")):
                categories["why"].append(q)
            elif any(kw in q_lower for kw in ["kod", "code", "python", "function", "class"]):
                categories["code"].append(q)
            elif any(kw in q_lower for kw in ["merhaba", "selam", "hello", "hi"]):
                categories["greeting"].append(q)
            else:
                categories["other"].append(q)
        
        return {k: v for k, v in categories.items() if v}
    
    def extract_knowledge(self, date: Optional[str] = None) -> List[ExtractedFact]:
        """Konuşmalardan bilgi çıkar"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        conversations = self.get_conversations(date)
        facts = []
        
        # Başarılı ve bilgi içeren konuşmaları bul
        for c in conversations:
            if not c.get("success", True):
                continue
            
            user_input = c.get("user_input", "")
            response = c.get("assistant_response", "")
            intent = c.get("intent", "unknown")
            
            # Bilgi içeren yanıtları tespit et
            if self._contains_factual_info(response):
                fact = self._extract_fact_from_response(user_input, response, intent)
                if fact:
                    facts.append(fact)
        
        return facts
    
    def _contains_factual_info(self, text: str) -> bool:
        """Metin bilgi içeriyor mu?"""
        # Basit heuristik: Uzun yanıtlar ve belirli pattern'ler
        if len(text) < 50:
            return False
        
        factual_patterns = [
            r"\d{4}",  # Yıllar
            r"[A-Z][a-z]+ [A-Z][a-z]+",  # Proper nouns
            r"(çünkü|because|nedeni|sebebi)",
            r"(tanım|definition|anlam)",
        ]
        
        for pattern in factual_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return len(text) > 200  # Uzun yanıtlar genelde bilgi içerir
    
    def _extract_fact_from_response(
        self,
        query: str,
        response: str,
        intent: str
    ) -> Optional[ExtractedFact]:
        """Yanıttan fact çıkar"""
        # İlk cümleyi al (genelde özet)
        sentences = re.split(r'[.!?]', response)
        if not sentences:
            return None
        
        first_sentence = sentences[0].strip()
        if len(first_sentence) < 20:
            return None
        
        return ExtractedFact(
            fact_text=first_sentence,
            source_query=query,
            confidence=0.7,  # Basit extraction için sabit
            category=intent
        )
    
    def suggest_training_data(self, date: Optional[str] = None) -> List[TrainingSuggestion]:
        """Eğitim verisi önerileri oluştur"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        suggestions = []
        
        # Başarısız konuşmalardan öneri
        failed = self.find_failed_conversations(date)
        if failed:
            error_intents = Counter(f.intent for f in failed)
            for intent, count in error_intents.most_common(3):
                suggestions.append(TrainingSuggestion(
                    category=intent,
                    reason=f"{count} başarısız sorgu bu kategoride",
                    example_queries=[f.user_input for f in failed if f.intent == intent][:5],
                    priority=min(5, count)
                ))
        
        # Düşük güvenlik skorlu sorgulardan öneri
        patterns = self.detect_patterns(date)
        for p in patterns:
            if p.pattern_type == "low_confidence_routing":
                suggestions.append(TrainingSuggestion(
                    category="router",
                    reason="Düşük güvenlikle yönlendirilen sorgular var",
                    example_queries=p.examples,
                    priority=4
                ))
        
        return suggestions
    
    # ============ Memory Integration ============
    
    def sync_to_memory(self, facts: List[ExtractedFact]) -> int:
        """Çıkarılan bilgileri memory'e kaydet"""
        if not self.memory_handler:
            return 0
        
        count = 0
        for fact in facts:
            try:
                self.memory_handler.add_memory(
                    text=fact.fact_text,
                    memory_type="fact",
                    metadata={
                        "source": "async_extraction",
                        "category": fact.category,
                        "confidence": fact.confidence,
                        "source_query": fact.source_query
                    }
                )
                count += 1
            except Exception as e:
                self.logger.log_error(f"Memory sync error: {e}")
        
        return count
    
    # ============ Report Management ============
    
    def _save_report(self, report: AnalysisReport):
        """Raporu dosyaya kaydet"""
        filename = f"report_{report.date}_{report.analysis_type}.json"
        file_path = self.output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
    
    def run_full_analysis(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Tam analiz çalıştır"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        self.logger.log_system(f"Starting full analysis for {date}")
        
        results = {
            "date": date,
            "generated_at": datetime.now().isoformat()
        }
        
        # 1. Günlük özet
        daily_report = self.analyze_daily_logs(date)
        results["daily_summary"] = daily_report.summary
        
        # 2. Başarısız konuşmalar
        failed = self.find_failed_conversations(date)
        results["failed_conversations"] = len(failed)
        results["failed_details"] = [f.to_dict() for f in failed[:10]]
        
        # 3. Pattern tespiti
        patterns = self.detect_patterns(date)
        results["patterns"] = [p.to_dict() for p in patterns]
        
        # 4. Bilgi çıkarımı
        facts = self.extract_knowledge(date)
        results["extracted_facts"] = len(facts)
        
        # 5. Memory'e sync
        if self.memory_handler:
            synced = self.sync_to_memory(facts)
            results["facts_synced_to_memory"] = synced
        
        # 6. Eğitim önerileri
        suggestions = self.suggest_training_data(date)
        results["training_suggestions"] = [s.to_dict() for s in suggestions]
        
        # 7. Öneriler
        results["recommendations"] = daily_report.recommendations
        
        # Sonuç raporunu kaydet
        report_path = self.output_dir / f"full_analysis_{date}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        self.logger.log_system(f"Full analysis completed for {date}", {
            "conversations": results["daily_summary"].get("total_conversations", 0),
            "failed": results["failed_conversations"],
            "patterns": len(patterns),
            "facts": results["extracted_facts"]
        })
        
        return results


def create_async_processor(
    log_dir: str = "./logs",
    memory_handler = None
) -> AsyncProcessor:
    """AsyncProcessor oluştur"""
    return AsyncProcessor(log_dir=log_dir, memory_handler=memory_handler)


if __name__ == "__main__":
    # Test
    processor = create_async_processor()
    
    # Bugünün analizini çalıştır
    date = datetime.now().strftime("%Y-%m-%d")
    print(f"Running analysis for {date}...")
    
    results = processor.run_full_analysis(date)
    
    print(f"\n=== Analysis Results ===")
    print(f"Total conversations: {results['daily_summary'].get('total_conversations', 0)}")
    print(f"Success rate: {results['daily_summary'].get('success_rate', 0):.1%}")
    print(f"Failed: {results['failed_conversations']}")
    print(f"Patterns found: {len(results['patterns'])}")
    print(f"Facts extracted: {results['extracted_facts']}")
    print(f"\nRecommendations:")
    for rec in results['recommendations']:
        print(f"  - {rec}")
    
    print("\nAsync Processor test completed!")
