#!/usr/bin/env python3
"""
EVO-TR: Entegrasyon Testleri

Tüm bileşenlerin birlikte çalışmasını test eder.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import time
from dataclasses import dataclass

# Import all components
from src.router.intent_classifier import IntentClassifier
from src.memory import MemoryManager, MemoryHandler, ContextBuffer
from src.experts import LoRAManager
from src.inference import MLXInference
from src.orchestrator import EvoTR


class TestRouterIntegration:
    """Router entegrasyon testleri."""
    
    @pytest.fixture(scope="class")
    def router(self):
        """Router instance."""
        return IntentClassifier(
            model_path="./models/router/sentence_transformer",
            dataset_path="./data/router/intent_dataset.json",
            mapping_path="./data/router/intent_mapping.json"
        )
    
    def test_router_loads(self, router):
        """Router yükleniyor mu?"""
        assert router is not None
    
    def test_router_predicts_code_python(self, router):
        """Python kodu soruları code_python olarak sınıflandırılıyor mu?"""
        result = router.predict("Python'da liste nasıl oluşturulur?")
        assert result['intent'] == 'code_python'
        assert result['confidence'] > 0.3
    
    def test_router_predicts_general_chat(self, router):
        """Selamlaşma genel sohbet olarak sınıflandırılıyor mu?"""
        result = router.predict("Merhaba, nasılsın?")
        assert result['intent'] == 'general_chat'
        assert result['confidence'] > 0.3
    
    def test_router_predicts_turkish_culture(self, router):
        """Türk kültürü soruları doğru sınıflandırılıyor mu?"""
        result = router.predict("Türk kahvesi nasıl yapılır?")
        assert result['intent'] == 'turkish_culture'
    
    def test_router_predicts_memory_recall(self, router):
        """Hafıza soruları memory_recall olarak sınıflandırılıyor mu?"""
        result = router.predict("Az önce ne sordum sana?")
        assert result['intent'] == 'memory_recall'


class TestMemoryIntegration:
    """Memory entegrasyon testleri."""
    
    @pytest.fixture(scope="class")
    def memory_manager(self):
        """MemoryManager instance."""
        return MemoryManager(
            db_path="./data/chromadb",
            collection_name="test_integration"
        )
    
    def test_memory_manager_loads(self, memory_manager):
        """MemoryManager yükleniyor mu?"""
        assert memory_manager is not None
    
    def test_add_and_search(self, memory_manager):
        """Ekleme ve arama çalışıyor mu?"""
        # Ekle
        memory_manager.add_conversation(
            user_message="Test sorusu",
            assistant_response="Test yanıtı",
            intent="general_chat"
        )
        
        # Ara
        results = memory_manager.search_similar("Test", top_k=3)
        assert len(results) > 0
    
    def test_context_integration(self, memory_manager):
        """Context buffer çalışıyor mu?"""
        context = memory_manager.get_rag_context("Test")
        # String döndürüyor
        assert isinstance(context, str)


class TestLoRAIntegration:
    """LoRA Manager entegrasyon testleri."""
    
    @pytest.fixture(scope="class")
    def lora_manager(self):
        """LoRAManager instance."""
        return LoRAManager(
            base_model_path="./models/base/qwen-2.5-3b-instruct",
            adapters_dir="./adapters"
        )
    
    def test_lora_manager_loads(self, lora_manager):
        """LoRAManager yükleniyor mu?"""
        assert lora_manager is not None
    
    def test_list_adapters(self, lora_manager):
        """Adapter'lar listeleniyor mu?"""
        adapters = lora_manager.list_adapters()
        assert len(adapters) >= 2  # En az python_coder ve tr_chat
        assert "python_coder" in adapters
    
    def test_intent_to_adapter_mapping(self, lora_manager):
        """Intent → Adapter mapping çalışıyor mu?"""
        # code_python → python_coder
        adapter = lora_manager.get_adapter_for_intent("code_python")
        assert adapter == "python_coder"
        
        # general_chat → None (base model)
        adapter = lora_manager.get_adapter_for_intent("general_chat")
        assert adapter is None


class TestInferenceIntegration:
    """Inference entegrasyon testleri."""
    
    @pytest.fixture(scope="class")
    def inference(self):
        """MLXInference instance."""
        return MLXInference(
            base_model_path="./models/base/qwen-2.5-3b-instruct"
        )
    
    def test_inference_loads(self, inference):
        """MLXInference yükleniyor mu?"""
        assert inference is not None
    
    def test_generate_response(self, inference):
        """Yanıt üretiyor mu?"""
        response = inference.generate(
            prompt="Merhaba!",
            max_tokens=50
        )
        assert len(response) > 0
    
    def test_stats_tracking(self, inference):
        """İstatistikler takip ediliyor mu?"""
        stats = inference.get_stats()
        assert "total_generations" in stats
        assert "total_tokens" in stats


class TestOrchestratorIntegration:
    """Orchestrator entegrasyon testleri - Full System."""
    
    @pytest.fixture(scope="class")
    def evo(self):
        """EvoTR instance."""
        return EvoTR(verbose=False)
    
    def test_evo_loads(self, evo):
        """EvoTR yükleniyor mu?"""
        assert evo is not None
    
    def test_chat_simple(self, evo):
        """Basit chat çalışıyor mu?"""
        response = evo.chat("Merhaba!")
        assert len(response) > 0
    
    def test_chat_python_question(self, evo):
        """Python sorusu adapter değişikliği yapıyor mu?"""
        evo.chat("Python'da liste nasıl oluşturulur?")
        status = evo.get_status()
        assert status["current_intent"] == "code_python"
        assert status["current_adapter"] == "python_coder"
    
    def test_memory_recall(self, evo):
        """Hafıza hatırlama çalışıyor mu?"""
        # Önce bir soru sor
        evo.chat("Fibonacci dizisi nedir?")
        
        # Sonra hafızadan sor
        response = evo.chat("Az önce ne sordum?")
        status = evo.get_status()
        assert status["current_intent"] == "memory_recall"
    
    def test_conversation_history(self, evo):
        """Konuşma geçmişi kaydediliyor mu?"""
        history = evo.get_conversation_history()
        assert len(history) >= 2  # En az 2 konuşma
    
    def test_clear_conversation(self, evo):
        """Konuşma temizleme çalışıyor mu?"""
        evo.clear_conversation()
        history = evo.get_conversation_history()
        assert len(history) == 0
    
    def test_add_fact(self, evo):
        """Bilgi ekleme çalışıyor mu?"""
        doc_id = evo.add_fact("Test bilgisi: Integration test başarılı.")
        assert doc_id is not None
    
    def test_search_memory(self, evo):
        """Hafıza arama çalışıyor mu?"""
        results = evo.search_memory("Integration test")
        assert len(results) > 0


class TestEndToEndFlow:
    """Uçtan uca test senaryoları."""
    
    @pytest.fixture(scope="class")
    def evo(self):
        """Fresh EvoTR instance."""
        evo = EvoTR(verbose=False)
        evo.clear_conversation()
        return evo
    
    def test_full_conversation_flow(self, evo):
        """Tam bir konuşma akışı."""
        # 1. Selamlama
        r1 = evo.chat("Merhaba!")
        assert len(r1) > 0
        
        # 2. Python sorusu
        r2 = evo.chat("Python'da for döngüsü nasıl yazılır?")
        assert len(r2) > 0
        s2 = evo.get_status()
        assert s2["current_intent"] == "code_python"
        
        # 3. Hafıza sorusu
        r3 = evo.chat("Az önce hangi programlama dilini sordum?")
        s3 = evo.get_status()
        assert s3["current_intent"] == "memory_recall"
        
        # 4. Geçmiş kontrolü
        history = evo.get_conversation_history()
        assert len(history) == 3
    
    def test_adapter_switching_flow(self, evo):
        """Adapter değiştirme akışı."""
        evo.clear_conversation()
        
        # Base model ile başla
        evo.chat("Merhaba!")
        s1 = evo.get_status()
        assert s1["current_adapter"] in [None, "base_model"]
        
        # Python adapter'a geç
        evo.chat("Python sözlük nasıl oluşturulur?")
        s2 = evo.get_status()
        assert s2["current_adapter"] == "python_coder"
        
        # Tekrar base'e dön
        evo.chat("Bugün hava nasıl?")
        s3 = evo.get_status()
        # general_chat base model kullanır
        assert s3["current_intent"] == "general_chat"


class TestPerformance:
    """Performans testleri."""
    
    @pytest.fixture(scope="class")
    def evo(self):
        """EvoTR instance."""
        return EvoTR(verbose=False)
    
    def test_response_time(self, evo):
        """Yanıt süresi makul mü?"""
        start = time.time()
        evo.chat("Merhaba!")
        elapsed = time.time() - start
        
        # 10 saniyeden az olmalı (cold start dahil)
        assert elapsed < 10.0
    
    def test_throughput(self, evo):
        """İstatistikler doğru mu?"""
        stats = evo.get_status()["inference_stats"]
        
        if stats["total_generations"] > 0:
            assert stats["avg_tokens_per_second"] > 10  # En az 10 token/s


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
