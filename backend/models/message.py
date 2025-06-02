"""
Message model for chat functionality and execution linking
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, JSON, Integer, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class MessageType(str, Enum):
    """Message type enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"

class MessageStatus(str, Enum):
    """Message status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Message(BaseModel):
    """
    Model for messages within conversation threads.
    Messages can trigger crew executions and link to execution logs.
    """
    
    # Foreign key relationships
    thread_id = Column(String(36), ForeignKey("threads.id"), nullable=False, index=True)
    execution_id = Column(String(36), ForeignKey("executions.id"), nullable=True, index=True)
    
    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default=MessageType.USER, nullable=False)
    
    # Message metadata (renamed from 'metadata' due to SQLAlchemy reserved name)
    status = Column(String(20), default=MessageStatus.PENDING, nullable=False)
    message_metadata = Column(JSON, nullable=True)
    
    # Order within thread
    sequence_number = Column(Integer, nullable=False)
    
    # Processing flags
    triggers_execution = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    thread = relationship("Thread", back_populates="messages")
    execution = relationship("Execution", foreign_keys=[execution_id], back_populates="messages")
    
    def set_message_type(self, message_type: MessageType) -> None:
        """Set message type with validation"""
        if not isinstance(message_type, MessageType):
            try:
                message_type = MessageType(message_type)
            except ValueError:
                raise ValueError(f"Invalid message type: {message_type}")
        
        self.message_type = message_type.value
    
    def set_status(self, status: MessageStatus) -> None:
        """Set message status with validation"""
        if not isinstance(status, MessageStatus):
            try:
                status = MessageStatus(status)
            except ValueError:
                raise ValueError(f"Invalid message status: {status}")
        
        old_status = getattr(self, 'status', None)
        self.status = status.value
        
        # Update processed timestamp when status changes to completed/failed
        if old_status != status.value and status in [MessageStatus.COMPLETED, MessageStatus.FAILED]:
            self.processed_at = datetime.utcnow()
    
    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set message metadata"""
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("Message metadata must be a dictionary")
        self.message_metadata = metadata
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get message metadata"""
        metadata = getattr(self, 'message_metadata', None)
        return metadata if metadata is not None else {}
    
    def link_execution(self, execution_id: str) -> None:
        """Link message to an execution"""
        self.execution_id = execution_id
        self.triggers_execution = True
    
    def unlink_execution(self) -> None:
        """Unlink message from execution"""
        self.execution_id = None
        self.triggers_execution = False
    
    def mark_processing(self) -> None:
        """Mark message as processing"""
        self.set_status(MessageStatus.PROCESSING)
    
    def mark_completed(self) -> None:
        """Mark message as completed"""
        self.set_status(MessageStatus.COMPLETED)
    
    def mark_failed(self) -> None:
        """Mark message as failed"""
        self.set_status(MessageStatus.FAILED)
    
    def is_user_message(self) -> bool:
        """Check if this is a user message"""
        return getattr(self, 'message_type', None) == MessageType.USER.value
    
    def is_assistant_message(self) -> bool:
        """Check if this is an assistant message"""
        return getattr(self, 'message_type', None) == MessageType.ASSISTANT.value
    
    def is_system_message(self) -> bool:
        """Check if this is a system message"""
        return getattr(self, 'message_type', None) == MessageType.SYSTEM.value
    
    def is_error_message(self) -> bool:
        """Check if this is an error message"""
        return getattr(self, 'message_type', None) == MessageType.ERROR.value
    
    def is_completed(self) -> bool:
        """Check if message processing is completed"""
        return getattr(self, 'status', None) == MessageStatus.COMPLETED.value
    
    def is_pending(self) -> bool:
        """Check if message is pending processing"""
        return getattr(self, 'status', None) == MessageStatus.PENDING.value
    
    def is_processing(self) -> bool:
        """Check if message is currently being processed"""
        return getattr(self, 'status', None) == MessageStatus.PROCESSING.value
    
    def is_failed(self) -> bool:
        """Check if message processing failed"""
        return getattr(self, 'status', None) == MessageStatus.FAILED.value
    
    def has_execution(self) -> bool:
        """Check if message is linked to an execution"""
        return getattr(self, 'execution_id', None) is not None
    
    def get_user_id(self) -> Optional[str]:
        """Get the user ID through thread and graph relationships"""
        thread = getattr(self, 'thread', None)
        if thread:
            return thread.get_user_id()
        return None
    
    def is_owned_by(self, user_id: str) -> bool:
        """Check if this message belongs to the given user"""
        thread = getattr(self, 'thread', None)
        if thread:
            return thread.is_owned_by(user_id)
        return False
    
    def can_be_accessed_by(self, user_id: str) -> bool:
        """Check if this message can be accessed by the given user"""
        thread = getattr(self, 'thread', None)
        if thread:
            return thread.can_be_accessed_by(user_id)
        return False
    
    def __repr__(self) -> str:
        return f"<Message(id={getattr(self, 'id', None)}, thread_id='{self.thread_id}', type='{getattr(self, 'message_type', 'unknown')}', status='{getattr(self, 'status', 'unknown')}')>" 