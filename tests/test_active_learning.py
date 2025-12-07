"""
EVO-TR: Active Learning Tests

Belirsizlik tespiti ve aktif öğrenme testleri.
"""

import pytest
import tempfile
import os
from pathlib import Path


class TestUncertaintyDetector:
    """Test uncertainty detection."""
    
    def test_uncertainty_detector_exists(self):
        """UncertaintyDetector should exist."""
        from src.lifecycle.active_learning import UncertaintyDetector
        assert UncertaintyDetector is not None
    
    def test_uncertainty_detector_init(self):
        """UncertaintyDetector should initialize."""
        from src.lifecycle.active_learning import UncertaintyDetector
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = UncertaintyDetector(log_path=tmpdir)
            assert detector is not None
    
    def test_detect_low_confidence(self):
        """Should detect low confidence."""
        from src.lifecycle.active_learning import UncertaintyDetector
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = UncertaintyDetector(log_path=tmpdir)
            is_uncertain, record = detector.detect_uncertainty(
                user_message="test message for detection",
                router_result={
                    "intent": "general",
                    "confidence": 0.3,
                    "all_scores": {"general": 0.3}
                }
            )
            assert is_uncertain is True
            assert record is not None
    
    def test_detect_multiple_intents(self):
        """Should detect multiple intents ambiguity."""
        from src.lifecycle.active_learning import UncertaintyDetector
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = UncertaintyDetector(log_path=tmpdir)
            is_uncertain, record = detector.detect_uncertainty(
                user_message="Python'da matematik işlemi",
                router_result={
                    "intent": "coding_python",
                    "confidence": 0.8,
                    "all_scores": {"coding_python": 0.45, "math": 0.43}
                }
            )
            assert is_uncertain is True
            assert "multiple_intents" in record.uncertainty_type
    
    def test_detect_short_query(self):
        """Should detect short query."""
        from src.lifecycle.active_learning import UncertaintyDetector
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = UncertaintyDetector(log_path=tmpdir)
            is_uncertain, record = detector.detect_uncertainty(
                user_message="ne?",
                router_result={
                    "intent": "help",
                    "confidence": 0.5,
                    "all_scores": {"help": 0.5}
                }
            )
            assert is_uncertain is True
    
    def test_no_uncertainty_for_confident_query(self):
        """Should not detect uncertainty for confident query."""
        from src.lifecycle.active_learning import UncertaintyDetector
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = UncertaintyDetector(log_path=tmpdir)
            is_uncertain, record = detector.detect_uncertainty(
                user_message="Python'da liste nasıl oluşturulur detaylı açıkla",
                router_result={
                    "intent": "coding_python",
                    "confidence": 0.95,
                    "all_scores": {"coding_python": 0.95, "help": 0.03}
                }
            )
            assert is_uncertain is False
            assert record is None
    
    def test_generate_clarification_prompt(self):
        """Should generate clarification prompt."""
        from src.lifecycle.active_learning import UncertaintyDetector
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = UncertaintyDetector(log_path=tmpdir)
            is_uncertain, record = detector.detect_uncertainty(
                user_message="bu?",
                router_result={
                    "intent": "general",
                    "confidence": 0.3,
                    "all_scores": {"general": 0.3, "help": 0.25}
                }
            )
            if record:
                prompt = detector.generate_clarification_prompt(record)
                assert isinstance(prompt, str)
                assert len(prompt) > 0
    
    def test_get_statistics(self):
        """Should return statistics."""
        from src.lifecycle.active_learning import UncertaintyDetector
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = UncertaintyDetector(log_path=tmpdir)
            
            # Add some detections
            detector.detect_uncertainty(
                user_message="test one",
                router_result={"intent": "general", "confidence": 0.3, "all_scores": {"general": 0.3}}
            )
            detector.detect_uncertainty(
                user_message="test two",
                router_result={"intent": "help", "confidence": 0.4, "all_scores": {"help": 0.4}}
            )
            
            stats = detector.get_statistics()
            assert stats["total"] >= 2


class TestUncertaintyLevel:
    """Test uncertainty level enum."""
    
    def test_uncertainty_levels_exist(self):
        """UncertaintyLevel should have all levels."""
        from src.lifecycle.active_learning import UncertaintyLevel
        assert UncertaintyLevel.VERY_LOW is not None
        assert UncertaintyLevel.LOW is not None
        assert UncertaintyLevel.MEDIUM is not None
        assert UncertaintyLevel.HIGH is not None
        assert UncertaintyLevel.VERY_HIGH is not None


class TestUncertaintyType:
    """Test uncertainty type enum."""
    
    def test_uncertainty_types_exist(self):
        """UncertaintyType should have all types."""
        from src.lifecycle.active_learning import UncertaintyType
        assert UncertaintyType.INTENT_AMBIGUITY is not None
        assert UncertaintyType.LOW_CONFIDENCE is not None
        assert UncertaintyType.MULTIPLE_INTENTS is not None
        assert UncertaintyType.OUT_OF_DOMAIN is not None
        assert UncertaintyType.SHORT_QUERY is not None


class TestUncertaintyRecord:
    """Test uncertainty record dataclass."""
    
    def test_uncertainty_record_exists(self):
        """UncertaintyRecord should exist."""
        from src.lifecycle.active_learning import UncertaintyRecord
        assert UncertaintyRecord is not None
    
    def test_uncertainty_record_fields(self):
        """UncertaintyRecord should have required fields."""
        from src.lifecycle.active_learning import UncertaintyRecord
        import dataclasses
        fields = [f.name for f in dataclasses.fields(UncertaintyRecord)]
        assert "id" in fields
        assert "user_message" in fields
        assert "uncertainty_type" in fields
        assert "confidence_score" in fields


class TestActiveLearningManager:
    """Test active learning manager."""
    
    def test_manager_exists(self):
        """ActiveLearningManager should exist."""
        from src.lifecycle.active_learning import ActiveLearningManager
        assert ActiveLearningManager is not None
    
    def test_manager_init(self):
        """ActiveLearningManager should initialize."""
        from src.lifecycle.active_learning import ActiveLearningManager
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ActiveLearningManager(candidate_path=tmpdir)
            assert manager is not None
    
    def test_process_interaction(self):
        """Should process interaction."""
        from src.lifecycle.active_learning import ActiveLearningManager
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ActiveLearningManager(candidate_path=tmpdir)
            result = manager.process_interaction(
                user_message="test message",
                model_response="test response",
                router_result={
                    "intent": "general",
                    "confidence": 0.5,
                    "all_scores": {"general": 0.5}
                }
            )
            assert "is_uncertain" in result
            assert "is_training_candidate" in result
    
    def test_training_candidate_on_negative_feedback(self):
        """Should mark as training candidate on negative feedback."""
        from src.lifecycle.active_learning import ActiveLearningManager
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ActiveLearningManager(candidate_path=tmpdir)
            result = manager.process_interaction(
                user_message="test message for training",
                model_response="test response",
                router_result={
                    "intent": "general",
                    "confidence": 0.85,
                    "all_scores": {"general": 0.85}
                },
                feedback={"feedback_type": "thumbs_down"}
            )
            assert result["is_training_candidate"] is True
    
    def test_get_candidate_stats(self):
        """Should return candidate statistics."""
        from src.lifecycle.active_learning import ActiveLearningManager
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ActiveLearningManager(candidate_path=tmpdir)
            
            # Add some interactions
            manager.process_interaction(
                user_message="test",
                model_response="response",
                router_result={"intent": "general", "confidence": 0.4, "all_scores": {"general": 0.4}}
            )
            
            stats = manager.get_candidate_stats()
            assert "total" in stats
            assert stats["total"] >= 0


class TestIntentDescriptions:
    """Test intent to description mapping."""
    
    def test_intent_descriptions(self):
        """Detector should convert intents to descriptions."""
        from src.lifecycle.active_learning import UncertaintyDetector
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = UncertaintyDetector(log_path=tmpdir)
            
            # Test known intents
            desc = detector._intent_to_description("coding_python")
            assert "Python" in desc
            
            desc = detector._intent_to_description("math")
            assert "Matematik" in desc
            
            desc = detector._intent_to_description("turkish_chat")
            assert "Türkçe" in desc


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
