"""
EVO-TR Lifecycle Module
========================
Sistem yaşam döngüsü yönetimi.

Bileşenler:
- Logger: Structured logging (JSON format)
- SyncHandler: Real-time chat loop (Gündüz modu)
- AsyncProcessor: Log analizi ve bilgi çıkarımı (Gece modu)
- SelfImprovementPipeline: Otomatik iyileştirme sistemi
"""

from .logger import (
    EvoTRLogger,
    LogLevel,
    LogCategory,
    ConversationEntry,
    PerformanceEntry,
    create_logger
)

from .sync_handler import (
    SyncHandler,
    SessionState,
    create_sync_handler
)

from .async_processor import (
    AsyncProcessor,
    AnalysisType,
    FailedConversation,
    ConversationPattern,
    ExtractedFact,
    TrainingSuggestion,
    AnalysisReport,
    create_async_processor
)

from .self_improvement import (
    SelfImprovementPipeline,
    ImprovementPriority,
    ImprovementType,
    ImprovementTask,
    PerformanceMetric,
    create_improvement_pipeline
)

__all__ = [
    # Logger
    "EvoTRLogger",
    "LogLevel",
    "LogCategory",
    "ConversationEntry",
    "PerformanceEntry",
    "create_logger",
    
    # Sync Handler
    "SyncHandler",
    "SessionState",
    "create_sync_handler",
    
    # Async Processor
    "AsyncProcessor",
    "AnalysisType",
    "FailedConversation",
    "ConversationPattern",
    "ExtractedFact",
    "TrainingSuggestion",
    "AnalysisReport",
    "create_async_processor",
    
    # Self Improvement
    "SelfImprovementPipeline",
    "ImprovementPriority",
    "ImprovementType",
    "ImprovementTask",
    "PerformanceMetric",
    "create_improvement_pipeline"
]