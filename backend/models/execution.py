"""
Execution model for tracking CrewAI crew execution lifecycle
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, JSON, Integer, Boolean, Float
from sqlalchemy.orm import relationship
from .base import BaseModel

class ExecutionStatus(str, Enum):
    """Execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class ExecutionPriority(str, Enum):
    """Execution priority enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class Execution(BaseModel):
    """
    Model for tracking CrewAI crew execution lifecycle, results, and performance.
    Each execution represents a single run of a crew based on a graph configuration.
    """
    
    # Override id field to use String(36) to match migration schema
    id = Column(String(36), primary_key=True, index=True, nullable=False)
    
    # Foreign key relationships
    graph_id = Column(String(36), ForeignKey("graphs.id"), nullable=False, index=True)
    trigger_message_id = Column(String(36), ForeignKey("messages.id"), nullable=True, index=True)
    
    # Execution metadata
    execution_name = Column(String(200), nullable=True)  # Optional human-readable name
    status = Column(String(20), default=ExecutionStatus.PENDING, nullable=False)
    priority = Column(String(20), default=ExecutionPriority.NORMAL, nullable=False)
    
    # Execution configuration
    execution_config = Column(JSON, nullable=True)  # Runtime configuration overrides
    
    # Timing information
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Results and output
    result_data = Column(JSON, nullable=True)  # Final execution results
    output_logs = Column(Text, nullable=True)  # Execution logs and output
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)  # Detailed error information
    
    # Performance metrics
    metrics = Column(JSON, nullable=True)  # Performance and usage metrics
    
    # Execution control
    is_cancelled = Column(Boolean, default=False, nullable=False)
    cancellation_reason = Column(String(500), nullable=True)
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0, nullable=False)  # 0-100
    current_step = Column(String(200), nullable=True)  # Current execution step
    
    # Relationships
    graph = relationship("Graph", back_populates="executions")
    trigger_message = relationship("Message", foreign_keys=[trigger_message_id])
    messages = relationship("Message", foreign_keys="Message.execution_id", back_populates="execution")
    metrics = relationship("Metric", back_populates="execution")
    
    def set_status(self, status: ExecutionStatus) -> None:
        """Set execution status with validation and timestamp updates"""
        if not isinstance(status, ExecutionStatus):
            try:
                status = ExecutionStatus(status)
            except ValueError:
                raise ValueError(f"Invalid execution status: {status}")
        
        old_status = getattr(self, 'status', None)
        self.status = status.value
        
        # Update timestamps based on status changes
        now = datetime.utcnow()
        
        if old_status != status.value:
            started_at = getattr(self, 'started_at', None)
            completed_at = getattr(self, 'completed_at', None)
            
            if status == ExecutionStatus.RUNNING and not started_at:
                self.started_at = now
            elif status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT]:
                if not completed_at:
                    self.completed_at = now
                    # Calculate duration if we have start time
                    if started_at:
                        self.duration_seconds = (now - started_at).total_seconds()
    
    def set_priority(self, priority: ExecutionPriority) -> None:
        """Set execution priority with validation"""
        if not isinstance(priority, ExecutionPriority):
            try:
                priority = ExecutionPriority(priority)
            except ValueError:
                raise ValueError(f"Invalid execution priority: {priority}")
        
        self.priority = priority.value
    
    def start_execution(self) -> None:
        """Mark execution as started"""
        self.set_status(ExecutionStatus.RUNNING)
        self.progress_percentage = 0
    
    def complete_execution(self, result_data: Optional[Dict[str, Any]] = None) -> None:
        """Mark execution as completed with optional result data"""
        self.set_status(ExecutionStatus.COMPLETED)
        self.progress_percentage = 100
        if result_data:
            self.result_data = result_data
    
    def fail_execution(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> None:
        """Mark execution as failed with error information"""
        self.set_status(ExecutionStatus.FAILED)
        self.error_message = error_message
        if error_details:
            self.error_details = error_details
    
    def cancel_execution(self, reason: Optional[str] = None) -> None:
        """Cancel the execution with optional reason"""
        self.set_status(ExecutionStatus.CANCELLED)
        self.is_cancelled = True
        if reason:
            self.cancellation_reason = reason
    
    def update_progress(self, percentage: int, current_step: Optional[str] = None) -> None:
        """Update execution progress"""
        if not 0 <= percentage <= 100:
            raise ValueError("Progress percentage must be between 0 and 100")
        
        self.progress_percentage = percentage
        if current_step:
            self.current_step = current_step
    
    def set_execution_config(self, config: Dict[str, Any]) -> None:
        """Set execution configuration"""
        if config is not None and not isinstance(config, dict):
            raise ValueError("Execution config must be a dictionary")
        self.execution_config = config
    
    def get_execution_config(self) -> Dict[str, Any]:
        """Get execution configuration"""
        config = getattr(self, 'execution_config', None)
        return config if config is not None else {}
    
    def set_metrics(self, metrics: Dict[str, Any]) -> None:
        """Set performance metrics"""
        if metrics is not None and not isinstance(metrics, dict):
            raise ValueError("Metrics must be a dictionary")
        self.metrics = metrics
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        metrics = getattr(self, 'metrics', None)
        return metrics if metrics is not None else {}
    
    def add_log_entry(self, log_entry: str) -> None:
        """Add a log entry to the execution logs"""
        current_logs = getattr(self, 'output_logs', None) or ""
        timestamp = datetime.utcnow().isoformat()
        new_entry = f"[{timestamp}] {log_entry}\n"
        self.output_logs = current_logs + new_entry
    
    def is_running(self) -> bool:
        """Check if execution is currently running"""
        return getattr(self, 'status', None) == ExecutionStatus.RUNNING.value
    
    def is_completed(self) -> bool:
        """Check if execution is completed"""
        return getattr(self, 'status', None) == ExecutionStatus.COMPLETED.value
    
    def is_failed(self) -> bool:
        """Check if execution failed"""
        return getattr(self, 'status', None) == ExecutionStatus.FAILED.value
    
    def is_pending(self) -> bool:
        """Check if execution is pending"""
        return getattr(self, 'status', None) == ExecutionStatus.PENDING.value
    
    def is_finished(self) -> bool:
        """Check if execution is in a finished state"""
        status = getattr(self, 'status', None)
        return status in [ExecutionStatus.COMPLETED.value, ExecutionStatus.FAILED.value, 
                         ExecutionStatus.CANCELLED.value, ExecutionStatus.TIMEOUT.value]
    
    def get_duration_minutes(self) -> Optional[float]:
        """Get execution duration in minutes"""
        duration = getattr(self, 'duration_seconds', None)
        return duration / 60.0 if duration is not None else None
    
    def get_user_id(self) -> Optional[str]:
        """Get the user ID through graph relationship"""
        graph = getattr(self, 'graph', None)
        if graph:
            return getattr(graph, 'user_id', None)
        return None
    
    def is_owned_by(self, user_id: str) -> bool:
        """Check if this execution belongs to the given user"""
        graph = getattr(self, 'graph', None)
        if graph:
            return graph.is_owned_by(user_id)
        return False
    
    def can_be_accessed_by(self, user_id: str) -> bool:
        """Check if this execution can be accessed by the given user"""
        graph = getattr(self, 'graph', None)
        if graph:
            return graph.can_be_accessed_by(user_id)
        return False
    
    def __repr__(self) -> str:
        return f"<Execution(id={getattr(self, 'id', None)}, graph_id='{self.graph_id}', status='{getattr(self, 'status', 'unknown')}', progress={getattr(self, 'progress_percentage', 0)}%)>" 