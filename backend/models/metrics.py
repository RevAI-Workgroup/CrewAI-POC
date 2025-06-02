"""
Metrics model for MLFlow integration and execution performance tracking
"""

from enum import Enum
from typing import Dict, Any, Optional, Union
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, JSON, Float, Integer, Boolean, Index
from sqlalchemy.orm import relationship
from .base import BaseModel

class MetricType(str, Enum):
    """Metric type enumeration for different measurement types"""
    COUNTER = "counter"      # Monotonically increasing values (e.g., requests processed)
    GAUGE = "gauge"          # Point-in-time values (e.g., memory usage, CPU %)
    HISTOGRAM = "histogram"  # Distribution of values (e.g., response times)
    TIMER = "timer"          # Duration measurements
    RATE = "rate"           # Rate of change over time

class MetricCategory(str, Enum):
    """Metric category for organization and filtering"""
    PERFORMANCE = "performance"    # Execution performance metrics
    RESOURCE = "resource"         # Resource usage (CPU, memory, disk)
    BUSINESS = "business"         # Business logic metrics
    SYSTEM = "system"            # System-level metrics
    CUSTOM = "custom"            # User-defined metrics

class Metric(BaseModel):
    """
    Model for storing MLFlow metrics and execution performance data.
    Supports various metric types and enables analytics and monitoring.
    """
    
    # Override id field to use String(36) to match migration schema
    id = Column(String(36), primary_key=True, index=True, nullable=False)
    
    # Foreign key relationships
    execution_id = Column(String(36), ForeignKey("executions.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Metric identification
    metric_name = Column(String(200), nullable=False, index=True)
    metric_type = Column(String(20), default=MetricType.GAUGE, nullable=False)
    category = Column(String(20), default=MetricCategory.PERFORMANCE, nullable=False)
    
    # Metric value and data
    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=True)  # e.g., "seconds", "bytes", "percent"
    
    # Timing information
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    step = Column(Integer, nullable=True)  # MLFlow step number for tracking progression
    
    # Metadata and context
    tags = Column(JSON, nullable=True)  # Key-value tags for filtering and grouping
    metric_metadata = Column(JSON, nullable=True)  # Additional metric metadata (renamed from 'metadata' due to SQLAlchemy reserved name)
    description = Column(Text, nullable=True)  # Human-readable description
    
    # Aggregation support
    is_aggregated = Column(Boolean, default=False, nullable=False)
    aggregation_method = Column(String(20), nullable=True)  # "sum", "avg", "min", "max", "count"
    aggregation_window = Column(String(50), nullable=True)  # "1m", "5m", "1h", "1d"
    
    # MLFlow integration
    mlflow_run_id = Column(String(100), nullable=True, index=True)  # MLFlow run identifier
    mlflow_experiment_id = Column(String(100), nullable=True)  # MLFlow experiment identifier
    
    # Relationships
    execution = relationship("Execution", back_populates="metrics")
    user = relationship("User", back_populates="metrics")
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_metrics_execution_name', 'execution_id', 'metric_name'),
        Index('idx_metrics_timestamp_type', 'timestamp', 'metric_type'),
        Index('idx_metrics_category_name', 'category', 'metric_name'),
        Index('idx_metrics_mlflow_run', 'mlflow_run_id'),
    )
    
    def set_metric_type(self, metric_type: MetricType) -> None:
        """Set metric type with validation"""
        if not isinstance(metric_type, MetricType):
            try:
                metric_type = MetricType(metric_type)
            except ValueError:
                raise ValueError(f"Invalid metric type: {metric_type}")
        
        self.metric_type = metric_type.value
    
    def set_category(self, category: MetricCategory) -> None:
        """Set metric category with validation"""
        if not isinstance(category, MetricCategory):
            try:
                category = MetricCategory(category)
            except ValueError:
                raise ValueError(f"Invalid metric category: {category}")
        
        self.category = category.value
    
    def add_tag(self, key: str, value: Union[str, int, float, bool]) -> None:
        """Add a tag to the metric"""
        if not isinstance(key, str):
            raise ValueError("Tag key must be a string")
        
        current_tags = getattr(self, 'tags', None) or {}
        current_tags[key] = value
        self.tags = current_tags
    
    def remove_tag(self, key: str) -> None:
        """Remove a tag from the metric"""
        current_tags = getattr(self, 'tags', None) or {}
        if key in current_tags:
            del current_tags[key]
            self.tags = current_tags
    
    def get_tag(self, key: str, default: Any = None) -> Any:
        """Get a tag value"""
        current_tags = getattr(self, 'tags', None) or {}
        return current_tags.get(key, default)
    
    def get_tags(self) -> Dict[str, Any]:
        """Get all tags"""
        return getattr(self, 'tags', None) or {}
    
    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set metric metadata"""
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")
        self.metric_metadata = metadata
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metric metadata"""
        return getattr(self, 'metric_metadata', None) or {}
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add a metadata entry"""
        if not isinstance(key, str):
            raise ValueError("Metadata key must be a string")
        
        current_metadata = getattr(self, 'metric_metadata', None) or {}
        current_metadata[key] = value
        self.metric_metadata = current_metadata
    
    def set_mlflow_info(self, run_id: str, experiment_id: Optional[str] = None) -> None:
        """Set MLFlow run and experiment information"""
        if not isinstance(run_id, str):
            raise ValueError("MLFlow run ID must be a string")
        
        self.mlflow_run_id = run_id
        if experiment_id:
            self.mlflow_experiment_id = experiment_id
    
    def set_aggregation(self, method: str, window: Optional[str] = None) -> None:
        """Set aggregation method and window"""
        valid_methods = ["sum", "avg", "min", "max", "count", "median", "p95", "p99"]
        if method not in valid_methods:
            raise ValueError(f"Invalid aggregation method: {method}. Must be one of {valid_methods}")
        
        self.is_aggregated = True
        self.aggregation_method = method
        if window:
            self.aggregation_window = window
    
    def is_counter(self) -> bool:
        """Check if metric is a counter type"""
        return getattr(self, 'metric_type', None) == MetricType.COUNTER.value
    
    def is_gauge(self) -> bool:
        """Check if metric is a gauge type"""
        return getattr(self, 'metric_type', None) == MetricType.GAUGE.value
    
    def is_histogram(self) -> bool:
        """Check if metric is a histogram type"""
        return getattr(self, 'metric_type', None) == MetricType.HISTOGRAM.value
    
    def is_timer(self) -> bool:
        """Check if metric is a timer type"""
        return getattr(self, 'metric_type', None) == MetricType.TIMER.value
    
    def is_rate(self) -> bool:
        """Check if metric is a rate type"""
        return getattr(self, 'metric_type', None) == MetricType.RATE.value
    
    def get_formatted_value(self) -> str:
        """Get formatted value with unit"""
        value = getattr(self, 'value', 0)
        unit = getattr(self, 'unit', None)
        
        if unit:
            return f"{value} {unit}"
        return str(value)
    
    def get_execution_id(self) -> Optional[str]:
        """Get the execution ID this metric belongs to"""
        return getattr(self, 'execution_id', None)
    
    def get_user_id(self) -> Optional[str]:
        """Get the user ID this metric belongs to"""
        return getattr(self, 'user_id', None)
    
    def is_owned_by(self, user_id: str) -> bool:
        """Check if metric is owned by the specified user"""
        return getattr(self, 'user_id', None) == user_id
    
    def can_be_accessed_by(self, user_id: str) -> bool:
        """Check if metric can be accessed by the specified user"""
        # Users can access their own metrics
        if self.is_owned_by(user_id):
            return True
        
        # Check if user can access the associated execution
        execution = getattr(self, 'execution', None)
        if execution and hasattr(execution, 'can_be_accessed_by'):
            return execution.can_be_accessed_by(user_id)
        
        return False
    
    def to_mlflow_format(self) -> Dict[str, Any]:
        """Convert metric to MLFlow format for logging"""
        return {
            "key": getattr(self, 'metric_name', ''),
            "value": getattr(self, 'value', 0),
            "timestamp": int(getattr(self, 'timestamp', datetime.utcnow()).timestamp() * 1000),
            "step": getattr(self, 'step', None)
        }
    
    @classmethod
    def create_performance_metric(cls, execution_id: str, user_id: str, name: str, 
                                value: float, unit: Optional[str] = None, 
                                step: Optional[int] = None) -> 'Metric':
        """Create a performance metric"""
        return cls(
            execution_id=execution_id,
            user_id=user_id,
            metric_name=name,
            metric_type=MetricType.GAUGE,
            category=MetricCategory.PERFORMANCE,
            value=value,
            unit=unit,
            step=step
        )
    
    @classmethod
    def create_resource_metric(cls, execution_id: str, user_id: str, name: str, 
                             value: float, unit: Optional[str] = None) -> 'Metric':
        """Create a resource usage metric"""
        return cls(
            execution_id=execution_id,
            user_id=user_id,
            metric_name=name,
            metric_type=MetricType.GAUGE,
            category=MetricCategory.RESOURCE,
            value=value,
            unit=unit
        )
    
    @classmethod
    def create_timer_metric(cls, execution_id: str, user_id: str, name: str, 
                          duration_seconds: float, step: Optional[int] = None) -> 'Metric':
        """Create a timer metric for duration measurements"""
        return cls(
            execution_id=execution_id,
            user_id=user_id,
            metric_name=name,
            metric_type=MetricType.TIMER,
            category=MetricCategory.PERFORMANCE,
            value=duration_seconds,
            unit="seconds",
            step=step
        )
    
    def __repr__(self) -> str:
        return (f"<Metric(id={getattr(self, 'id', None)}, "
                f"name='{getattr(self, 'metric_name', '')}', "
                f"type='{getattr(self, 'metric_type', '')}', "
                f"value={getattr(self, 'value', 0)}, "
                f"execution_id='{getattr(self, 'execution_id', '')}')>") 