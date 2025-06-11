"""
Tests for async execution service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime

from services.async_execution_service import AsyncExecutionService
from models.execution import Execution, ExecutionStatus
from models.graph import Graph


class TestAsyncExecutionService:
    """Test cases for AsyncExecutionService."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.service = AsyncExecutionService()
        self.graph_id = uuid4()
        self.thread_id = uuid4()
        self.user_id = uuid4()
        self.inputs = {"test": "input"}
    
    @patch('services.async_execution_service.execute_crew_async')
    def test_queue_execution_success(self, mock_task):
        """Test successful execution queueing."""
        # Setup
        mock_result = Mock()
        mock_result.id = "test-task-id"
        mock_task.apply_async.return_value = mock_result
        
        # Execute
        task_id = self.service.queue_execution(
            self.graph_id, self.thread_id, self.user_id, self.inputs
        )
        
        # Verify
        assert task_id == "test-task-id"
        mock_task.apply_async.assert_called_once()
    
    @patch('services.async_execution_service.celery_app')
    def test_get_task_status_success(self, mock_celery):
        """Test successful task status retrieval."""
        # Setup
        mock_result = Mock()
        mock_result.status = "SUCCESS"
        mock_result.result = {"test": "result"}
        mock_result.ready.return_value = True
        mock_result.failed.return_value = False
        mock_result.date_done = datetime.utcnow()
        mock_celery.AsyncResult.return_value = mock_result
        
        # Execute
        status = self.service.get_task_status("test-task-id")
        
        # Verify
        assert status["status"] == "SUCCESS"
        assert status["result"] == {"test": "result"}
        assert status["task_id"] == "test-task-id"
    
    @patch('services.async_execution_service.celery_app')
    def test_cancel_task_success(self, mock_celery):
        """Test successful task cancellation."""
        # Execute
        result = self.service.cancel_task("test-task-id")
        
        # Verify
        assert result is True
        mock_celery.control.revoke.assert_called_once_with("test-task-id", terminate=True)


class TestExecuteCrewAsync:
    """Test cases for execute_crew_async task."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        with patch('services.async_execution_service.SessionLocal') as mock_session:
            mock_db = Mock()
            mock_session.return_value = mock_db
            yield mock_db
    
    @pytest.fixture
    def mock_graph(self):
        """Mock graph object."""
        graph = Mock(spec=Graph)
        graph.id = uuid4()
        graph.graph_data = {
            "nodes": [
                {"id": "agent1", "type": "agent", "data": {"role": "test", "goal": "test", "backstory": "test"}},
                {"id": "task1", "type": "task", "data": {"description": "test task"}}
            ],
            "edges": []
        }
        return graph
    
    @pytest.fixture
    def mock_execution(self):
        """Mock execution object."""
        execution = Mock(spec=Execution)
        execution.id = uuid4()
        return execution
    
    @patch('services.async_execution_service.GraphTranslationService')
    @patch('services.async_execution_service.SessionLocal')
    def test_execute_crew_async_success(self, mock_session_local, mock_translation_service, mock_graph, mock_execution):
        """Test successful crew execution."""
        # Setup mock database session
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        
        # Setup mock execution
        mock_execution.id = str(uuid4())
        mock_execution.start_execution = Mock()
        mock_execution.complete_execution = Mock()
        
        # Setup mock database queries
        mock_db.query.return_value.filter.return_value.first.return_value = mock_graph
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        
        # Setup mock crew execution
        mock_crew = Mock()
        mock_crew.kickoff.return_value = Mock()
        mock_crew.kickoff.return_value.raw = "execution result"
        mock_translation_service.return_value.translate_graph.return_value = mock_crew
        
        # Mock the Execution constructor to return our mock
        with patch('services.async_execution_service.Execution', return_value=mock_execution):
            # Create mock task context
            mock_self = Mock()
            mock_self.request = Mock()
            mock_self.request.id = "test-task-id"
            mock_self.update_state = Mock()
            
            # Import the testable logic function
            from services.async_execution_service import _execute_crew_logic
            
            # Execute using the core logic function (bypasses Celery)
            result = _execute_crew_logic(
                mock_self,
                str(uuid4()),
                str(uuid4()),
                str(uuid4()),
                {"test": "input"}
            )
            
            # Verify
            assert result["status"] == "success"
            assert "execution_id" in result
            assert result["result"] == "execution result"
            
            # Verify mock calls
            mock_execution.start_execution.assert_called_once()
            mock_execution.complete_execution.assert_called_once()
            mock_translation_service.assert_called_once()
            mock_crew.kickoff.assert_called_once()


class TestAsyncExecutionIntegration:
    """Integration tests for async execution service."""
    
    @pytest.mark.integration
    def test_full_execution_flow(self):
        """Test complete execution flow (requires Redis)."""
        # This test would require actual Redis and Celery setup
        # Skip in unit tests
        pytest.skip("Integration test requires Redis setup")
    
    @pytest.mark.integration 
    def test_error_handling_flow(self):
        """Test error handling in execution flow."""
        # This test would verify error scenarios
        # Skip in unit tests
        pytest.skip("Integration test requires Redis setup")


if __name__ == "__main__":
    pytest.main([__file__]) 