"""
SSE Event schemas for real-time updates.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field

from models.execution import ExecutionStatus


class SSEEvent(BaseModel):
    """Base SSE event schema."""
    event_type: str = Field(..., description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    data: Dict[str, Any] = Field(..., description="Event data")
    
    def to_sse_format(self) -> str:
        """Convert to SSE format string."""
        return f"event: {self.event_type}\ndata: {self.model_dump_json()}\n\n"


class ExecutionStatusEvent(SSEEvent):
    """Execution status change event."""
    event_type: Literal["execution_status"] = "execution_status"
    
    class Data(BaseModel):
        execution_id: str
        status: ExecutionStatus
        progress_percentage: Optional[int] = None
        current_step: Optional[str] = None
        error_message: Optional[str] = None
        result_data: Optional[Dict[str, Any]] = None
        user_id: str
        graph_id: str
        thread_id: Optional[str] = None
    
    data: Data


class ExecutionProgressEvent(SSEEvent):
    """Execution progress update event."""
    event_type: Literal["execution_progress"] = "execution_progress"
    
    class Data(BaseModel):
        execution_id: str
        progress_percentage: int = Field(..., ge=0, le=100)
        current_step: str
        message: Optional[str] = None
        user_id: str
    
    data: Data


class ExecutionStartEvent(SSEEvent):
    """Execution start event."""
    event_type: Literal["execution_start"] = "execution_start"
    
    class Data(BaseModel):
        execution_id: str
        graph_id: str
        thread_id: Optional[str] = None
        user_id: str
        inputs: Dict[str, Any]
        started_at: datetime
    
    data: Data


class ExecutionCompleteEvent(SSEEvent):
    """Execution completion event."""
    event_type: Literal["execution_complete"] = "execution_complete"
    
    class Data(BaseModel):
        execution_id: str
        result: Any
        duration_seconds: Optional[float] = None
        completed_at: datetime
        user_id: str
    
    data: Data


class ExecutionErrorEvent(SSEEvent):
    """Execution error event."""
    event_type: Literal["execution_error"] = "execution_error"
    
    class Data(BaseModel):
        execution_id: str
        error_message: str
        error_details: Optional[Dict[str, Any]] = None
        user_id: str
        failed_at: datetime
    
    data: Data


class ConnectionEvent(SSEEvent):
    """Client connection event."""
    event_type: Literal["connection"] = "connection"
    
    class Data(BaseModel):
        status: Literal["connected", "disconnected"]
        message: str
        client_id: str
    
    data: Data


class HeartbeatEvent(SSEEvent):
    """Heartbeat event to keep connections alive."""
    event_type: Literal["heartbeat"] = "heartbeat"
    
    class Data(BaseModel):
        message: str = "heartbeat"
        server_time: datetime = Field(default_factory=datetime.utcnow)
    
    data: Data


# Event type mapping for easy creation
EVENT_TYPES = {
    "execution_status": ExecutionStatusEvent,
    "execution_progress": ExecutionProgressEvent,
    "execution_start": ExecutionStartEvent,
    "execution_complete": ExecutionCompleteEvent,
    "execution_error": ExecutionErrorEvent,
    "connection": ConnectionEvent,
    "heartbeat": HeartbeatEvent,
}


def create_sse_event(event_type: str, data: Dict[str, Any]) -> SSEEvent:
    """Create SSE event from type and data."""
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Unknown event type: {event_type}")
    
    event_class = EVENT_TYPES[event_type]
    return event_class(data=data) 