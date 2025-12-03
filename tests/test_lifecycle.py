"""
EVO-TR Lifecycle Module Tests
==============================
Lifecycle bileşenleri için unit testler.
"""

import pytest
import json
import os
import sys
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.lifecycle import (
    EvoTRLogger,
    LogLevel,
    LogCategory,
    create_logger,
    SyncHandler,
    SessionState,
    create_sync_handler,
    AsyncProcessor,
    create_async_processor,
    SelfImprovementPipeline,
    ImprovementPriority,
    create_improvement_pipeline
)


# ============ Fixtures ============

@pytest.fixture
def temp_log_dir():
    """Geçici log dizini"""
    temp_dir = tempfile.mkdtemp(prefix="evotr_test_logs_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_chat_callback():
    """Mock chat callback"""
    def callback(user_input: str):
        return {
            "response": f"Mock response to: {user_input}",
            "intent": "general_chat",
            "confidence": 0.85,
            "adapter": None,
            "memory_hits": 0,
            "tokens": 10
        }
    return callback


@pytest.fixture
def logger(temp_log_dir):
    """Test logger"""
    return create_logger(log_dir=temp_log_dir)


@pytest.fixture
def sync_handler(mock_chat_callback, temp_log_dir):
    """Test sync handler"""
    return create_sync_handler(
        chat_callback=mock_chat_callback,
        log_dir=temp_log_dir
    )


@pytest.fixture
def async_processor(temp_log_dir):
    """Test async processor"""
    return create_async_processor(log_dir=temp_log_dir)


@pytest.fixture
def improvement_pipeline(temp_log_dir):
    """Test improvement pipeline"""
    return create_improvement_pipeline(log_dir=temp_log_dir)


# ============ Logger Tests ============

class TestLogger:
    """Logger testleri"""
    
    def test_logger_creation(self, temp_log_dir):
        """Logger oluşturma"""
        logger = create_logger(log_dir=temp_log_dir)
        assert logger is not None
        assert logger.session_id is not None
        assert Path(temp_log_dir).exists()
    
    def test_log_info(self, logger, temp_log_dir):
        """Info log yazma"""
        logger.log_info("Test message", {"key": "value"})
        
        # Log dosyasını kontrol et
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = Path(temp_log_dir) / f"evotr_{today}.jsonl"
        assert log_file.exists()
        
        # İçeriği kontrol et
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) >= 1
    
    def test_log_conversation(self, logger, temp_log_dir):
        """Conversation log yazma"""
        entry = logger.log_conversation(
            user_input="Merhaba",
            assistant_response="Selam!",
            intent="general_chat",
            confidence=0.9,
            adapter_used="tr_chat",
            memory_hits=0,
            response_time_ms=150.0,
            tokens_generated=5
        )
        
        assert entry is not None
        assert entry.user_input == "Merhaba"
        assert entry.intent == "general_chat"
        assert logger.turn_count == 1
        
        # Conversation log dosyasını kontrol et
        today = datetime.now().strftime("%Y-%m-%d")
        conv_file = Path(temp_log_dir) / f"conversations_{today}.jsonl"
        assert conv_file.exists()
    
    def test_log_performance(self, logger, temp_log_dir):
        """Performance log yazma"""
        entry = logger.log_performance(
            operation="inference",
            duration_ms=200.0,
            tokens_per_second=50.0
        )
        
        assert entry is not None
        assert entry.operation == "inference"
        
        # Performance log dosyasını kontrol et
        today = datetime.now().strftime("%Y-%m-%d")
        perf_file = Path(temp_log_dir) / f"performance_{today}.jsonl"
        assert perf_file.exists()
    
    def test_session_stats(self, logger):
        """Session istatistikleri"""
        logger.log_conversation(
            user_input="Test",
            assistant_response="Response",
            intent="test",
            confidence=0.9
        )
        
        stats = logger.get_session_stats()
        assert "session_id" in stats
        assert stats["total_turns"] == 1
    
    def test_log_error(self, logger, temp_log_dir):
        """Error log yazma"""
        logger.log_error("Test error", {"detail": "test"})
        
        today = datetime.now().strftime("%Y-%m-%d")
        error_file = Path(temp_log_dir) / f"errors_{today}.jsonl"
        assert error_file.exists()
    
    def test_daily_summary(self, logger):
        """Günlük özet"""
        # Birkaç log yaz
        for i in range(3):
            logger.log_conversation(
                user_input=f"Test {i}",
                assistant_response=f"Response {i}",
                intent="test",
                confidence=0.9,
                response_time_ms=100.0 + i * 10
            )
        
        summary = logger.get_daily_summary()
        assert summary["total_turns"] == 3
        assert summary["success_rate"] == 1.0


# ============ SyncHandler Tests ============

class TestSyncHandler:
    """SyncHandler testleri"""
    
    def test_handler_creation(self, sync_handler):
        """Handler oluşturma"""
        assert sync_handler is not None
        assert sync_handler.state is not None
        assert sync_handler.state.is_active
    
    def test_process_message(self, sync_handler):
        """Mesaj işleme"""
        result = sync_handler.process_message("Merhaba!")
        
        assert result["success"]
        assert result["intent"] == "general_chat"
        assert result["confidence"] == 0.85
        assert "Mock response" in result["response"]
        assert sync_handler.state.turn_count == 1
    
    def test_session_state(self, sync_handler):
        """Session state takibi"""
        sync_handler.process_message("Test 1")
        sync_handler.process_message("Test 2")
        
        state = sync_handler.get_state()
        assert state["turn_count"] == 2
        assert state["is_active"]
        assert state["last_intent"] == "general_chat"
    
    def test_end_session(self, sync_handler):
        """Session sonlandırma"""
        sync_handler.process_message("Test")
        stats = sync_handler.end_session()
        
        assert not sync_handler.state.is_active
        assert stats["turn_count"] == 1
    
    def test_error_handling(self, temp_log_dir):
        """Hata yönetimi"""
        def failing_callback(msg):
            raise ValueError("Test error")
        
        handler = create_sync_handler(failing_callback, log_dir=temp_log_dir)
        result = handler.process_message("Test")
        
        assert not result["success"]
        assert result["error"] is not None
        assert handler.state.error_count == 1
    
    def test_callbacks(self, mock_chat_callback, temp_log_dir):
        """Callback sistemi"""
        handler = create_sync_handler(mock_chat_callback, log_dir=temp_log_dir)
        
        callback_called = {"response": False, "error": False}
        
        @handler.on_response
        def on_response(data):
            callback_called["response"] = True
        
        handler.process_message("Test")
        assert callback_called["response"]


# ============ AsyncProcessor Tests ============

class TestAsyncProcessor:
    """AsyncProcessor testleri"""
    
    def test_processor_creation(self, async_processor):
        """Processor oluşturma"""
        assert async_processor is not None
    
    def test_analyze_empty_logs(self, async_processor):
        """Boş log analizi"""
        report = async_processor.analyze_daily_logs()
        
        assert report is not None
        assert report.summary["total_conversations"] == 0
    
    def test_detect_patterns_empty(self, async_processor):
        """Boş pattern tespiti"""
        patterns = async_processor.detect_patterns()
        assert isinstance(patterns, list)
    
    def test_find_failed_conversations_empty(self, async_processor):
        """Boş başarısız konuşma araması"""
        failed = async_processor.find_failed_conversations()
        assert isinstance(failed, list)
        assert len(failed) == 0
    
    def test_full_analysis(self, async_processor):
        """Tam analiz"""
        results = async_processor.run_full_analysis()
        
        assert "date" in results
        assert "daily_summary" in results
        assert "failed_conversations" in results
        assert "patterns" in results
        assert "recommendations" in results
    
    def test_analysis_with_data(self, temp_log_dir):
        """Verili analiz"""
        # Önce log yaz
        logger = create_logger(log_dir=temp_log_dir)
        for i in range(5):
            logger.log_conversation(
                user_input=f"Soru {i}",
                assistant_response=f"Cevap {i}",
                intent="general_chat",
                confidence=0.9,
                response_time_ms=100.0
            )
        
        # Sonra analiz et
        processor = create_async_processor(log_dir=temp_log_dir)
        report = processor.analyze_daily_logs()
        
        assert report.summary["total_conversations"] == 5
        assert report.summary["success_rate"] == 1.0


# ============ SelfImprovementPipeline Tests ============

class TestSelfImprovementPipeline:
    """SelfImprovementPipeline testleri"""
    
    def test_pipeline_creation(self, improvement_pipeline):
        """Pipeline oluşturma"""
        assert improvement_pipeline is not None
        assert improvement_pipeline.targets is not None
    
    def test_update_metrics_empty(self, improvement_pipeline):
        """Boş metrik güncelleme"""
        metrics = improvement_pipeline.update_metrics(days=1)
        # Boş veri için boş dict döner
        assert isinstance(metrics, dict)
    
    def test_check_retraining_triggers(self, improvement_pipeline):
        """Re-training trigger kontrolü"""
        triggers = improvement_pipeline.check_retraining_triggers()
        
        assert "router_retrain" in triggers
        assert "lora_retrain" in triggers
        assert "memory_rebuild" in triggers
    
    def test_generate_tasks_empty(self, improvement_pipeline):
        """Boş görev oluşturma"""
        tasks = improvement_pipeline.analyze_and_generate_tasks(days=1)
        assert isinstance(tasks, list)
    
    def test_task_management(self, temp_log_dir):
        """Görev yönetimi"""
        from src.lifecycle.self_improvement import ImprovementTask, ImprovementType
        
        # Yeni pipeline oluştur (temiz state)
        pipeline = create_improvement_pipeline(log_dir=temp_log_dir)
        pipeline.tasks.clear()  # Mevcut görevleri temizle
        
        # Manuel görev ekle
        task = ImprovementTask(
            task_id="TEST-001",
            improvement_type=ImprovementType.SYSTEM_CONFIG,
            priority=ImprovementPriority.HIGH,
            title="Test Task",
            description="Test description",
            evidence=["Test evidence"],
            suggested_actions=["Test action"],
            estimated_effort="low"
        )
        pipeline.tasks.append(task)
        
        pending = pipeline.get_pending_tasks()
        assert len(pending) == 1
        
        pipeline.complete_task("TEST-001")
        pending = pipeline.get_pending_tasks()
        assert len(pending) == 0
    
    def test_generate_report(self, improvement_pipeline):
        """Rapor oluşturma"""
        report = improvement_pipeline.generate_improvement_report()
        
        assert "generated_at" in report
        assert "metrics" in report
        assert "retraining_triggers" in report
    
    def test_save_report(self, improvement_pipeline, temp_log_dir):
        """Rapor kaydetme"""
        report_path = improvement_pipeline.save_improvement_report()
        assert report_path.exists()


# ============ Integration Tests ============

class TestLifecycleIntegration:
    """Lifecycle entegrasyon testleri"""
    
    def test_logger_sync_handler_integration(self, temp_log_dir, mock_chat_callback):
        """Logger ve SyncHandler entegrasyonu"""
        logger = create_logger(log_dir=temp_log_dir)
        handler = SyncHandler(
            chat_callback=mock_chat_callback,
            logger=logger
        )
        
        handler.process_message("Test mesajı")
        
        # Logger'da kayıt olmalı
        assert logger.turn_count == 1
    
    def test_full_lifecycle_flow(self, temp_log_dir, mock_chat_callback):
        """Tam lifecycle akışı"""
        # 1. Logger oluştur
        logger = create_logger(log_dir=temp_log_dir)
        
        # 2. SyncHandler ile mesaj işle
        handler = SyncHandler(
            chat_callback=mock_chat_callback,
            logger=logger
        )
        
        for i in range(5):
            handler.process_message(f"Soru {i}")
        
        handler.end_session()
        
        # 3. AsyncProcessor ile analiz et
        processor = create_async_processor(log_dir=temp_log_dir)
        analysis = processor.run_full_analysis()
        
        assert analysis["daily_summary"]["total_conversations"] == 5
        
        # 4. Self-Improvement ile kontrol et
        pipeline = create_improvement_pipeline(log_dir=temp_log_dir)
        triggers = pipeline.check_retraining_triggers()
        
        assert isinstance(triggers, dict)


# ============ Run Tests ============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
