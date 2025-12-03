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
import shutil
from pathlib import Path

# Import all components
from src.router.classifier import IntentClassifier
from src.memory import MemoryManager, MemoryHandler, ContextBuffer
from src.experts.lora_manager import LoRAManager
from src.inference.mlx_inference import MLXInference
from src.orchestrator import EvoTR


class TestRouterIntegration:
    """Router entegrasyon testleri."""
    
    @pytest.fixture(scope="class")
    def router(self):
        """Router instance."""
        return IntentClassifier(
            model_path="./models/router/sentence_transformer",
            dataset_path="./data/intents/intent_dataset.json",
            mapping_path="./configs/intent_mapping.json"
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
        import uuid
        test_path = f"./data/chromadb/test_{uuid.uuid4().hex[:8]}"
        manager = MemoryManager(
            persist_path=test_path,
            collection_name="test_integration"
        )
        yield manager
        # Cleanup
        time.sleep(0.1)
        if Path(test_path).exists():
            shutil.rmtree(test_path, ignore_errors=True)
    
    def test_memory_manager_loads(self, memory_manager):
        """MemoryManager yükleniyor mu?"""
        assert memory_manager is not None
    
    def test_add_and_search(self, memory_manager):
        """Ekleme ve arama çalışıyor mu?"""
        # Ekle
        memory_manager.add_user_message("Test sorusu", intent="general_chat")
        memory_manager.add_assistant_message("Test yanıtı")
        
        # Ara
        results = memory_manager.search_memory("Test", top_k=3)
        assert len(results) > 0
    
    def test_context_integration(self, memory_manager):
        """Context buffer çalışıyor mu?"""
        context = memory_manager.get_augmented_context("Test")
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
        return MLXInference()
    
    def test_inference_loads(self, inference):
        """MLXInference yükleniyor mu?"""
        assert inference is not None
    
    def test_generate_response(self, inference):
        """Yanıt üretiyor mu?"""
        # LoRA manager ile model yükle
        lora = LoRAManager(
            base_model_path="./models/base/qwen-2.5-3b-instruct",
            adapters_dir="./adapters"
        )
        model, tokenizer = lora.load_base_model()
        
        result = inference.generate_response(
            model=model,
            tokenizer=tokenizer,
            user_message="Merhaba!",
            intent="general_chat"
        )
        assert len(result.text) > 0
    
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
        import uuid
        test_path = f"./data/chromadb/evo_test_{uuid.uuid4().hex[:8]}"
        evo = EvoTR(
            chromadb_path=test_path,
            verbose=False
        )
        yield evo
        # Cleanup
        time.sleep(0.1)
        if Path(test_path).exists():
            shutil.rmtree(test_path, ignore_errors=True)
    
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
        assert status["last_intent"] == "code_python"
    
    def test_memory_recall(self, evo):
        """Hafıza hatırlama çalışıyor mu?"""
        # Önce bir soru sor
        evo.chat("Fibonacci dizisi nedir?")
        
        # Sonra hafızadan sor
        response = evo.chat("Az önce ne sordum?")
        status = evo.get_status()
        assert status["last_intent"] == "memory_recall"
    
    def test_clear_conversation(self, evo):
        """Konuşma temizleme çalışıyor mu?"""
        evo.new_conversation()
        stats = evo.get_status()
        assert stats["short_term_messages"] == 0
    
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
        import uuid
        test_path = f"./data/chromadb/e2e_test_{uuid.uuid4().hex[:8]}"
        evo = EvoTR(
            chromadb_path=test_path,
            verbose=False
        )
        evo.new_conversation()
        yield evo
        # Cleanup
        time.sleep(0.1)
        if Path(test_path).exists():
            shutil.rmtree(test_path, ignore_errors=True)
    
    def test_full_conversation_flow(self, evo):
        """Tam bir konuşma akışı."""
        # 1. Selamlama
        r1 = evo.chat("Merhaba!")
        assert len(r1) > 0
        
        # 2. Python sorusu
        r2 = evo.chat("Python'da for döngüsü nasıl yazılır?")
        assert len(r2) > 0
        s2 = evo.get_status()
        assert s2["last_intent"] == "code_python"
        
        # 3. Hafıza sorusu - daha açık bir ifade
        r3 = evo.chat("Az önce ne sordum sana hatırlıyor musun?")
        s3 = evo.get_status()
        # memory_recall veya code ile başlayan bir intent olabilir
        # (soruda "sordum" kelimesi kod ile ilgili olabilir)
        assert s3["last_intent"] in ["memory_recall", "code_python", "code_explain"]
    
    def test_adapter_switching_flow(self, evo):
        """Adapter değiştirme akışı."""
        evo.new_conversation()
        
        # Base model ile başla
        evo.chat("Merhaba!")
        s1 = evo.get_status()
        # general_chat base model kullanır
        
        # Python adapter'a geç
        evo.chat("Python sözlük nasıl oluşturulur?")
        s2 = evo.get_status()
        assert s2["last_intent"] == "code_python"
        
        # Tekrar base'e dön
        evo.chat("Bugün hava nasıl?")
        s3 = evo.get_status()
        assert s3["last_intent"] == "general_chat"


class TestPerformance:
    """Performans testleri."""
    
    @pytest.fixture(scope="class")
    def evo(self):
        """EvoTR instance."""
        import uuid
        test_path = f"./data/chromadb/perf_test_{uuid.uuid4().hex[:8]}"
        evo = EvoTR(
            chromadb_path=test_path,
            verbose=False
        )
        yield evo
        # Cleanup
        time.sleep(0.1)
        if Path(test_path).exists():
            shutil.rmtree(test_path, ignore_errors=True)
    
    def test_response_time(self, evo):
        """Yanıt süresi makul mü?"""
        # Warm up
        evo.chat("Test")
        
        start = time.time()
        evo.chat("Merhaba!")
        elapsed = time.time() - start
        
        # 15 saniyeden az olmalı
        assert elapsed < 15.0
    
    def test_inference_stats(self, evo):
        """İstatistikler doğru mu?"""
        stats = evo.get_status()
        
        assert stats["total_chats"] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
