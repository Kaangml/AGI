"""
EVO-TR: Test-Time Training (TTT) System

Inference sırasında anlık adaptasyon yetenekleri.
Model, her sorguya göre kendini dinamik olarak ayarlar.

TTT Yaklaşımları:
1. Context-Aware Caching: Benzer sorguları cache'le
2. Dynamic Prompting: Prompt'u dinamik olarak ayarla
3. Few-Shot Enhancement: Benzer örnekleri retrieval ile bul
4. Self-Correction: Çıktıyı değerlendir ve düzelt
"""

import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Generator
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import OrderedDict


class AdaptationStrategy(Enum):
    """TTT adaptasyon stratejileri."""
    NONE = "none"                           # Adaptasyon yok
    CONTEXT_CACHE = "context_cache"         # Context caching
    DYNAMIC_PROMPT = "dynamic_prompt"       # Dinamik prompt
    FEW_SHOT = "few_shot"                   # Few-shot örnekler
    SELF_CORRECT = "self_correct"           # Self-correction
    FULL = "full"                           # Tüm stratejiler


@dataclass
class TTTConfig:
    """TTT konfigürasyonu."""
    enabled: bool = True
    strategies: List[str] = field(default_factory=lambda: ["context_cache", "dynamic_prompt"])
    cache_size: int = 100                   # Cache'de tutulacak örnek sayısı
    cache_ttl_minutes: int = 60             # Cache geçerlilik süresi
    similarity_threshold: float = 0.7       # Benzerlik eşiği
    max_few_shot_examples: int = 3          # Max few-shot örnek
    self_correct_iterations: int = 2        # Self-correction iterasyonu


@dataclass
class CacheEntry:
    """Cache girişi."""
    query: str
    query_hash: str
    response: str
    context: Dict[str, Any]
    adapter_used: str
    confidence: float
    timestamp: str
    hit_count: int = 0
    
    def is_expired(self, ttl_minutes: int) -> bool:
        """Cache girişi süresi dolmuş mu?"""
        created = datetime.fromisoformat(self.timestamp)
        return datetime.now() - created > timedelta(minutes=ttl_minutes)


class ContextCache:
    """
    Context-Aware Cache.
    
    Benzer sorguları cache'leyerek hızlı yanıt verir.
    """
    
    def __init__(self, max_size: int = 100, ttl_minutes: int = 60):
        self.max_size = max_size
        self.ttl_minutes = ttl_minutes
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
        
        print(f"✅ ContextCache hazır | Size: {max_size}, TTL: {ttl_minutes}m")
    
    def _hash_query(self, query: str) -> str:
        """Sorguyu hash'le."""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def get(self, query: str) -> Optional[CacheEntry]:
        """Cache'den al."""
        query_hash = self._hash_query(query)
        
        if query_hash in self.cache:
            entry = self.cache[query_hash]
            
            # TTL kontrolü
            if entry.is_expired(self.ttl_minutes):
                del self.cache[query_hash]
                self.stats["misses"] += 1
                return None
            
            # Hit count artır ve sona taşı (LRU)
            entry.hit_count += 1
            self.cache.move_to_end(query_hash)
            self.stats["hits"] += 1
            return entry
        
        self.stats["misses"] += 1
        return None
    
    def put(
        self,
        query: str,
        response: str,
        context: Dict[str, Any],
        adapter_used: str,
        confidence: float
    ) -> CacheEntry:
        """Cache'e ekle."""
        query_hash = self._hash_query(query)
        
        # Eviction gerekli mi?
        while len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats["evictions"] += 1
        
        entry = CacheEntry(
            query=query,
            query_hash=query_hash,
            response=response,
            context=context,
            adapter_used=adapter_used,
            confidence=confidence,
            timestamp=datetime.now().isoformat()
        )
        
        self.cache[query_hash] = entry
        return entry
    
    def get_similar(self, query: str, threshold: float = 0.7) -> List[CacheEntry]:
        """Benzer sorguları bul (basit keyword matching)."""
        query_words = set(query.lower().split())
        similar = []
        
        for entry in self.cache.values():
            if entry.is_expired(self.ttl_minutes):
                continue
            
            entry_words = set(entry.query.lower().split())
            
            # Jaccard similarity
            if query_words and entry_words:
                intersection = len(query_words & entry_words)
                union = len(query_words | entry_words)
                similarity = intersection / union if union > 0 else 0
                
                if similarity >= threshold:
                    similar.append(entry)
        
        return similar
    
    def get_stats(self) -> Dict[str, Any]:
        """Cache istatistikleri."""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": round(hit_rate * 100, 2),
            "evictions": self.stats["evictions"]
        }
    
    def clear(self):
        """Cache'i temizle."""
        self.cache.clear()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}


class DynamicPromptGenerator:
    """
    Dinamik Prompt Üretici.
    
    Sorguya ve context'e göre optimal prompt oluşturur.
    """
    
    # Adapter-specific system prompts
    ADAPTER_PROMPTS = {
        "tr_chat": "Sen Türkçe konuşan, yardımsever bir AI asistansın. Doğal ve akıcı Türkçe kullan.",
        "python_coder": "Sen uzman bir Python programcısısın. Temiz, okunabilir ve iyi dokümante edilmiş kod yaz.",
        "math_expert": "Sen matematik uzmanısın. Adım adım çözümler göster ve formülleri açıkla.",
        "science_expert": "Sen bilim uzmanısın. Bilimsel kavramları anlaşılır şekilde açıkla.",
        "history_expert": "Sen tarih uzmanısın. Tarihi olayları kronolojik ve bağlamsal olarak açıkla."
    }
    
    # Intent-specific enhancements
    INTENT_ENHANCEMENTS = {
        "coding_python": "Kod bloklarını ``` ile sarmalayarak göster. Gerektiğinde örnek kullanım da ekle.",
        "math": "Matematiksel ifadeleri açık yaz. Adım adım çözüm göster.",
        "science": "Bilimsel terimleri Türkçe karşılıklarıyla birlikte ver.",
        "history": "Tarihleri ve önemli kişileri belirt.",
        "turkish_chat": "Samimi ve doğal bir dil kullan.",
        "greeting": "Sıcak ve samimi bir selamlama yap.",
        "help": "Yardım seçeneklerini liste halinde sun."
    }
    
    def __init__(self):
        self.prompt_history: List[Dict[str, Any]] = []
        print("✅ DynamicPromptGenerator hazır")
    
    def generate_system_prompt(
        self,
        adapter: str,
        intent: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Dinamik system prompt oluştur."""
        parts = []
        
        # Base adapter prompt
        base_prompt = self.ADAPTER_PROMPTS.get(adapter, self.ADAPTER_PROMPTS["tr_chat"])
        parts.append(base_prompt)
        
        # Intent enhancement
        enhancement = self.INTENT_ENHANCEMENTS.get(intent, "")
        if enhancement:
            parts.append(enhancement)
        
        # Context-specific additions
        if context:
            if context.get("user_preferences"):
                prefs = context["user_preferences"]
                if prefs.get("verbose"):
                    parts.append("Detaylı açıklamalar ver.")
                if prefs.get("concise"):
                    parts.append("Kısa ve öz yanıtlar ver.")
            
            if context.get("previous_errors"):
                parts.append("Önceki hatalara dikkat et ve tekrarlama.")
        
        return " ".join(parts)
    
    def enhance_user_prompt(
        self,
        query: str,
        similar_examples: Optional[List[CacheEntry]] = None,
        intent: Optional[str] = None
    ) -> str:
        """Kullanıcı prompt'unu zenginleştir."""
        enhanced = query
        
        # Few-shot örnekleri ekle
        if similar_examples:
            examples_text = "\n\nBenzer sorular ve yanıtları:\n"
            for i, ex in enumerate(similar_examples[:3], 1):
                examples_text += f"\nÖrnek {i}:\nSoru: {ex.query}\nYanıt: {ex.response[:200]}...\n"
            
            enhanced = examples_text + f"\nŞimdiki soru: {query}"
        
        return enhanced
    
    def record_prompt(
        self,
        query: str,
        system_prompt: str,
        adapter: str,
        intent: str
    ):
        """Prompt'u kaydet (analiz için)."""
        self.prompt_history.append({
            "query": query,
            "system_prompt": system_prompt,
            "adapter": adapter,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        })
        
        # Son 100 kaydı tut
        if len(self.prompt_history) > 100:
            self.prompt_history = self.prompt_history[-100:]


class SelfCorrector:
    """
    Self-Correction sistemi.
    
    Model çıktısını değerlendirir ve gerektiğinde düzeltir.
    """
    
    # Kalite kontrol kuralları
    QUALITY_CHECKS = {
        "min_length": 10,           # Minimum karakter
        "max_length": 5000,         # Maximum karakter
        "has_content": True,        # Boş olmamalı
        "no_repetition": True,      # Tekrar kontrolü
        "complete_sentence": True,  # Tam cümle kontrolü
    }
    
    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations
        self.correction_history: List[Dict[str, Any]] = []
        print(f"✅ SelfCorrector hazır | Max iterations: {max_iterations}")
    
    def evaluate_response(
        self,
        query: str,
        response: str,
        intent: Optional[str] = None
    ) -> Tuple[float, List[str]]:
        """
        Yanıtı değerlendir.
        
        Returns:
            (quality_score, issues_list)
        """
        issues = []
        score = 1.0
        
        # Uzunluk kontrolü
        if len(response) < self.QUALITY_CHECKS["min_length"]:
            issues.append("too_short")
            score -= 0.3
        elif len(response) > self.QUALITY_CHECKS["max_length"]:
            issues.append("too_long")
            score -= 0.1
        
        # Boşluk kontrolü
        if not response.strip():
            issues.append("empty")
            score = 0
            return score, issues
        
        # Tekrar kontrolü
        words = response.split()
        if len(words) > 5:
            # Ardışık tekrarları kontrol et
            for i in range(len(words) - 3):
                if words[i:i+3] == words[i+3:i+6]:
                    issues.append("repetition")
                    score -= 0.2
                    break
        
        # Cümle tamamlama kontrolü
        if not response.rstrip().endswith(('.', '!', '?', ':', '```')):
            issues.append("incomplete_sentence")
            score -= 0.1
        
        # Intent-specific kontroller
        if intent == "coding_python":
            if "```" not in response and len(response) > 50:
                # Kod sorusu ama kod bloğu yok
                if any(kw in query.lower() for kw in ["kod", "yaz", "nasıl", "örnek"]):
                    issues.append("missing_code_block")
                    score -= 0.15
        
        return max(0, min(1, score)), issues
    
    def generate_correction_prompt(
        self,
        query: str,
        response: str,
        issues: List[str]
    ) -> str:
        """Düzeltme prompt'u oluştur."""
        issue_descriptions = {
            "too_short": "Yanıt çok kısa, daha detaylı açıkla.",
            "too_long": "Yanıt çok uzun, daha özet yap.",
            "empty": "Yanıt boş, tekrar cevapla.",
            "repetition": "Yanıtta tekrarlar var, tekrarları kaldır.",
            "incomplete_sentence": "Yanıt tamamlanmamış, cümleyi tamamla.",
            "missing_code_block": "Kod örneği eksik, kod bloğu ekle."
        }
        
        corrections_needed = [
            issue_descriptions.get(issue, f"Sorun: {issue}")
            for issue in issues
        ]
        
        return (
            f"Önceki yanıtını gözden geçir ve düzelt.\n\n"
            f"Orijinal soru: {query}\n\n"
            f"Önceki yanıt: {response}\n\n"
            f"Düzeltilmesi gereken sorunlar:\n" +
            "\n".join(f"- {c}" for c in corrections_needed) +
            "\n\nDüzeltilmiş yanıt:"
        )
    
    def should_correct(self, quality_score: float, issues: List[str]) -> bool:
        """Düzeltme gerekli mi?"""
        # Ciddi sorunlar varsa düzelt
        critical_issues = {"empty", "too_short", "repetition"}
        if critical_issues & set(issues):
            return True
        
        # Kalite skoru düşükse düzelt
        return quality_score < 0.7
    
    def record_correction(
        self,
        query: str,
        original: str,
        corrected: str,
        issues: List[str]
    ):
        """Düzeltmeyi kaydet."""
        self.correction_history.append({
            "query": query,
            "original_length": len(original),
            "corrected_length": len(corrected),
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        })


class TestTimeTrainer:
    """
    Test-Time Training (TTT) Ana Sınıfı.
    
    Inference sırasında tüm adaptasyon stratejilerini koordine eder.
    """
    
    def __init__(self, config: Optional[TTTConfig] = None):
        self.config = config or TTTConfig()
        
        # Bileşenler
        self.cache = ContextCache(
            max_size=self.config.cache_size,
            ttl_minutes=self.config.cache_ttl_minutes
        )
        self.prompt_generator = DynamicPromptGenerator()
        self.self_corrector = SelfCorrector(
            max_iterations=self.config.self_correct_iterations
        )
        
        # İstatistikler
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "corrections_made": 0,
            "few_shot_used": 0
        }
        
        print(f"✅ TestTimeTrainer hazır")
        print(f"   Strategies: {self.config.strategies}")
    
    def adapt(
        self,
        query: str,
        intent: str,
        adapter: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        TTT adaptasyonu uygula.
        
        Returns:
            {
                "system_prompt": str,
                "enhanced_query": str,
                "cached_response": Optional[str],
                "few_shot_examples": List[str],
                "strategies_applied": List[str]
            }
        """
        self.stats["total_queries"] += 1
        context = context or {}
        
        result = {
            "system_prompt": "",
            "enhanced_query": query,
            "cached_response": None,
            "few_shot_examples": [],
            "strategies_applied": []
        }
        
        # 1. Context Cache kontrolü
        if "context_cache" in self.config.strategies:
            cached = self.cache.get(query)
            if cached:
                result["cached_response"] = cached.response
                result["strategies_applied"].append("context_cache")
                self.stats["cache_hits"] += 1
                return result
        
        # 2. Dinamik prompt oluştur
        if "dynamic_prompt" in self.config.strategies:
            result["system_prompt"] = self.prompt_generator.generate_system_prompt(
                adapter=adapter,
                intent=intent,
                context=context
            )
            result["strategies_applied"].append("dynamic_prompt")
        
        # 3. Few-shot örnekleri bul
        if "few_shot" in self.config.strategies:
            similar = self.cache.get_similar(
                query,
                threshold=self.config.similarity_threshold
            )
            if similar:
                result["few_shot_examples"] = [
                    {"query": s.query, "response": s.response[:300]}
                    for s in similar[:self.config.max_few_shot_examples]
                ]
                result["enhanced_query"] = self.prompt_generator.enhance_user_prompt(
                    query=query,
                    similar_examples=similar[:self.config.max_few_shot_examples],
                    intent=intent
                )
                result["strategies_applied"].append("few_shot")
                self.stats["few_shot_used"] += 1
        
        return result
    
    def post_process(
        self,
        query: str,
        response: str,
        intent: str,
        adapter: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Yanıtı post-process et (self-correction dahil).
        
        Returns:
            (final_response, metadata)
        """
        metadata = {
            "original_response": response,
            "corrections": [],
            "quality_score": 1.0,
            "cached": False
        }
        
        # Self-correction
        if "self_correct" in self.config.strategies:
            current_response = response
            
            for iteration in range(self.self_corrector.max_iterations):
                quality_score, issues = self.self_corrector.evaluate_response(
                    query=query,
                    response=current_response,
                    intent=intent
                )
                
                metadata["quality_score"] = quality_score
                
                if not self.self_corrector.should_correct(quality_score, issues):
                    break
                
                # Düzeltme gerekli - not: Burada gerçek model çağrısı yapılır
                # Şimdilik sadece metadata'yı güncelliyoruz
                metadata["corrections"].append({
                    "iteration": iteration + 1,
                    "issues": issues,
                    "score_before": quality_score
                })
                self.stats["corrections_made"] += 1
                
                # Gerçek düzeltme için model çağrısı gerekir
                # correction_prompt = self.self_corrector.generate_correction_prompt(
                #     query, current_response, issues
                # )
                # current_response = model.generate(correction_prompt)
                break  # Simülasyon - gerçekte döngü devam eder
        
        # Cache'e ekle
        if "context_cache" in self.config.strategies:
            self.cache.put(
                query=query,
                response=response,
                context=context or {},
                adapter_used=adapter,
                confidence=metadata["quality_score"]
            )
            metadata["cached"] = True
        
        return response, metadata
    
    def get_statistics(self) -> Dict[str, Any]:
        """TTT istatistikleri."""
        return {
            "config": asdict(self.config),
            "stats": self.stats,
            "cache_stats": self.cache.get_stats(),
            "correction_history_size": len(self.self_corrector.correction_history)
        }


# Test
if __name__ == "__main__":
    print("=" * 50)
    print("Test-Time Training (TTT) Test")
    print("=" * 50)
    
    # TTT oluştur
    config = TTTConfig(
        strategies=["context_cache", "dynamic_prompt", "few_shot", "self_correct"]
    )
    ttt = TestTimeTrainer(config)
    
    # Test 1: İlk sorgu (cache miss)
    print("\n1. İlk sorgu (cache miss):")
    result = ttt.adapt(
        query="Python'da liste nasıl oluşturulur?",
        intent="coding_python",
        adapter="python_coder"
    )
    print(f"   Cache hit: {result['cached_response'] is not None}")
    print(f"   Strategies: {result['strategies_applied']}")
    print(f"   System prompt: {result['system_prompt'][:100]}...")
    
    # Yanıtı cache'e ekle
    response = "Python'da liste oluşturmak için köşeli parantez kullanılır: my_list = []"
    final, meta = ttt.post_process(
        query="Python'da liste nasıl oluşturulur?",
        response=response,
        intent="coding_python",
        adapter="python_coder"
    )
    print(f"   Cached: {meta['cached']}")
    print(f"   Quality: {meta['quality_score']}")
    
    # Test 2: Aynı sorgu (cache hit)
    print("\n2. Aynı sorgu (cache hit):")
    result = ttt.adapt(
        query="Python'da liste nasıl oluşturulur?",
        intent="coding_python",
        adapter="python_coder"
    )
    print(f"   Cache hit: {result['cached_response'] is not None}")
    if result['cached_response']:
        print(f"   Cached response: {result['cached_response'][:50]}...")
    
    # Test 3: Benzer sorgu (few-shot)
    print("\n3. Benzer sorgu (few-shot beklenir):")
    result = ttt.adapt(
        query="Python'da liste nasıl yapılır?",
        intent="coding_python",
        adapter="python_coder"
    )
    print(f"   Few-shot examples: {len(result['few_shot_examples'])}")
    print(f"   Strategies: {result['strategies_applied']}")
    
    # Test 4: Self-correction
    print("\n4. Self-correction testi:")
    short_response = "Liste yap"
    final, meta = ttt.post_process(
        query="Python'da liste detaylı açıkla",
        response=short_response,
        intent="coding_python",
        adapter="python_coder"
    )
    print(f"   Quality score: {meta['quality_score']}")
    print(f"   Corrections needed: {len(meta['corrections']) > 0}")
    
    # İstatistikler
    print("\n📊 TTT İstatistikleri:")
    stats = ttt.get_statistics()
    print(f"   Total queries: {stats['stats']['total_queries']}")
    print(f"   Cache hits: {stats['stats']['cache_hits']}")
    print(f"   Cache hit rate: {stats['cache_stats']['hit_rate']}%")
    print(f"   Corrections made: {stats['stats']['corrections_made']}")
    
    print("\n✅ Test tamamlandı!")
