"""
EVO-TR: Preference Learning Tests

DPO ve tercih öğrenimi testleri.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path


class TestPreferenceSource:
    """Test preference source enum."""
    
    def test_preference_source_exists(self):
        """PreferenceSource should exist."""
        from src.lifecycle.preference_learning import PreferenceSource
        assert PreferenceSource is not None
    
    def test_preference_source_values(self):
        """PreferenceSource should have all values."""
        from src.lifecycle.preference_learning import PreferenceSource
        assert PreferenceSource.USER_FEEDBACK is not None
        assert PreferenceSource.USER_EDIT is not None
        assert PreferenceSource.A_B_TEST is not None


class TestPreferencePair:
    """Test preference pair dataclass."""
    
    def test_preference_pair_exists(self):
        """PreferencePair should exist."""
        from src.lifecycle.preference_learning import PreferencePair
        assert PreferencePair is not None
    
    def test_preference_pair_fields(self):
        """PreferencePair should have required fields."""
        from src.lifecycle.preference_learning import PreferencePair
        import dataclasses
        fields = [f.name for f in dataclasses.fields(PreferencePair)]
        assert "prompt" in fields
        assert "chosen" in fields
        assert "rejected" in fields
        assert "margin" in fields
    
    def test_to_dpo_format(self):
        """Should convert to DPO format."""
        from src.lifecycle.preference_learning import PreferencePair
        pair = PreferencePair(
            id="test_id",
            prompt="test prompt",
            chosen="good response",
            rejected="bad response",
            source="user_edit",
            margin=1.0,
            adapter="test",
            timestamp="2024-01-01"
        )
        dpo = pair.to_dpo_format()
        assert "prompt" in dpo
        assert "chosen" in dpo
        assert "rejected" in dpo
        assert dpo["chosen"] == "good response"


class TestPreferenceCollector:
    """Test preference collector."""
    
    def test_collector_exists(self):
        """PreferenceCollector should exist."""
        from src.lifecycle.preference_learning import PreferenceCollector
        assert PreferenceCollector is not None
    
    def test_collector_init(self):
        """PreferenceCollector should initialize."""
        from src.lifecycle.preference_learning import PreferenceCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = PreferenceCollector(storage_path=tmpdir)
            assert collector is not None
    
    def test_create_from_edit_feedback(self):
        """Should create pair from edit feedback."""
        from src.lifecycle.preference_learning import PreferenceCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = PreferenceCollector(storage_path=tmpdir)
            pair = collector.create_from_feedback(
                prompt="test",
                response="bad",
                feedback_type="edit",
                adapter="test",
                corrected_response="good"
            )
            assert pair is not None
            assert pair.chosen == "good"
            assert pair.rejected == "bad"
    
    def test_create_from_thumbs_up_returns_none(self):
        """thumbs_up without comparison should return None."""
        from src.lifecycle.preference_learning import PreferenceCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = PreferenceCollector(storage_path=tmpdir)
            pair = collector.create_from_feedback(
                prompt="test",
                response="response",
                feedback_type="thumbs_up",
                adapter="test"
            )
            assert pair is None  # No comparison available
    
    def test_create_from_ab_test(self):
        """Should create pair from A/B test."""
        from src.lifecycle.preference_learning import PreferenceCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = PreferenceCollector(storage_path=tmpdir)
            pair = collector.create_from_ab_test(
                prompt="test",
                response_a="a is better",
                response_b="b is worse",
                preferred="a",
                adapter="test"
            )
            assert pair is not None
            assert pair.chosen == "a is better"
    
    def test_create_from_multiple_responses(self):
        """Should create pairs from multiple responses."""
        from src.lifecycle.preference_learning import PreferenceCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = PreferenceCollector(storage_path=tmpdir)
            pairs = collector.create_from_multiple_responses(
                prompt="test",
                responses=["best", "good", "bad"],
                scores=[0.9, 0.6, 0.2],
                adapter="test"
            )
            assert len(pairs) == 2  # best vs good, best vs bad
    
    def test_get_preferences_by_adapter(self):
        """Should filter by adapter."""
        from src.lifecycle.preference_learning import PreferenceCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = PreferenceCollector(storage_path=tmpdir)
            
            # Add preferences for different adapters
            collector.create_from_ab_test("p1", "a", "b", "a", "adapter1")
            collector.create_from_ab_test("p2", "c", "d", "c", "adapter2")
            collector.create_from_ab_test("p3", "e", "f", "e", "adapter1")
            
            adapter1_prefs = collector.get_preferences_by_adapter("adapter1")
            assert len(adapter1_prefs) == 2
    
    def test_get_statistics(self):
        """Should return statistics."""
        from src.lifecycle.preference_learning import PreferenceCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = PreferenceCollector(storage_path=tmpdir)
            collector.create_from_ab_test("p", "a", "b", "a", "test")
            
            stats = collector.get_statistics()
            assert "total" in stats
            assert stats["total"] >= 1


class TestDPOTrainer:
    """Test DPO trainer."""
    
    def test_trainer_exists(self):
        """DPOTrainer should exist."""
        from src.lifecycle.preference_learning import DPOTrainer
        assert DPOTrainer is not None
    
    def test_trainer_init(self):
        """DPOTrainer should initialize."""
        from src.lifecycle.preference_learning import DPOTrainer
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = DPOTrainer(
                adapters_dir=tmpdir,
                output_dir=os.path.join(tmpdir, "output")
            )
            assert trainer is not None
    
    def test_prepare_dpo_config(self):
        """Should prepare DPO config."""
        from src.lifecycle.preference_learning import DPOTrainer
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = DPOTrainer(
                adapters_dir=tmpdir,
                output_dir=os.path.join(tmpdir, "output")
            )
            
            config = trainer.prepare_dpo_config(
                adapter_name="test",
                training_data_path=Path(tmpdir) / "data.jsonl"
            )
            
            assert "model" in config
            assert "method" in config
            assert config["method"] == "dpo"
            assert "beta" in config
    
    def test_estimate_training_time(self):
        """Should estimate training time."""
        from src.lifecycle.preference_learning import DPOTrainer
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = DPOTrainer(
                adapters_dir=tmpdir,
                output_dir=os.path.join(tmpdir, "output")
            )
            
            estimate = trainer.estimate_training_time(num_pairs=100, epochs=2)
            assert "estimated_seconds" in estimate
            assert "estimated_minutes" in estimate
            assert estimate["pairs"] == 100


class TestPreferenceLearningPipeline:
    """Test preference learning pipeline."""
    
    def test_pipeline_exists(self):
        """PreferenceLearningPipeline should exist."""
        from src.lifecycle.preference_learning import PreferenceLearningPipeline
        assert PreferenceLearningPipeline is not None
    
    def test_pipeline_init(self):
        """PreferenceLearningPipeline should initialize."""
        from src.lifecycle.preference_learning import PreferenceLearningPipeline
        pipeline = PreferenceLearningPipeline()
        assert pipeline is not None
    
    def test_process_feedback(self):
        """Should process feedback."""
        from src.lifecycle.preference_learning import PreferenceLearningPipeline
        pipeline = PreferenceLearningPipeline()
        
        pair = pipeline.process_feedback(
            prompt="test",
            response="old",
            feedback_type="edit",
            adapter="test",
            corrected_response="new"
        )
        assert pair is not None
    
    def test_get_pipeline_status(self):
        """Should return pipeline status."""
        from src.lifecycle.preference_learning import PreferenceLearningPipeline
        pipeline = PreferenceLearningPipeline()
        
        status = pipeline.get_pipeline_status()
        assert "preference_stats" in status
        assert "auto_train_enabled" in status


class TestDPOFormat:
    """Test DPO data format."""
    
    def test_dpo_format_has_required_fields(self):
        """DPO format should have prompt, chosen, rejected."""
        from src.lifecycle.preference_learning import PreferencePair
        pair = PreferencePair(
            id="id",
            prompt="p",
            chosen="c",
            rejected="r",
            source="test",
            margin=1.0,
            adapter="a",
            timestamp="t"
        )
        
        dpo = pair.to_dpo_format()
        assert set(dpo.keys()) == {"prompt", "chosen", "rejected"}
    
    def test_export_creates_jsonl(self):
        """Export should create JSONL file."""
        from src.lifecycle.preference_learning import PreferenceCollector
        with tempfile.TemporaryDirectory() as tmpdir:
            collector = PreferenceCollector(storage_path=tmpdir)
            
            # Add enough pairs
            for i in range(15):
                collector.create_from_ab_test(f"p{i}", "a", "b", "a", "test")
            
            path = collector.export_for_dpo(min_pairs=10)
            
            assert path is not None
            assert path.exists()
            
            # Check format
            with open(path, "r") as f:
                for line in f:
                    data = json.loads(line)
                    assert "prompt" in data
                    assert "chosen" in data
                    assert "rejected" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
