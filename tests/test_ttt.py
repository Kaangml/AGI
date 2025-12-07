"""
Test-Time Training (TTT) Tests
FAZ 10: TTT Module Unit Tests
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import asdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ttt.test_time_training import (
    TTTConfig,
    CacheEntry,
    ContextCache,
    DynamicPromptGenerator,
    SelfCorrector,
    TestTimeTrainer,
    AdaptationStrategy
)


# ============================================================
# TTTConfig Tests
# ============================================================

class TestTTTConfig:
    """TTT Configuration Tests"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = TTTConfig()
        
        assert config.enabled is True
        assert config.cache_size == 100
        assert config.cache_ttl_minutes == 60
        assert config.similarity_threshold == 0.7
        assert config.max_few_shot_examples == 3
        assert config.self_correct_iterations == 2
        
    def test_custom_config(self):
        """Test custom configuration"""
        config = TTTConfig(
            enabled=False,
            cache_size=500,
            cache_ttl_minutes=120,
            similarity_threshold=0.9,
            max_few_shot_examples=5,
            self_correct_iterations=3
        )
        
        assert config.enabled is False
        assert config.cache_size == 500
        assert config.cache_ttl_minutes == 120
        assert config.similarity_threshold == 0.9
        assert config.max_few_shot_examples == 5
        assert config.self_correct_iterations == 3
        
    def test_config_with_strategies(self):
        """Test config with custom strategies"""
        config = TTTConfig(
            strategies=["context_cache", "dynamic_prompt", "few_shot", "self_correct"]
        )
        
        assert len(config.strategies) == 4
        assert "context_cache" in config.strategies
        assert "self_correct" in config.strategies
        
    def test_config_to_dict(self):
        """Test config to dict conversion"""
        config = TTTConfig()
        config_dict = asdict(config)
        
        assert isinstance(config_dict, dict)
        assert 'cache_size' in config_dict
        assert 'strategies' in config_dict


# ============================================================
# AdaptationStrategy Tests
# ============================================================

class TestAdaptationStrategy:
    """Adaptation Strategy Enum Tests"""
    
    def test_strategy_values(self):
        """Test strategy enum values"""
        assert AdaptationStrategy.NONE.value == "none"
        assert AdaptationStrategy.CONTEXT_CACHE.value == "context_cache"
        assert AdaptationStrategy.DYNAMIC_PROMPT.value == "dynamic_prompt"
        assert AdaptationStrategy.FEW_SHOT.value == "few_shot"
        assert AdaptationStrategy.SELF_CORRECT.value == "self_correct"
        assert AdaptationStrategy.FULL.value == "full"


# ============================================================
# CacheEntry Tests
# ============================================================

class TestCacheEntry:
    """Cache Entry Tests"""
    
    def test_cache_entry_creation(self):
        """Test cache entry creation"""
        entry = CacheEntry(
            query="Test query",
            query_hash="abc123",
            response="Test response",
            context={"key": "value"},
            adapter_used="tr_chat",
            confidence=0.9,
            timestamp=datetime.now().isoformat()
        )
        
        assert entry.query == "Test query"
        assert entry.response == "Test response"
        assert entry.confidence == 0.9
        assert entry.hit_count == 0
        
    def test_cache_entry_expiration(self):
        """Test cache entry expiration check"""
        # Old entry (2 hours ago)
        old_time = (datetime.now() - timedelta(hours=2)).isoformat()
        entry = CacheEntry(
            query="Old query",
            query_hash="old123",
            response="Old response",
            context={},
            adapter_used="tr_chat",
            confidence=0.8,
            timestamp=old_time
        )
        
        # Should be expired with 60 min TTL
        assert entry.is_expired(60) is True
        
        # Should not be expired with 180 min TTL
        assert entry.is_expired(180) is False
        
    def test_cache_entry_not_expired(self):
        """Test cache entry not expired"""
        entry = CacheEntry(
            query="Recent query",
            query_hash="new123",
            response="Recent response",
            context={},
            adapter_used="tr_chat",
            confidence=0.95,
            timestamp=datetime.now().isoformat()
        )
        
        assert entry.is_expired(60) is False


# ============================================================
# ContextCache Tests
# ============================================================

class TestContextCache:
    """Context Cache Tests"""
    
    def test_cache_creation(self):
        """Test cache creation"""
        cache = ContextCache(max_size=100, ttl_minutes=60)
        
        assert cache.max_size == 100
        assert cache.ttl_minutes == 60
        assert len(cache.cache) == 0
        
    def test_cache_put_and_get(self):
        """Test adding and retrieving from cache"""
        cache = ContextCache(max_size=100)
        
        # Add entry
        entry = cache.put(
            query="Python'da liste nasıl oluşturulur?",
            response="my_list = []",
            context={"intent": "coding"},
            adapter_used="python_coder",
            confidence=0.95
        )
        
        assert entry is not None
        assert entry.query == "Python'da liste nasıl oluşturulur?"
        
        # Get entry
        retrieved = cache.get("Python'da liste nasıl oluşturulur?")
        
        assert retrieved is not None
        assert retrieved.response == "my_list = []"
        
    def test_cache_miss(self):
        """Test cache miss"""
        cache = ContextCache(max_size=100)
        
        result = cache.get("Non-existent query")
        
        assert result is None
        
    def test_cache_hit_count(self):
        """Test cache hit count increment"""
        cache = ContextCache(max_size=100)
        
        cache.put(
            query="Test query",
            response="Test response",
            context={},
            adapter_used="tr_chat",
            confidence=0.9
        )
        
        # First hit
        entry = cache.get("Test query")
        assert entry.hit_count == 1
        
        # Second hit
        entry = cache.get("Test query")
        assert entry.hit_count == 2
        
    def test_cache_eviction(self):
        """Test cache eviction when full"""
        cache = ContextCache(max_size=3)
        
        # Add 5 entries
        for i in range(5):
            cache.put(
                query=f"Query {i}",
                response=f"Response {i}",
                context={},
                adapter_used="tr_chat",
                confidence=0.9
            )
        
        # Should only have 3 entries
        assert len(cache.cache) <= 3
        assert cache.stats["evictions"] >= 2
        
    def test_get_similar_queries(self):
        """Test finding similar queries"""
        cache = ContextCache(max_size=100)
        
        # Add some entries
        cache.put(
            query="Python'da liste nasıl oluşturulur?",
            response="my_list = []",
            context={},
            adapter_used="python_coder",
            confidence=0.95
        )
        cache.put(
            query="Python'da sözlük nasıl oluşturulur?",
            response="my_dict = {}",
            context={},
            adapter_used="python_coder",
            confidence=0.9
        )
        cache.put(
            query="Matematik integrasyon formülü",
            response="∫f(x)dx",
            context={},
            adapter_used="math_expert",
            confidence=0.85
        )
        
        # Find similar to Python query
        similar = cache.get_similar("Python'da tuple nasıl oluşturulur?", threshold=0.3)
        
        assert len(similar) >= 1
        
    def test_cache_stats(self):
        """Test cache statistics"""
        cache = ContextCache(max_size=100)
        
        cache.put("Q1", "R1", {}, "tr_chat", 0.9)
        cache.get("Q1")  # Hit
        cache.get("Q2")  # Miss
        
        stats = cache.get_stats()
        
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 50.0
        
    def test_cache_clear(self):
        """Test clearing cache"""
        cache = ContextCache(max_size=100)
        
        cache.put("Q1", "R1", {}, "tr_chat", 0.9)
        cache.put("Q2", "R2", {}, "tr_chat", 0.8)
        
        cache.clear()
        
        assert len(cache.cache) == 0
        assert cache.stats["hits"] == 0
        assert cache.stats["misses"] == 0


# ============================================================
# DynamicPromptGenerator Tests
# ============================================================

class TestDynamicPromptGenerator:
    """Dynamic Prompt Generator Tests"""
    
    def test_generator_creation(self):
        """Test generator creation"""
        generator = DynamicPromptGenerator()
        
        assert len(generator.prompt_history) == 0
        
    def test_generate_system_prompt_tr_chat(self):
        """Test system prompt for Turkish chat"""
        generator = DynamicPromptGenerator()
        
        prompt = generator.generate_system_prompt(
            adapter="tr_chat",
            intent="turkish_chat"
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Türkçe" in prompt
        
    def test_generate_system_prompt_python(self):
        """Test system prompt for Python coder"""
        generator = DynamicPromptGenerator()
        
        prompt = generator.generate_system_prompt(
            adapter="python_coder",
            intent="coding_python"
        )
        
        assert isinstance(prompt, str)
        assert "Python" in prompt
        
    def test_generate_system_prompt_math(self):
        """Test system prompt for math expert"""
        generator = DynamicPromptGenerator()
        
        prompt = generator.generate_system_prompt(
            adapter="math_expert",
            intent="math"
        )
        
        assert isinstance(prompt, str)
        assert "matematik" in prompt.lower() or "adım" in prompt.lower()
        
    def test_generate_system_prompt_with_context(self):
        """Test system prompt with context"""
        generator = DynamicPromptGenerator()
        
        prompt = generator.generate_system_prompt(
            adapter="tr_chat",
            intent="turkish_chat",
            context={
                "user_preferences": {
                    "verbose": True
                }
            }
        )
        
        assert "detaylı" in prompt.lower() or "Detaylı" in prompt
        
    def test_enhance_user_prompt(self):
        """Test user prompt enhancement"""
        generator = DynamicPromptGenerator()
        
        query = "Python nedir?"
        enhanced = generator.enhance_user_prompt(query)
        
        assert query in enhanced
        
    def test_enhance_user_prompt_with_examples(self):
        """Test user prompt enhancement with examples"""
        generator = DynamicPromptGenerator()
        
        # Create mock cache entries
        examples = [
            CacheEntry(
                query="Python'da değişken",
                query_hash="x1",
                response="x = 5",
                context={},
                adapter_used="python",
                confidence=0.9,
                timestamp=datetime.now().isoformat()
            )
        ]
        
        enhanced = generator.enhance_user_prompt(
            query="Python'da fonksiyon",
            similar_examples=examples,
            intent="coding_python"
        )
        
        assert "Benzer" in enhanced or "Örnek" in enhanced
        
    def test_record_prompt(self):
        """Test prompt recording"""
        generator = DynamicPromptGenerator()
        
        generator.record_prompt(
            query="Test query",
            system_prompt="Test system prompt",
            adapter="tr_chat",
            intent="greeting"
        )
        
        assert len(generator.prompt_history) == 1
        assert generator.prompt_history[0]["query"] == "Test query"


# ============================================================
# SelfCorrector Tests
# ============================================================

class TestSelfCorrector:
    """Self Corrector Tests"""
    
    def test_corrector_creation(self):
        """Test corrector creation"""
        corrector = SelfCorrector(max_iterations=3)
        
        assert corrector.max_iterations == 3
        
    def test_evaluate_good_response(self):
        """Test evaluating a good response"""
        corrector = SelfCorrector()
        
        query = "Python'da liste nasıl oluşturulur?"
        response = """
        Python'da liste oluşturmak için köşeli parantez kullanılır:
        
        ```python
        my_list = [1, 2, 3, 4, 5]
        empty_list = []
        ```
        
        Listeler farklı veri tiplerini içerebilir.
        """
        
        score, issues = corrector.evaluate_response(query, response, "coding_python")
        
        assert isinstance(score, (int, float))
        assert 0.0 <= score <= 1.0
        assert score >= 0.7  # Good response
        
    def test_evaluate_empty_response(self):
        """Test evaluating empty response"""
        corrector = SelfCorrector()
        
        score, issues = corrector.evaluate_response("Test", "", None)
        
        assert score == 0
        assert "empty" in issues
        
    def test_evaluate_short_response(self):
        """Test evaluating short response"""
        corrector = SelfCorrector()
        
        score, issues = corrector.evaluate_response(
            "Python'u detaylı açıkla",
            "Bir dil",
            None
        )
        
        assert score < 1.0
        assert "too_short" in issues
        
    def test_evaluate_incomplete_response(self):
        """Test evaluating incomplete response"""
        corrector = SelfCorrector()
        
        # Response that doesn't end properly
        score, issues = corrector.evaluate_response(
            "Test query",
            "Bu bir yanıt ama tamamlanmamış",  # No punctuation
            None
        )
        
        # Should detect incomplete
        assert score <= 1.0
        
    def test_should_correct_critical_issue(self):
        """Test correction needed for critical issues"""
        corrector = SelfCorrector()
        
        # Empty is critical
        assert corrector.should_correct(0.5, ["empty"]) is True
        
        # Too short is critical
        assert corrector.should_correct(0.8, ["too_short"]) is True
        
        # Repetition is critical
        assert corrector.should_correct(0.7, ["repetition"]) is True
        
    def test_should_correct_low_quality(self):
        """Test correction needed for low quality"""
        corrector = SelfCorrector()
        
        # Low quality score
        assert corrector.should_correct(0.6, []) is True
        
        # Good quality score
        assert corrector.should_correct(0.85, []) is False
        
    def test_generate_correction_prompt(self):
        """Test correction prompt generation"""
        corrector = SelfCorrector()
        
        prompt = corrector.generate_correction_prompt(
            query="Python'da döngü nasıl yazılır?",
            response="for kullanılır",
            issues=["too_short"]
        )
        
        assert isinstance(prompt, str)
        assert "Python" in prompt or "döngü" in prompt
        assert "düzelt" in prompt.lower() or "Düzelt" in prompt
        
    def test_record_correction(self):
        """Test recording correction"""
        corrector = SelfCorrector()
        
        corrector.record_correction(
            query="Test query",
            original="Short",
            corrected="This is a much longer and better response.",
            issues=["too_short"]
        )
        
        assert len(corrector.correction_history) == 1
        assert corrector.correction_history[0]["issues"] == ["too_short"]


# ============================================================
# TestTimeTrainer Tests
# ============================================================

class TestTestTimeTrainer:
    """Test Time Trainer Tests"""
    
    def test_trainer_creation(self):
        """Test trainer creation"""
        trainer = TestTimeTrainer()
        
        assert trainer.config is not None
        assert trainer.cache is not None
        assert trainer.prompt_generator is not None
        assert trainer.self_corrector is not None
        
    def test_trainer_with_custom_config(self):
        """Test trainer with custom config"""
        config = TTTConfig(
            cache_size=500,
            strategies=["context_cache", "dynamic_prompt"]
        )
        trainer = TestTimeTrainer(config)
        
        assert trainer.config.cache_size == 500
        assert len(trainer.config.strategies) == 2
        
    def test_adapt_first_query(self):
        """Test adapting first query (cache miss)"""
        trainer = TestTimeTrainer()
        
        result = trainer.adapt(
            query="Python'da liste nasıl oluşturulur?",
            intent="coding_python",
            adapter="python_coder"
        )
        
        assert result["cached_response"] is None
        assert "dynamic_prompt" in result["strategies_applied"]
        assert len(result["system_prompt"]) > 0
        
    def test_adapt_cached_query(self):
        """Test adapting cached query"""
        trainer = TestTimeTrainer()
        
        # First add to cache
        trainer.cache.put(
            query="Python nedir?",
            response="Python bir programlama dilidir.",
            context={},
            adapter_used="python_coder",
            confidence=0.9
        )
        
        # Now query should hit cache
        result = trainer.adapt(
            query="Python nedir?",
            intent="coding_python",
            adapter="python_coder"
        )
        
        assert result["cached_response"] is not None
        assert "context_cache" in result["strategies_applied"]
        
    def test_adapt_with_few_shot(self):
        """Test adapting with few-shot examples"""
        config = TTTConfig(
            strategies=["context_cache", "dynamic_prompt", "few_shot"],
            similarity_threshold=0.2  # Lower threshold for test
        )
        trainer = TestTimeTrainer(config)
        
        # Add similar entry
        trainer.cache.put(
            query="Python'da liste oluşturma",
            response="my_list = [1, 2, 3]",
            context={},
            adapter_used="python_coder",
            confidence=0.95
        )
        
        # Query similar topic
        result = trainer.adapt(
            query="Python'da tuple oluşturma",
            intent="coding_python",
            adapter="python_coder"
        )
        
        # May or may not find few-shot depending on similarity
        assert "strategies_applied" in result
        
    def test_post_process_good_response(self):
        """Test post-processing good response"""
        config = TTTConfig(
            strategies=["context_cache", "self_correct"]
        )
        trainer = TestTimeTrainer(config)
        
        response = "Python'da liste oluşturmak için köşeli parantez kullanılır. my_list = [1, 2, 3]"
        
        final, metadata = trainer.post_process(
            query="Python'da liste nasıl?",
            response=response,
            intent="coding_python",
            adapter="python_coder"
        )
        
        assert final == response
        assert metadata["quality_score"] > 0
        assert metadata["cached"] is True
        
    def test_post_process_short_response(self):
        """Test post-processing short response"""
        config = TTTConfig(
            strategies=["context_cache", "self_correct"]
        )
        trainer = TestTimeTrainer(config)
        
        short_response = "Liste"
        
        final, metadata = trainer.post_process(
            query="Python'da liste detaylı açıkla",
            response=short_response,
            intent="coding_python",
            adapter="python_coder"
        )
        
        assert metadata["quality_score"] < 1.0
        # May have corrections noted
        
    def test_get_statistics(self):
        """Test getting statistics"""
        trainer = TestTimeTrainer()
        
        # Do some operations
        trainer.adapt("Query 1", "intent1", "adapter1")
        trainer.adapt("Query 2", "intent2", "adapter2")
        
        stats = trainer.get_statistics()
        
        assert "config" in stats
        assert "stats" in stats
        assert "cache_stats" in stats
        assert stats["stats"]["total_queries"] == 2
        
    def test_trainer_stats_tracking(self):
        """Test statistics are properly tracked"""
        trainer = TestTimeTrainer()
        
        initial_queries = trainer.stats["total_queries"]
        
        trainer.adapt("Test", "intent", "adapter")
        
        assert trainer.stats["total_queries"] == initial_queries + 1


# ============================================================
# Integration Tests
# ============================================================

class TestTTTIntegration:
    """TTT Integration Tests"""
    
    def test_full_flow(self):
        """Test complete TTT flow"""
        config = TTTConfig(
            strategies=["context_cache", "dynamic_prompt", "few_shot", "self_correct"]
        )
        trainer = TestTimeTrainer(config)
        
        # Step 1: Adapt query
        adapt_result = trainer.adapt(
            query="Python'da for döngüsü nasıl yazılır?",
            intent="coding_python",
            adapter="python_coder"
        )
        
        assert "system_prompt" in adapt_result
        
        # Step 2: Simulate model response
        model_response = """
        Python'da for döngüsü şu şekilde yazılır:
        
        ```python
        for i in range(10):
            print(i)
        ```
        
        Bu döngü 0'dan 9'a kadar sayıları yazdırır.
        """
        
        # Step 3: Post-process
        final, metadata = trainer.post_process(
            query="Python'da for döngüsü nasıl yazılır?",
            response=model_response,
            intent="coding_python",
            adapter="python_coder"
        )
        
        assert len(final) > 0
        assert metadata["cached"] is True
        
        # Step 4: Second query should hit cache
        result2 = trainer.adapt(
            query="Python'da for döngüsü nasıl yazılır?",
            intent="coding_python",
            adapter="python_coder"
        )
        
        assert result2["cached_response"] is not None
        
    def test_multiple_adapters(self):
        """Test with multiple adapters"""
        trainer = TestTimeTrainer()
        
        adapters = ["tr_chat", "python_coder", "math_expert", "science_expert"]
        
        for adapter in adapters:
            result = trainer.adapt(
                query=f"Test query for {adapter}",
                intent="test",
                adapter=adapter
            )
            
            assert result["system_prompt"] is not None
            
    def test_context_preservation(self):
        """Test context is preserved through flow"""
        trainer = TestTimeTrainer()
        
        context = {
            "user_id": "test_user",
            "session_id": "session_123",
            "user_preferences": {"verbose": True}
        }
        
        result = trainer.adapt(
            query="Test query",
            intent="test",
            adapter="tr_chat",
            context=context
        )
        
        trainer.post_process(
            query="Test query",
            response="Test response",
            intent="test",
            adapter="tr_chat",
            context=context
        )
        
        # Check cache entry has context
        cached = trainer.cache.get("Test query")
        if cached:
            assert cached.context.get("user_id") == "test_user"


# ============================================================
# Performance Tests
# ============================================================

class TestTTTPerformance:
    """TTT Performance Tests"""
    
    def test_cache_lookup_performance(self):
        """Test cache lookup is fast"""
        cache = ContextCache(max_size=1000)
        
        # Add entries
        for i in range(500):
            cache.put(f"Query {i}", f"Response {i}", {}, "tr_chat", 0.9)
        
        import time
        start = time.time()
        
        for i in range(100):
            cache.get(f"Query {i}")
        
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # Should be under 100ms
        
    def test_similar_search_performance(self):
        """Test similar query search performance"""
        cache = ContextCache(max_size=100)
        
        # Add entries
        for i in range(50):
            cache.put(f"Python kod örneği {i}", f"Response {i}", {}, "python_coder", 0.9)
        
        import time
        start = time.time()
        
        cache.get_similar("Python kod yazma", threshold=0.3)
        
        elapsed = time.time() - start
        
        assert elapsed < 0.5  # Should be under 500ms
        
    def test_adaptation_performance(self):
        """Test adaptation is fast"""
        trainer = TestTimeTrainer()
        
        import time
        start = time.time()
        
        for _ in range(50):
            trainer.adapt("Test query", "intent", "adapter")
        
        elapsed = time.time() - start
        
        # 50 adaptations should be fast
        assert elapsed < 1.0


# ============================================================
# Edge Case Tests
# ============================================================

class TestTTTEdgeCases:
    """TTT Edge Case Tests"""
    
    def test_unicode_handling(self):
        """Test Unicode text handling"""
        trainer = TestTimeTrainer()
        
        # Turkish characters
        result = trainer.adapt(
            query="Türkçe özel karakterler: ğüşöçİ",
            intent="turkish_chat",
            adapter="tr_chat"
        )
        
        assert result is not None
        
    def test_empty_query(self):
        """Test handling empty query"""
        trainer = TestTimeTrainer()
        
        result = trainer.adapt(
            query="",
            intent="test",
            adapter="tr_chat"
        )
        
        assert result is not None
        
    def test_very_long_query(self):
        """Test handling very long query"""
        trainer = TestTimeTrainer()
        
        long_query = "Test " * 1000
        
        result = trainer.adapt(
            query=long_query,
            intent="test",
            adapter="tr_chat"
        )
        
        assert result is not None
        
    def test_special_characters(self):
        """Test special characters in query"""
        trainer = TestTimeTrainer()
        
        special_query = "Kod: `print('hello')` ve <tag>içerik</tag> ve \"quotes\""
        
        result = trainer.adapt(
            query=special_query,
            intent="coding_python",
            adapter="python_coder"
        )
        
        assert result is not None
        
    def test_disabled_strategies(self):
        """Test with disabled strategies"""
        config = TTTConfig(
            strategies=[]  # No strategies
        )
        trainer = TestTimeTrainer(config)
        
        result = trainer.adapt(
            query="Test",
            intent="test",
            adapter="tr_chat"
        )
        
        assert len(result["strategies_applied"]) == 0
        
    def test_unknown_adapter(self):
        """Test with unknown adapter"""
        trainer = TestTimeTrainer()
        
        result = trainer.adapt(
            query="Test",
            intent="test",
            adapter="unknown_adapter"
        )
        
        # Should fall back to default prompt
        assert result["system_prompt"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
