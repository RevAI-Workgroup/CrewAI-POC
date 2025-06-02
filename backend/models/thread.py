"""
Thread model for managing conversation threads within graphs
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel

class ThreadStatus(str, Enum):
    """Thread status enumeration"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class Thread(BaseModel):
    """
    Model for conversation threads within graphs.
    A thread represents a workspace or conversation session where users 
    can interact with a specific graph instance.
    """
    
    # Foreign key to graph
    graph_id = Column(String(36), ForeignKey("graphs.id"), nullable=False, index=True)
    
    # Thread metadata
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=ThreadStatus.ACTIVE, nullable=False)
    
    # Thread configuration as JSON
    thread_config = Column(JSON, nullable=True)
    
    # Activity tracking
    last_activity_at = Column(DateTime, nullable=True)
    
    # Status management
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    graph = relationship("Graph", back_populates="threads")
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")
    
    def set_thread_config(self, config: Dict[str, Any]) -> None:
        """Set thread configuration"""
        if config is not None and not isinstance(config, dict):
            raise ValueError("Thread config must be a dictionary")
        self.thread_config = config
    
    def get_thread_config(self) -> Dict[str, Any]:
        """Get thread configuration"""
        config = getattr(self, 'thread_config', None)
        return config if config is not None else {}
    
    def update_last_activity(self) -> None:
        """Update the last activity timestamp to now"""
        self.last_activity_at = datetime.utcnow()
    
    def set_status(self, status: ThreadStatus) -> None:
        """Set thread status with validation"""
        if not isinstance(status, ThreadStatus):
            # Try to convert string to ThreadStatus
            try:
                status = ThreadStatus(status)
            except ValueError:
                raise ValueError(f"Invalid thread status: {status}")
        
        old_status = getattr(self, 'status', None)
        self.status = status.value
        
        # Update activity when status changes
        if old_status != status.value:
            self.update_last_activity()
    
    def archive(self) -> None:
        """Archive the thread"""
        self.set_status(ThreadStatus.ARCHIVED)
        self.update_last_activity()
    
    def activate(self) -> None:
        """Activate the thread"""
        self.set_status(ThreadStatus.ACTIVE)
        self.update_last_activity()
    
    def soft_delete(self) -> None:
        """Soft delete the thread"""
        self.set_status(ThreadStatus.DELETED)
        self.is_active = False
        self.update_last_activity()
    
    def is_owned_by(self, user_id: str) -> bool:
        """Check if this thread belongs to the given user (through graph ownership)"""
        graph = getattr(self, 'graph', None)
        if graph:
            return graph.is_owned_by(user_id)
        return False
    
    def can_be_accessed_by(self, user_id: str) -> bool:
        """Check if this thread can be accessed by the given user"""
        graph = getattr(self, 'graph', None)
        if graph:
            return graph.can_be_accessed_by(user_id)
        return False
    
    def validate_graph_exists(self) -> bool:
        """Validate that the associated graph exists and is active"""
        graph = getattr(self, 'graph', None)
        if not graph:
            return False
        
        # Check if graph is active
        if not getattr(graph, 'is_active', True):
            return False
        
        return True
    
    def get_message_count(self) -> int:
        """Get the number of messages in this thread"""
        messages = getattr(self, 'messages', [])
        return len(messages) if messages else 0
    
    def is_status(self, status: ThreadStatus) -> bool:
        """Check if thread has the specified status"""
        current_status = getattr(self, 'status', ThreadStatus.ACTIVE)
        if isinstance(status, ThreadStatus):
            return current_status == status.value
        return current_status == status
    
    def is_active_status(self) -> bool:
        """Check if thread is in active status"""
        return self.is_status(ThreadStatus.ACTIVE) and getattr(self, 'is_active', True)
    
    def get_user_id(self) -> Optional[str]:
        """Get the user ID through graph relationship"""
        graph = getattr(self, 'graph', None)
        if graph:
            return getattr(graph, 'user_id', None)
        return None
    
    def __repr__(self) -> str:
        return f"<Thread(id={getattr(self, 'id', None)}, name='{self.name}', graph_id='{self.graph_id}', status='{getattr(self, 'status', 'unknown')}')>" 