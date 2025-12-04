"""
EVO-TR Router Unit Testleri
"""

import pytest
import sys
from pathlib import Path

# Proje kökünü path'e ekle
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.router.classifier import IntentClassifier, classify, route, get_classifier
from src.router.api import route_message, route_with_details, get_router_info


class TestIntentClassifier:
    """IntentClassifier testleri"""
    
    @pytest.fixture(scope="class")
    def classifier(self):
        """Test için classifier instance"""
        return get_classifier()
    
    def test_classifier_loads(self, classifier):
        """Classifier başarıyla yükleniyor mu?"""
        assert classifier is not None
        assert len(classifier.intent_embeddings) == 9  # 9 intent (code_math + science dahil)
    
    def test_general_chat_intent(self, classifier):
        """Genel sohbet intent'i doğru tespit ediliyor mu?"""
        result = classifier.predict("Merhaba, nasılsın?")
        assert result["intent"] == "general_chat"
        assert result["confidence"] > 0.5
    
    def test_code_python_intent(self, classifier):
        """Python kod intent'i doğru tespit ediliyor mu?"""
        result = classifier.predict("Python'da liste nasıl oluşturulur?")
        assert result["intent"] == "code_python"
        assert result["adapter_id"] == "adapter_python_coder"
    
    def test_code_debug_intent(self, classifier):
        """Debug intent'i doğru tespit ediliyor mu?"""
        result = classifier.predict("Bu hata ne anlama geliyor? TypeError alıyorum")
        assert result["intent"] == "code_debug"
        # Confidence düşükse fallback olabilir
        assert result["adapter_id"] in ["adapter_python_coder", "base_model"]
    
    def test_code_math_intent(self, classifier):
        """Matematik intent'i doğru tespit ediliyor mu?"""
        # Daha açık matematik sorusu kullan
        result = classifier.predict("Bir sayının 3 katı 24 ise o sayı kaçtır?")
        assert result["intent"] == "code_math"
        # Confidence yüksekse adapter, düşükse fallback
        assert result["adapter_id"] in ["adapter_math_expert", "base_model"]
    
    def test_science_intent(self, classifier):
        """Bilim intent'i doğru tespit ediliyor mu?"""
        result = classifier.predict("DNA yapısını açıkla")
        assert result["intent"] == "science"
        # Confidence yüksekse adapter, düşükse fallback
        assert result["adapter_id"] in ["adapter_science_expert", "base_model"]
    
    def test_memory_recall_intent(self, classifier):
        """Hafıza intent'i doğru tespit ediliyor mu?"""
        result = classifier.predict("Dün ne konuştuk?")
        assert result["intent"] == "memory_recall"
        assert result["adapter_id"] == "memory_system"
    
    def test_low_confidence_fallback(self, classifier):
        """Düşük confidence'ta fallback çalışıyor mu?"""
        # Çok belirsiz bir girdi
        result = classifier.predict("xyz 123 abc")
        # Confidence düşük olmalı veya fallback'e düşmeli
        if result["confidence"] < 0.7:
            assert result["adapter_id"] == "base_model"
    
    def test_predict_returns_all_fields(self, classifier):
        """Predict tüm gerekli alanları döndürüyor mu?"""
        result = classifier.predict("Merhaba")
        assert "intent" in result
        assert "confidence" in result
        assert "adapter_id" in result
        assert "all_scores" in result
        assert len(result["all_scores"]) == 9  # 9 intent
    
    def test_get_stats(self, classifier):
        """İstatistikler doğru döndürülüyor mu?"""
        stats = classifier.get_stats()
        assert stats["total_intents"] == 9  # 9 intent
        assert stats["total_samples"] >= 230  # 215 + 30 science = 245
        assert "confidence_threshold" in stats


class TestRouterAPI:
    """Router API testleri"""
    
    def test_route_message(self):
        """route_message adapter ID döndürüyor mu?"""
        adapter = route_message("Merhaba")
        assert isinstance(adapter, str)
        assert adapter in ["adapter_tr_chat", "adapter_python_coder", 
                          "adapter_math_expert", "adapter_science_expert",
                          "memory_system", "base_model"]
    
    def test_route_with_details(self):
        """route_with_details detaylı bilgi döndürüyor mu?"""
        result = route_with_details("Python fonksiyon yaz")
        assert "intent" in result
        assert "confidence" in result
        assert "adapter_id" in result
    
    def test_get_router_info(self):
        """get_router_info bilgi döndürüyor mu?"""
        info = get_router_info()
        assert "total_intents" in info
        assert "intents" in info


class TestEdgeCases:
    """Kenar durumları testleri"""
    
    @pytest.fixture(scope="class")
    def classifier(self):
        return get_classifier()
    
    def test_empty_string(self, classifier):
        """Boş string hata vermemeli"""
        result = classifier.predict("")
        assert result is not None
        assert "intent" in result
    
    def test_very_long_text(self, classifier):
        """Çok uzun metin işlenebilmeli"""
        long_text = "Python " * 100
        result = classifier.predict(long_text)
        assert result is not None
    
    def test_special_characters(self, classifier):
        """Özel karakterler sorun olmamalı"""
        result = classifier.predict("!@#$%^&*()")
        assert result is not None
    
    def test_turkish_characters(self, classifier):
        """Türkçe karakterler doğru işlenmeli"""
        result = classifier.predict("Türkçe öğütğüşçı ĞÜŞİÖÇ")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
