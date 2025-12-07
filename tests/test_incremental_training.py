"""
EVO-TR: Incremental Training Tests

LoRA incremental training testleri.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path


class TestTrainingStatus:
    """Test training status enum."""
    
    def test_training_status_exists(self):
        """TrainingStatus should exist."""
        from src.lifecycle.incremental_training import TrainingStatus
        assert TrainingStatus is not None
    
    def test_training_status_values(self):
        """TrainingStatus should have all values."""
        from src.lifecycle.incremental_training import TrainingStatus
        assert TrainingStatus.PENDING is not None
        assert TrainingStatus.TRAINING is not None
        assert TrainingStatus.COMPLETED is not None
        assert TrainingStatus.FAILED is not None


class TestTrainingJob:
    """Test training job dataclass."""
    
    def test_training_job_exists(self):
        """TrainingJob should exist."""
        from src.lifecycle.incremental_training import TrainingJob
        assert TrainingJob is not None
    
    def test_training_job_fields(self):
        """TrainingJob should have required fields."""
        from src.lifecycle.incremental_training import TrainingJob
        import dataclasses
        fields = [f.name for f in dataclasses.fields(TrainingJob)]
        assert "id" in fields
        assert "adapter_name" in fields
        assert "status" in fields
        assert "samples_count" in fields


class TestIncrementalTrainer:
    """Test incremental trainer."""
    
    def test_trainer_exists(self):
        """IncrementalTrainer should exist."""
        from src.lifecycle.incremental_training import IncrementalTrainer
        assert IncrementalTrainer is not None
    
    def test_trainer_init(self):
        """IncrementalTrainer should initialize."""
        from src.lifecycle.incremental_training import IncrementalTrainer
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = IncrementalTrainer(
                adapters_dir=tmpdir,
                training_data_dir=os.path.join(tmpdir, "data")
            )
            assert trainer is not None
    
    def test_prepare_training_data_thumbs_up(self):
        """Should prepare training data from thumbs_up feedback."""
        from src.lifecycle.incremental_training import IncrementalTrainer
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = IncrementalTrainer(
                adapters_dir=tmpdir,
                training_data_dir=os.path.join(tmpdir, "data")
            )
            
            feedback = [
                {"user_message": "test1", "assistant_response": "resp1", "feedback_type": "thumbs_up"},
                {"user_message": "test2", "assistant_response": "resp2", "feedback_type": "thumbs_up"},
                {"user_message": "test3", "assistant_response": "resp3", "feedback_type": "thumbs_up"},
            ]
            
            path = trainer.prepare_training_data(feedback, "test_adapter", min_samples=2)
            assert path is not None
            assert path.exists()
    
    def test_prepare_training_data_with_correction(self):
        """Should include corrected responses in training data."""
        from src.lifecycle.incremental_training import IncrementalTrainer
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = IncrementalTrainer(
                adapters_dir=tmpdir,
                training_data_dir=os.path.join(tmpdir, "data")
            )
            
            feedback = [
                {"user_message": "test", "assistant_response": "wrong", 
                 "feedback_type": "edit", "corrected_response": "correct"},
                {"user_message": "test2", "assistant_response": "resp2", "feedback_type": "thumbs_up"},
            ]
            
            path = trainer.prepare_training_data(feedback, "test_adapter", min_samples=1)
            
            # Check content
            if path:
                with open(path, "r") as f:
                    samples = [json.loads(line) for line in f]
                    # Should have corrected response
                    corrected = [s for s in samples if s["metadata"].get("is_correction")]
                    assert len(corrected) >= 1
    
    def test_prepare_training_data_insufficient(self):
        """Should return None if insufficient samples."""
        from src.lifecycle.incremental_training import IncrementalTrainer
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = IncrementalTrainer(
                adapters_dir=tmpdir,
                training_data_dir=os.path.join(tmpdir, "data")
            )
            
            feedback = [
                {"user_message": "test", "assistant_response": "resp", "feedback_type": "thumbs_up"}
            ]
            
            path = trainer.prepare_training_data(feedback, "test_adapter", min_samples=10)
            assert path is None
    
    def test_create_training_job(self):
        """Should create training job."""
        from src.lifecycle.incremental_training import IncrementalTrainer
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = IncrementalTrainer(
                adapters_dir=tmpdir,
                training_data_dir=os.path.join(tmpdir, "data")
            )
            
            # Create dummy data file
            data_path = Path(tmpdir) / "test.jsonl"
            with open(data_path, "w") as f:
                f.write('{"messages": []}\n')
                f.write('{"messages": []}\n')
            
            job = trainer.create_training_job("test_adapter", data_path)
            assert job is not None
            assert job.samples_count == 2
    
    def test_get_training_stats(self):
        """Should return training stats."""
        from src.lifecycle.incremental_training import IncrementalTrainer
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = IncrementalTrainer(
                adapters_dir=tmpdir,
                training_data_dir=os.path.join(tmpdir, "data")
            )
            
            stats = trainer.get_training_stats()
            assert "total" in stats


class TestContinuousLearningPipeline:
    """Test continuous learning pipeline."""
    
    def test_pipeline_exists(self):
        """ContinuousLearningPipeline should exist."""
        from src.lifecycle.incremental_training import ContinuousLearningPipeline
        assert ContinuousLearningPipeline is not None
    
    def test_pipeline_init(self):
        """ContinuousLearningPipeline should initialize."""
        from src.lifecycle.incremental_training import ContinuousLearningPipeline
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ContinuousLearningPipeline(
                adapters_dir=tmpdir,
                min_feedback_for_training=5
            )
            assert pipeline is not None
    
    def test_should_trigger_training_insufficient(self):
        """Should not trigger with insufficient feedback."""
        from src.lifecycle.incremental_training import ContinuousLearningPipeline
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ContinuousLearningPipeline(
                adapters_dir=tmpdir,
                min_feedback_for_training=10
            )
            
            should, reason = pipeline.should_trigger_training(5)
            assert should is False
            assert "Yeterli feedback yok" in reason
    
    def test_should_trigger_training_sufficient(self):
        """Should trigger with sufficient feedback."""
        from src.lifecycle.incremental_training import ContinuousLearningPipeline
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ContinuousLearningPipeline(
                adapters_dir=tmpdir,
                min_feedback_for_training=5
            )
            
            should, reason = pipeline.should_trigger_training(10)
            assert should is True
    
    def test_get_pipeline_status(self):
        """Should return pipeline status."""
        from src.lifecycle.incremental_training import ContinuousLearningPipeline
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = ContinuousLearningPipeline(
                adapters_dir=tmpdir
            )
            
            status = pipeline.get_pipeline_status()
            assert "is_active" in status
            assert "total_trainings" in status


class TestTrainingSampleFormat:
    """Test training sample format."""
    
    def test_sample_has_messages(self):
        """Training sample should have messages array."""
        from src.lifecycle.incremental_training import IncrementalTrainer
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = IncrementalTrainer(
                adapters_dir=tmpdir,
                training_data_dir=os.path.join(tmpdir, "data")
            )
            
            sample = trainer._create_training_sample("user msg", "assistant resp")
            assert "messages" in sample
            assert len(sample["messages"]) == 2
    
    def test_sample_has_user_and_assistant(self):
        """Training sample should have user and assistant roles."""
        from src.lifecycle.incremental_training import IncrementalTrainer
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = IncrementalTrainer(
                adapters_dir=tmpdir,
                training_data_dir=os.path.join(tmpdir, "data")
            )
            
            sample = trainer._create_training_sample("user msg", "assistant resp")
            roles = [m["role"] for m in sample["messages"]]
            assert "user" in roles
            assert "assistant" in roles
    
    def test_sample_has_metadata(self):
        """Training sample should have metadata."""
        from src.lifecycle.incremental_training import IncrementalTrainer
        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = IncrementalTrainer(
                adapters_dir=tmpdir,
                training_data_dir=os.path.join(tmpdir, "data")
            )
            
            sample = trainer._create_training_sample("user", "assistant", is_correction=True)
            assert "metadata" in sample
            assert sample["metadata"]["is_correction"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
