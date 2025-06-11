"""
Pydantic schemas for message validation and API responses
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

from models.message import MessageType, MessageStatus


class MessageTypeSchema(str, Enum):
    """Message type schema for API validation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"


class MessageStatusSchema(str, Enum):
    """Message status schema for API validation"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageCreateRequest(BaseModel):
    """Schema for creating a new message"""
    thread_id: str = Field(..., description="Thread ID this message belongs to")
    content: str = Field(..., min_length=1, max_length=50000, description="Message content")
    message_type: MessageTypeSchema = Field(default=MessageTypeSchema.USER, description="Type of message")
    triggers_execution: bool = Field(default=False, description="Whether this message should trigger execution")
    message_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional message metadata")
    
    @validator('content')
    def content_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Message content cannot be empty')
        return v.strip()


class MessageUpdateRequest(BaseModel):
    """Schema for updating a message"""
    content: Optional[str] = Field(None, min_length=1, max_length=50000, description="Updated message content")
    status: Optional[MessageStatusSchema] = Field(None, description="Updated message status")
    message_metadata: Optional[Dict[str, Any]] = Field(None, description="Updated message metadata")
    
    @validator('content')
    def content_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Message content cannot be empty')
        return v.strip() if v else v


class MessageResponse(BaseModel):
    """Schema for message API responses"""
    id: str
    thread_id: str
    execution_id: Optional[str]
    content: str
    message_type: MessageTypeSchema
    status: MessageStatusSchema
    message_metadata: Optional[Dict[str, Any]]
    sequence_number: int
    triggers_execution: bool
    sent_at: datetime
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Schema for message list API responses"""
    messages: list[MessageResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class MessageProcessingRequest(BaseModel):
    """Schema for triggering message processing"""
    process_immediately: bool = Field(default=False, description="Process message immediately vs queue")
    execution_config: Optional[Dict[str, Any]] = Field(default=None, description="Custom execution configuration")


class MessageProcessingResponse(BaseModel):
    """Schema for message processing response"""
    message_id: str
    status: MessageStatusSchema
    execution_id: Optional[str]
    processing_started: bool
    message: str 