"""
EVO-TR Self-Improvement Pipeline
==================================
Otomatik iyileştirme ve re-training trigger sistemi.

Özellikler:
- Hata pattern analizi
- Eğitim verisi önerileri
- LoRA re-training trigger
- Performance monitoring
- Improvement tracking
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import Counter
from enum import Enum

from .logger import EvoTRLogger, create_logger
from .async_processor import AsyncProcessor, TrainingSuggestion


class ImprovementPriority(Enum):
    """İyileştirme önceliği"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5


class ImprovementType(Enum):
    """İyileştirme tipi"""
    ROUTER_TRAINING = "router_training"
    LORA_FINETUNING = "lora_finetuning"
    MEMORY_ENRICHMENT = "memory_enrichment"
    SYSTEM_CONFIG = "system_config"
    DATA_AUGMENTATION = "data_augmentation"


@dataclass
class ImprovementTask:
    """İyileştirme görevi"""
    task_id: str
    improvement_type: ImprovementType
    priority: ImprovementPriority
    title: str
    description: str
    evidence: List[str]
    suggested_actions: List[str]
    estimated_effort: str  # "low", "medium", "high"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # pending, in_progress, completed, skipped
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "improvement_type": self.improvement_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "suggested_actions": self.suggested_actions,
            "estimated_effort": self.estimated_effort,
            "created_at": self.created_at,
            "status": self.status
        }


@dataclass
class PerformanceMetric:
    """Performans metriği"""
    metric_name: str
    current_value: float
    target_value: float
    trend: str  # "improving", "stable", "declining"
    history: List[Tuple[str, float]] = field(default_factory=list)
    
    @property
    def is_below_target(self) -> bool:
        return self.current_value < self.target_value
    
    def to_dict(self) -> Dict:
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "target_value": self.target_value,
            "trend": self.trend,
            "is_below_target": self.is_below_target,
            "history": self.history[-10:]  # Son 10 değer
        }


class SelfImprovementPipeline:
    """
    Self-Improvement Pipeline.
    
    Görevler:
    - Performans metriklerini izle
    - Hata pattern'lerini analiz et
    - İyileştirme görevleri oluştur
    - Re-training trigger'ları
    - İyileştirme takibi
    """
    
    # Varsayılan hedef metrikler
    DEFAULT_TARGETS = {
        "success_rate": 0.95,
        "avg_response_time_ms": 2000,
        "router_confidence": 0.8,
        "memory_hit_rate": 0.3
    }
    
    def __init__(
        self,
        log_dir: str = "./logs",
        data_dir: str = "./data",
        improvement_dir: str = "./logs/improvements",
        targets: Optional[Dict[str, float]] = None
    ):
        self.log_dir = Path(log_dir)
        self.data_dir = Path(data_dir)
        self.improvement_dir = Path(improvement_dir)
        self.improvement_dir.mkdir(parents=True, exist_ok=True)
        
        self.targets = targets or self.DEFAULT_TARGETS.copy()
        self.logger = create_logger(log_dir)
        self.async_processor = AsyncProcessor(log_dir)
        
        # State
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.tasks: List[ImprovementTask] = []
        self.task_counter = 0
        
        # Load existing state
        self._load_state()
    
    def _load_state(self):
        """Mevcut state'i yükle"""
        state_file = self.improvement_dir / "pipeline_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                self.task_counter = state.get("task_counter", 0)
                # Tasks'ları yükle
                for task_dict in state.get("pending_tasks", []):
                    self.tasks.append(self._dict_to_task(task_dict))
            except Exception as e:
                self.logger.log_error(f"Failed to load state: {e}")
    
    def _save_state(self):
        """State'i kaydet"""
        state_file = self.improvement_dir / "pipeline_state.json"
        state = {
            "task_counter": self.task_counter,
            "pending_tasks": [t.to_dict() for t in self.tasks if t.status == "pending"],
            "last_updated": datetime.now().isoformat()
        }
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def _dict_to_task(self, d: Dict) -> ImprovementTask:
        """Dict'ten task oluştur"""
        return ImprovementTask(
            task_id=d["task_id"],
            improvement_type=ImprovementType(d["improvement_type"]),
            priority=ImprovementPriority(d["priority"]),
            title=d["title"],
            description=d["description"],
            evidence=d["evidence"],
            suggested_actions=d["suggested_actions"],
            estimated_effort=d["estimated_effort"],
            created_at=d.get("created_at", datetime.now().isoformat()),
            status=d.get("status", "pending")
        )
    
    def _generate_task_id(self) -> str:
        """Unique task ID oluştur"""
        self.task_counter += 1
        return f"IMP-{datetime.now().strftime('%Y%m%d')}-{self.task_counter:04d}"
    
    # ============ Performance Monitoring ============
    
    def update_metrics(self, days: int = 7) -> Dict[str, PerformanceMetric]:
        """Performans metriklerini güncelle"""
        all_convs = []
        
        # Son N günün verilerini topla
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            convs = self.async_processor.get_conversations(date)
            for c in convs:
                c["_date"] = date
            all_convs.extend(convs)
        
        if not all_convs:
            return {}
        
        # Metrikleri hesapla
        total = len(all_convs)
        successful = sum(1 for c in all_convs if c.get("success", True))
        
        response_times = [c.get("response_time_ms", 0) for c in all_convs]
        confidences = [c.get("confidence", 0) for c in all_convs]
        memory_hits = sum(1 for c in all_convs if c.get("memory_hits", 0) > 0)
        
        # Metrik objelerini oluştur
        self.metrics = {
            "success_rate": PerformanceMetric(
                metric_name="success_rate",
                current_value=successful / total if total > 0 else 0,
                target_value=self.targets["success_rate"],
                trend=self._calculate_trend("success_rate", successful / total if total > 0 else 0)
            ),
            "avg_response_time_ms": PerformanceMetric(
                metric_name="avg_response_time_ms",
                current_value=sum(response_times) / len(response_times) if response_times else 0,
                target_value=self.targets["avg_response_time_ms"],
                trend=self._calculate_trend("avg_response_time_ms", 
                    sum(response_times) / len(response_times) if response_times else 0)
            ),
            "router_confidence": PerformanceMetric(
                metric_name="router_confidence",
                current_value=sum(confidences) / len(confidences) if confidences else 0,
                target_value=self.targets["router_confidence"],
                trend=self._calculate_trend("router_confidence",
                    sum(confidences) / len(confidences) if confidences else 0)
            ),
            "memory_hit_rate": PerformanceMetric(
                metric_name="memory_hit_rate",
                current_value=memory_hits / total if total > 0 else 0,
                target_value=self.targets["memory_hit_rate"],
                trend=self._calculate_trend("memory_hit_rate", memory_hits / total if total > 0 else 0)
            )
        }
        
        return self.metrics
    
    def _calculate_trend(self, metric_name: str, current_value: float) -> str:
        """Trend hesapla"""
        if metric_name not in self.metrics:
            return "stable"
        
        old_value = self.metrics[metric_name].current_value
        
        # Response time için ters mantık (düşük daha iyi)
        if metric_name == "avg_response_time_ms":
            if current_value < old_value * 0.9:
                return "improving"
            elif current_value > old_value * 1.1:
                return "declining"
        else:
            if current_value > old_value * 1.05:
                return "improving"
            elif current_value < old_value * 0.95:
                return "declining"
        
        return "stable"
    
    def get_metrics_report(self) -> Dict:
        """Metrik raporu oluştur"""
        if not self.metrics:
            self.update_metrics()
        
        return {
            "generated_at": datetime.now().isoformat(),
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "alerts": [
                {"metric": k, "message": f"{k} hedefin altında: {v.current_value:.2f} < {v.target_value:.2f}"}
                for k, v in self.metrics.items()
                if v.is_below_target
            ]
        }
    
    # ============ Improvement Task Generation ============
    
    def analyze_and_generate_tasks(self, days: int = 7) -> List[ImprovementTask]:
        """Analiz et ve iyileştirme görevleri oluştur"""
        new_tasks = []
        
        # Metrikleri güncelle
        self.update_metrics(days)
        
        # 1. Performans bazlı görevler
        for metric_name, metric in self.metrics.items():
            if metric.is_below_target:
                task = self._create_metric_improvement_task(metric_name, metric)
                if task:
                    new_tasks.append(task)
        
        # 2. Hata pattern bazlı görevler
        for i in range(min(days, 3)):  # Son 3 gün
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            failed = self.async_processor.find_failed_conversations(date)
            
            if len(failed) >= 3:  # 3+ hata varsa
                task = self._create_error_pattern_task(failed, date)
                if task:
                    new_tasks.append(task)
        
        # 3. Router improvement görevleri
        patterns = self.async_processor.detect_patterns()
        low_conf_pattern = [p for p in patterns if p.pattern_type == "low_confidence_routing"]
        if low_conf_pattern:
            task = self._create_router_improvement_task(low_conf_pattern[0])
            if task:
                new_tasks.append(task)
        
        # Yeni görevleri ekle
        for task in new_tasks:
            if not any(t.title == task.title for t in self.tasks):
                self.tasks.append(task)
        
        self._save_state()
        
        return new_tasks
    
    def _create_metric_improvement_task(
        self,
        metric_name: str,
        metric: PerformanceMetric
    ) -> Optional[ImprovementTask]:
        """Metrik bazlı iyileştirme görevi"""
        
        task_configs = {
            "success_rate": {
                "type": ImprovementType.SYSTEM_CONFIG,
                "priority": ImprovementPriority.HIGH,
                "title": "Başarı Oranını Artır",
                "actions": [
                    "Error loglarını detaylı incele",
                    "Hata yapan intent kategorilerini belirle",
                    "Timeout değerlerini kontrol et",
                    "Memory limitlerini optimize et"
                ],
                "effort": "medium"
            },
            "avg_response_time_ms": {
                "type": ImprovementType.SYSTEM_CONFIG,
                "priority": ImprovementPriority.MEDIUM,
                "title": "Yanıt Süresini Azalt",
                "actions": [
                    "Model cache stratejisini gözden geçir",
                    "LoRA adapter yükleme süresini optimize et",
                    "Memory search parametrelerini ayarla",
                    "Batch size ayarlarını kontrol et"
                ],
                "effort": "medium"
            },
            "router_confidence": {
                "type": ImprovementType.ROUTER_TRAINING,
                "priority": ImprovementPriority.HIGH,
                "title": "Router Güvenilirliğini Artır",
                "actions": [
                    "Düşük güvenlikli sorguları analiz et",
                    "Router eğitim verisine yeni örnekler ekle",
                    "Threshold değerlerini ayarla",
                    "Yeni intent kategorileri değerlendir"
                ],
                "effort": "high"
            },
            "memory_hit_rate": {
                "type": ImprovementType.MEMORY_ENRICHMENT,
                "priority": ImprovementPriority.LOW,
                "title": "Hafıza Kullanımını Artır",
                "actions": [
                    "Memory'e daha fazla fact ekle",
                    "Embedding model'i değerlendir",
                    "Similarity threshold'u ayarla",
                    "Daha fazla konuşma kaydet"
                ],
                "effort": "low"
            }
        }
        
        config = task_configs.get(metric_name)
        if not config:
            return None
        
        return ImprovementTask(
            task_id=self._generate_task_id(),
            improvement_type=config["type"],
            priority=config["priority"],
            title=config["title"],
            description=f"{metric_name}: {metric.current_value:.2%} (hedef: {metric.target_value:.2%})",
            evidence=[
                f"Current: {metric.current_value:.2%}",
                f"Target: {metric.target_value:.2%}",
                f"Trend: {metric.trend}"
            ],
            suggested_actions=config["actions"],
            estimated_effort=config["effort"]
        )
    
    def _create_error_pattern_task(
        self,
        failed_convs: List,
        date: str
    ) -> Optional[ImprovementTask]:
        """Hata pattern görevi"""
        error_types = Counter(f.error_message for f in failed_convs)
        
        return ImprovementTask(
            task_id=self._generate_task_id(),
            improvement_type=ImprovementType.SYSTEM_CONFIG,
            priority=ImprovementPriority.HIGH,
            title=f"Hata Pattern'i Analizi ({date})",
            description=f"{len(failed_convs)} başarısız konuşma tespit edildi",
            evidence=[
                f"Date: {date}",
                f"Total failures: {len(failed_convs)}",
                f"Top error: {error_types.most_common(1)[0] if error_types else 'Unknown'}"
            ],
            suggested_actions=[
                "Hata mesajlarını grupla ve analiz et",
                "Timeout veya resource limit kontrolü yap",
                "Problematik sorgu tiplerini belirle",
                "Error handling'i güçlendir"
            ],
            estimated_effort="medium"
        )
    
    def _create_router_improvement_task(self, pattern) -> Optional[ImprovementTask]:
        """Router improvement görevi"""
        return ImprovementTask(
            task_id=self._generate_task_id(),
            improvement_type=ImprovementType.ROUTER_TRAINING,
            priority=ImprovementPriority.HIGH,
            title="Router Eğitim Verisi Güncelle",
            description=f"{pattern.frequency} düşük güvenlikli yönlendirme",
            evidence=[
                f"Pattern: {pattern.pattern_type}",
                f"Frequency: {pattern.frequency}",
                f"Examples: {', '.join(pattern.examples[:3])}"
            ],
            suggested_actions=[
                "Düşük güvenlikli sorguları manuel etiketle",
                "Router eğitim setine ekle",
                "Fine-tuning yap veya threshold ayarla",
                "Yeni intent kategorisi ekle"
            ],
            estimated_effort="high"
        )
    
    # ============ Re-training Triggers ============
    
    def check_retraining_triggers(self) -> Dict[str, bool]:
        """Re-training gerekip gerekmediğini kontrol et"""
        triggers = {
            "router_retrain": False,
            "lora_retrain": False,
            "memory_rebuild": False
        }
        
        if not self.metrics:
            self.update_metrics()
        
        # Router re-training trigger
        if self.metrics.get("router_confidence", PerformanceMetric("", 1, 1, "stable")).current_value < 0.7:
            triggers["router_retrain"] = True
        
        # LoRA re-training trigger (success rate düşükse)
        if self.metrics.get("success_rate", PerformanceMetric("", 1, 1, "stable")).current_value < 0.85:
            triggers["lora_retrain"] = True
        
        # Memory rebuild trigger (hit rate çok düşükse)
        if self.metrics.get("memory_hit_rate", PerformanceMetric("", 1, 1, "stable")).current_value < 0.1:
            triggers["memory_rebuild"] = True
        
        return triggers
    
    def generate_training_data_suggestions(self) -> List[Dict]:
        """Eğitim verisi önerileri oluştur"""
        suggestions = []
        
        # Son 7 günün training suggestions'larını topla
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_suggestions = self.async_processor.suggest_training_data(date)
            
            for sug in day_suggestions:
                # Benzeri yoksa ekle
                if not any(s.get("category") == sug.category for s in suggestions):
                    suggestions.append(sug.to_dict())
        
        return sorted(suggestions, key=lambda x: x.get("priority", 0), reverse=True)
    
    # ============ Task Management ============
    
    def get_pending_tasks(self, priority_min: int = 1) -> List[ImprovementTask]:
        """Bekleyen görevleri al"""
        return [
            t for t in self.tasks 
            if t.status == "pending" and t.priority.value >= priority_min
        ]
    
    def complete_task(self, task_id: str, notes: str = ""):
        """Görevi tamamla"""
        for task in self.tasks:
            if task.task_id == task_id:
                task.status = "completed"
                self.logger.log_system(f"Task completed: {task_id}", {"notes": notes})
                break
        self._save_state()
    
    def skip_task(self, task_id: str, reason: str = ""):
        """Görevi atla"""
        for task in self.tasks:
            if task.task_id == task_id:
                task.status = "skipped"
                self.logger.log_system(f"Task skipped: {task_id}", {"reason": reason})
                break
        self._save_state()
    
    # ============ Reports ============
    
    def generate_improvement_report(self) -> Dict:
        """Tam iyileştirme raporu"""
        self.update_metrics()
        new_tasks = self.analyze_and_generate_tasks()
        
        return {
            "generated_at": datetime.now().isoformat(),
            "metrics": self.get_metrics_report(),
            "retraining_triggers": self.check_retraining_triggers(),
            "pending_tasks": [t.to_dict() for t in self.get_pending_tasks()],
            "new_tasks": [t.to_dict() for t in new_tasks],
            "training_suggestions": self.generate_training_data_suggestions()
        }
    
    def save_improvement_report(self, report: Optional[Dict] = None) -> Path:
        """Raporu kaydet"""
        if report is None:
            report = self.generate_improvement_report()
        
        filename = f"improvement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.improvement_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return filepath


def create_improvement_pipeline(
    log_dir: str = "./logs",
    data_dir: str = "./data"
) -> SelfImprovementPipeline:
    """Pipeline oluştur"""
    return SelfImprovementPipeline(log_dir=log_dir, data_dir=data_dir)


if __name__ == "__main__":
    # Test
    pipeline = create_improvement_pipeline()
    
    print("🔄 Running Self-Improvement Pipeline...")
    
    # Metrikleri güncelle
    metrics = pipeline.update_metrics(days=1)
    print(f"\n📊 Metrics:")
    for name, metric in metrics.items():
        status = "✅" if not metric.is_below_target else "⚠️"
        print(f"  {status} {name}: {metric.current_value:.2%} (target: {metric.target_value:.2%})")
    
    # Re-training trigger'larını kontrol et
    triggers = pipeline.check_retraining_triggers()
    print(f"\n🔔 Re-training Triggers:")
    for trigger, active in triggers.items():
        status = "🔴 ACTIVE" if active else "🟢 OK"
        print(f"  {status} {trigger}")
    
    # Görevleri oluştur
    tasks = pipeline.analyze_and_generate_tasks(days=1)
    print(f"\n📋 New Improvement Tasks: {len(tasks)}")
    for task in tasks:
        print(f"  [{task.priority.name}] {task.title}")
    
    # Raporu kaydet
    report_path = pipeline.save_improvement_report()
    print(f"\n📁 Report saved: {report_path}")
    
    print("\n✅ Self-Improvement Pipeline test completed!")
