"""
Tests for chat message schemas
"""
import pytest
from pydantic import ValidationError
from datetime import datetime

from schemas.message_schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatStreamChunk,
    ChatErrorResponse,
    ChatStatusResponse,
    MessageStatusSchema
)


class TestChatMessageRequest:
    """Tests for ChatMessageRequest schema"""
    
    def test_valid_chat_message_request(self):
        """Test valid chat message request"""
        data = {
            "message": "Hello, how can you help me?",
            "output": "Please provide a detailed response",
            "threadId": "thread-123"
        }
        
        request = ChatMessageRequest(**data)
        
        assert request.message == "Hello, how can you help me?"
        assert request.output == "Please provide a detailed response"
        assert request.threadId == "thread-123"
    
    def test_chat_message_request_without_output(self):
        """Test chat message request without optional output field"""
        data = {
            "message": "Hello, how can you help me?",
            "threadId": "thread-123"
        }
        
        request = ChatMessageRequest(**data)
        
        assert request.message == "Hello, how can you help me?"
        assert request.output is None
        assert request.threadId == "thread-123"
    
    def test_empty_message_validation(self):
        """Test that empty message raises validation error"""
        data = {
            "message": "",
            "threadId": "thread-123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ChatMessageRequest(**data)
        
        assert "String should have at least 1 character" in str(exc_info.value)
    
    def test_empty_thread_id_validation(self):
        """Test that empty thread ID raises validation error"""
        data = {
            "message": "Hello",
            "threadId": ""
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ChatMessageRequest(**data)
        
        assert "Thread ID cannot be empty" in str(exc_info.value)
    
    def test_message_too_long(self):
        """Test that message exceeding max length raises validation error"""
        long_message = "x" * 10001  # Exceeds max_length=10000
        data = {
            "message": long_message,
            "threadId": "thread-123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ChatMessageRequest(**data)
        
        assert "String should have at most 10000 characters" in str(exc_info.value)


class TestChatStreamChunk:
    """Tests for ChatStreamChunk schema"""
    
    def test_valid_stream_chunk(self):
        """Test valid stream chunk"""
        data = {
            "content": "Hello, this is a chunk",
            "message_id": "msg-123",
            "done": False
        }
        
        chunk = ChatStreamChunk(**data)
        
        assert chunk.content == "Hello, this is a chunk"
        assert chunk.message_id == "msg-123"
        assert chunk.done is False
        assert chunk.error is None
    
    def test_stream_chunk_completion(self):
        """Test stream chunk marking completion"""
        data = {
            "content": "Final chunk",
            "message_id": "msg-123",
            "done": True
        }
        
        chunk = ChatStreamChunk(**data)
        
        assert chunk.done is True
    
    def test_stream_chunk_error(self):
        """Test stream chunk with error"""
        data = {
            "error": "Execution failed",
            "done": True
        }
        
        chunk = ChatStreamChunk(**data)
        
        assert chunk.error == "Execution failed"
        assert chunk.done is True
        assert chunk.content is None


class TestChatErrorResponse:
    """Tests for ChatErrorResponse schema"""
    
    def test_valid_error_response(self):
        """Test valid error response"""
        data = {
            "error_type": "graph_validation",
            "error_message": "Graph must have exactly one crew node",
            "details": {"crew_count": 2},
            "thread_id": "thread-123",
            "retry_possible": False
        }
        
        error = ChatErrorResponse(**data)
        
        assert error.error_type == "graph_validation"
        assert error.error_message == "Graph must have exactly one crew node"
        assert error.details == {"crew_count": 2}
        assert error.thread_id == "thread-123"
        assert error.retry_possible is False
    
    def test_minimal_error_response(self):
        """Test error response with only required fields"""
        data = {
            "error_type": "crew_execution",
            "error_message": "CrewAI execution failed"
        }
        
        error = ChatErrorResponse(**data)
        
        assert error.error_type == "crew_execution"
        assert error.error_message == "CrewAI execution failed"
        assert error.details is None
        assert error.thread_id is None
        assert error.retry_possible is False


class TestChatStatusResponse:
    """Tests for ChatStatusResponse schema"""
    
    def test_valid_status_response(self):
        """Test valid status response"""
        data = {
            "thread_id": "thread-123",
            "is_executing": True,
            "last_message_at": datetime.now(),
            "message_count": 5,
            "crew_status": "running"
        }
        
        status = ChatStatusResponse(**data)
        
        assert status.thread_id == "thread-123"
        assert status.is_executing is True
        assert status.message_count == 5
        assert status.crew_status == "running" 