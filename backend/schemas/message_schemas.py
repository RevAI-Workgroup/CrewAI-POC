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


# Chat-specific schemas
class ChatMessageRequest(BaseModel):
    """Schema for chat message requests with CrewAI integration"""
    message: str = Field(..., min_length=1, max_length=10000, description="The message content")
    output: Optional[str] = Field(None, max_length=1000, description="Expected output format or constraints")
    threadId: str = Field(..., description="Thread ID for the conversation")
    
    @validator('message')
    def message_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Message content cannot be empty')
        return v.strip()
    
    @validator('threadId')
    def thread_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Thread ID cannot be empty')
        return v.strip()


class ChatMessageResponse(BaseModel):
    """Schema for chat message responses"""
    message_id: str
    thread_id: str
    user_message: str
    assistant_message: str
    execution_id: Optional[str]
    status: MessageStatusSchema
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]


class ChatStreamChunk(BaseModel):
    """Schema for streaming chat response chunks"""
    content: Optional[str] = Field(None, description="Content chunk for streaming")
    message_id: Optional[str] = Field(None, description="Associated message ID")
    done: bool = Field(default=False, description="Whether streaming is complete")
    error: Optional[str] = Field(None, description="Error message if streaming failed")
    
    class Config:
        # Allow extra fields for future extensibility
        extra = "allow"


class ChatErrorResponse(BaseModel):
    """Schema for chat-specific error responses"""
    error_type: str = Field(..., description="Type of error (graph_validation, crew_execution, etc.)")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    thread_id: Optional[str] = Field(None, description="Associated thread ID if applicable")
    retry_possible: bool = Field(default=False, description="Whether the operation can be retried")


class ChatStatusResponse(BaseModel):
    """Schema for chat status checks"""
    thread_id: str
    is_executing: bool = Field(description="Whether crew is currently executing")
    last_message_at: Optional[datetime] = Field(None, description="Timestamp of last message")
    message_count: int = Field(default=0, description="Total messages in thread")
    crew_status: Optional[str] = Field(None, description="Current crew execution status") 