"""
Tests for chat error handling functionality.
Tests the comprehensive error handling system for graph translation and crew execution.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from exceptions.chat_exceptions import (
    ChatError, GraphTranslationError, CrewExecutionError, StreamingError, ChatContextError,
    ChatErrorCode, ErrorHandler,
    create_graph_structure_error, create_multiple_crews_error, create_agent_config_error,
    create_crew_execution_error, create_streaming_error, create_execution_already_running_error
)
from services.graph_translation import GraphTranslationService
from models.graph import Graph
from models.thread import Thread
from models.user import User


class TestChatExceptions:
    """Test chat-specific exception classes."""
    
    def test_graph_translation_error_creation(self):
        """Test creating graph translation errors with proper context."""
        error = create_graph_structure_error("graph-123", {"field": "nodes"})
        
        assert isinstance(error, GraphTranslationError)
        assert error.chat_error_code == ChatErrorCode.GRAPH_STRUCTURE_INVALID
        assert "graph-123" in error.message
        assert error.details["graph_id"] == "graph-123"
        assert error.details["field"] == "nodes"
        assert not error.recoverable
        
    def test_multiple_crews_error(self):
        """Test error for multiple crews detected."""
        error = create_multiple_crews_error("graph-456", 3)
        
        assert error.chat_error_code == ChatErrorCode.MULTIPLE_CREWS_DETECTED
        assert "3 crews" in error.message
        assert error.details["crew_count"] == 3
        assert "exactly one crew" in error.user_message
        
    def test_agent_config_error(self):
        """Test error for missing agent configuration."""
        missing_fields = ["role", "backstory"]
        error = create_agent_config_error("graph-789", "agent-1", missing_fields)
        
        assert error.chat_error_code == ChatErrorCode.AGENT_CONFIG_MISSING
        assert "agent-1" in error.message
        assert error.details["missing_fields"] == missing_fields
        assert "incomplete" in error.user_message
        
    def test_crew_execution_error(self):
        """Test crew execution error handling."""
        original_error = Exception("CrewAI timeout occurred")
        error = create_crew_execution_error("exec-123", original_error)
        
        assert isinstance(error, CrewExecutionError)
        assert error.chat_error_code == ChatErrorCode.CREWAI_EXECUTION_TIMEOUT
        assert error.details["original_error"] == "CrewAI timeout occurred"
        assert error.recoverable
        assert "too long to respond" in error.user_message
        
    def test_streaming_error(self):
        """Test streaming error handling."""
        original_error = ConnectionError("Connection lost")
        error = create_streaming_error("thread-123", "msg-456", original_error)
        
        assert isinstance(error, StreamingError)
        assert error.chat_error_code == ChatErrorCode.STREAM_CONNECTION_LOST
        assert error.details["thread_id"] == "thread-123"
        assert error.details["message_id"] == "msg-456"
        assert "refresh and try again" in error.user_message
        
    def test_execution_already_running_error(self):
        """Test concurrent execution prevention error."""
        error = create_execution_already_running_error("graph-999")
        
        assert isinstance(error, ChatContextError)
        assert error.chat_error_code == ChatErrorCode.EXECUTION_ALREADY_RUNNING
        assert "already running" in error.user_message
        assert not error.recoverable


class TestErrorHandler:
    """Test the centralized error handling functionality."""
    
    def test_handle_graph_translation_error_multiple_crews(self):
        """Test handling multiple crews error."""
        original_error = Exception("Graph has 2 crews, but chat requires exactly 1")
        
        result = ErrorHandler.handle_graph_translation_error(
            original_error, "graph-123", "test_context"
        )
        
        assert isinstance(result, GraphTranslationError)
        assert result.chat_error_code == ChatErrorCode.MULTIPLE_CREWS_DETECTED
        assert result.details["crew_count"] == 2
        
    def test_handle_graph_translation_error_missing_agent(self):
        """Test handling missing agent fields error."""
        original_error = Exception("Agent missing required field: role")
        
        result = ErrorHandler.handle_graph_translation_error(
            original_error, "graph-456", "test_context"
        )
        
        assert result.chat_error_code == ChatErrorCode.AGENT_CONFIG_MISSING
        assert "missing_fields" in result.details
        
    def test_handle_crew_execution_error(self):
        """Test handling crew execution errors."""
        original_error = RuntimeError("Agent failed to execute task")
        
        result = ErrorHandler.handle_crew_execution_error(
            original_error, "exec-789", "test_context"
        )
        
        assert isinstance(result, CrewExecutionError)
        assert result.chat_error_code == ChatErrorCode.CREWAI_AGENT_FAILED
        assert result.details["execution_id"] == "exec-789"
        
    def test_handle_streaming_error(self):
        """Test handling streaming errors."""
        original_error = BrokenPipeError("Pipe broken")
        
        result = ErrorHandler.handle_streaming_error(
            original_error, "thread-111", "msg-222", "test_context"
        )
        
        assert isinstance(result, StreamingError)
        assert result.details["thread_id"] == "thread-111"
        assert result.details["message_id"] == "msg-222"
        
    def test_get_user_error_response(self):
        """Test formatting error response for frontend."""
        error = create_graph_structure_error("graph-123")
        
        response = ErrorHandler.get_user_error_response(error)
        
        assert response["error"] is True
        assert "message" in response
        assert "error_code" in response
        assert "severity" in response
        assert "recoverable" in response
        assert "retry_recommended" in response


class TestGraphTranslationServiceErrorHandling:
    """Test enhanced error handling in GraphTranslationService."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def translation_service(self, mock_db):
        """Create translation service with mock DB."""
        return GraphTranslationService(mock_db)
    
    @pytest.fixture
    def sample_graph(self):
        """Create a sample graph for testing."""
        graph = Mock(spec=Graph)
        graph.id = "test-graph-123"
        return graph
    
    def test_translate_graph_no_data(self, translation_service, sample_graph):
        """Test error when graph has no data."""
        sample_graph.graph_data = None
        
        with pytest.raises(GraphTranslationError) as exc_info:
            translation_service.translate_graph(sample_graph)
        
        error = exc_info.value
        assert error.chat_error_code == ChatErrorCode.GRAPH_STRUCTURE_INVALID
        assert "no data" in error.details["error"]
        
    def test_translate_graph_invalid_data_type(self, translation_service, sample_graph):
        """Test error when graph data is not a dictionary."""
        sample_graph.graph_data = "invalid_data"
        
        with pytest.raises(GraphTranslationError) as exc_info:
            translation_service.translate_graph(sample_graph)
        
        error = exc_info.value
        assert error.details["actual_type"] == "str"
        
    def test_translate_graph_missing_nodes(self, translation_service, sample_graph):
        """Test error when graph is missing nodes."""
        sample_graph.graph_data = {"edges": []}
        
        with pytest.raises(GraphTranslationError) as exc_info:
            translation_service.translate_graph(sample_graph)
        
        error = exc_info.value
        assert "missing 'nodes' field" in error.details["error"]
        
    def test_translate_graph_multiple_crews(self, translation_service, sample_graph):
        """Test error when graph has multiple crews."""
        sample_graph.graph_data = {
            "nodes": [
                {"id": "agent1", "type": "agent", "data": {"role": "test", "goal": "test", "backstory": "test"}},
                {"id": "task1", "type": "task", "data": {"description": "test", "expected_output": "test"}},
                {"id": "crew1", "type": "crew"},
                {"id": "crew2", "type": "crew"}
            ],
            "edges": []
        }
        
        with pytest.raises(GraphTranslationError) as exc_info:
            translation_service.translate_graph(sample_graph)
        
        error = exc_info.value
        assert error.chat_error_code == ChatErrorCode.MULTIPLE_CREWS_DETECTED
        assert error.details["crew_count"] == 2
        
    def test_translate_graph_missing_agent_fields(self, translation_service, sample_graph):
        """Test error when agent is missing required fields."""
        sample_graph.graph_data = {
            "nodes": [
                {"id": "agent1", "type": "agent", "data": {"role": "test"}},  # Missing goal and backstory
                {"id": "task1", "type": "task", "data": {"description": "test", "expected_output": "test"}},
                {"id": "crew1", "type": "crew"}
            ],
            "edges": []
        }
        
        with pytest.raises(GraphTranslationError) as exc_info:
            translation_service.translate_graph(sample_graph)
        
        error = exc_info.value
        assert error.chat_error_code == ChatErrorCode.AGENT_CONFIG_MISSING
        assert "goal" in error.details["missing_fields"]
        assert "backstory" in error.details["missing_fields"]


class TestChatStreamingErrorHandling:
    """Test error handling in chat streaming endpoint."""
    
    def test_execution_already_running_error_response(self):
        """Test that concurrent execution returns proper error format."""
        # This would be an integration test with the actual endpoint
        # Testing the error response format
        error = create_execution_already_running_error("graph-123")
        response = ErrorHandler.get_user_error_response(error)
        
        expected_keys = ["error", "message", "error_code", "severity", "recoverable", "retry_recommended"]
        assert all(key in response for key in expected_keys)
        assert response["error"] is True
        assert response["error_code"] == ChatErrorCode.EXECUTION_ALREADY_RUNNING
        assert "wait for it to complete" in response["message"]


if __name__ == "__main__":
    pytest.main([__file__]) 