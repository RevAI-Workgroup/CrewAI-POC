from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class ThreadStatusSchema(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class ThreadCreateRequest(BaseModel):
    graph_id: str = Field(..., description="Graph ID")
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    thread_config: Optional[Dict[str, Any]] = None

class ThreadUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[ThreadStatusSchema] = None
    thread_config: Optional[Dict[str, Any]] = None

class ThreadResponse(BaseModel):
    id: str
    graph_id: str
    name: str
    description: Optional[str]
    status: ThreadStatusSchema
    thread_config: Optional[Dict[str, Any]]
    last_activity_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    class Config:
        from_attributes = True

class ThreadListResponse(BaseModel):
    threads: List[ThreadResponse]
    total: int
    graph_id: str 