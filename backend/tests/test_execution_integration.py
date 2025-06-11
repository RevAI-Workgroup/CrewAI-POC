"""
Integration tests for execution service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
import json
from datetime import datetime

from .fixtures.execution_fixtures import *
from .utils.execution_test_utils import (
    ExecutionTestHelper, 
    mock_execution_environment,
    ExecutionTestAssertions
)

from services.async_execution_service import AsyncExecutionService, _execute_crew_logic
from models.execution import Execution, ExecutionStatus
from models.graph import Graph


class TestExecutionIntegration:
    """Integration tests for execution workflows."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.service = AsyncExecutionService()
        self.test_helper = ExecutionTestHelper()
        self.assertions = ExecutionTestAssertions()
    
    def test_full_execution_workflow_success(
        self, 
        sample_graph_id,
        sample_thread_id, 
        sample_user_id,
        sample_inputs,
        mock_graph,
        mock_execution
    ):
        """Test complete successful execution workflow."""
        with mock_execution_environment() as env:
            # Setup mocks
            env["session"].query.return_value.filter.return_value.first.return_value = mock_graph
            
            # Mock Execution constructor
            with patch('services.async_execution_service.Execution', return_value=mock_execution):
                # Create mock task context
                mock_self = Mock()
                mock_self.request = Mock()
                mock_self.request.id = "test-task-id"
                mock_self.request.retries = 0
                mock_self.update_state = Mock()
                
                # Execute the crew logic
                result = _execute_crew_logic(
                    mock_self,
                    str(sample_graph_id),
                    str(sample_thread_id),
                    str(sample_user_id),
                    sample_inputs
                )
                
                # Assert results
                self.assertions.assert_execution_success(result)
                
                # Verify execution lifecycle
                mock_execution.start_execution.assert_called_once()
                mock_execution.complete_execution.assert_called_once()
                
                # Verify graph translation
                env["translation_service"].assert_called_once()
                env["crew"].kickoff.assert_called_once_with(inputs=sample_inputs)
                
                # Verify progress updates
                assert mock_self.update_state.call_count >= 2
    
    def test_execution_with_graph_not_found(
        self,
        sample_graph_id,
        sample_thread_id,
        sample_user_id,
        sample_inputs
    ):
        """Test execution when graph is not found."""
        with mock_execution_environment() as env:
            # Setup graph not found
            env["session"].query.return_value.filter.return_value.first.return_value = None
            
            # Mock the Execution model to avoid database operations
            with patch('services.async_execution_service.Execution') as mock_exec_class:
                mock_execution = Mock()
                mock_execution.id = uuid4()
                mock_execution.start_execution = Mock()
                mock_exec_class.return_value = mock_execution
                
                # Create mock task context with proper attributes
                mock_self = Mock()
                mock_self.request = Mock()
                mock_self.request.id = "test-task-id"
                mock_self.request.retries = 0
                mock_self.update_state = Mock()
                mock_self.retry = Mock()
                mock_self.max_retries = 3
                
                # Execute the crew logic
                result = _execute_crew_logic(
                    mock_self,
                    str(sample_graph_id),
                    str(sample_thread_id),
                    str(sample_user_id),
                    sample_inputs
                )
                
                # Assert failure
                self.assertions.assert_execution_failure(result, "Graph")
                assert "not found" in result["error"]
    
    def test_execution_with_crewai_error(
        self,
        sample_graph_id,
        sample_thread_id,
        sample_user_id,
        sample_inputs,
        mock_graph,
        mock_execution
    ):
        """Test execution when CrewAI throws an error."""
        with mock_execution_environment() as env:
            # Setup mocks
            env["session"].query.return_value.filter.return_value.first.return_value = mock_graph
            
            # Make crew execution fail
            env["crew"].kickoff.side_effect = Exception("CrewAI execution failed")
            
            # Mock Execution constructor
            with patch('services.async_execution_service.Execution', return_value=mock_execution):
                # Create mock task context
                mock_self = Mock()
                mock_self.request = Mock()
                mock_self.request.id = "test-task-id"
                mock_self.request.retries = 0
                mock_self.update_state = Mock()
                mock_self.retry = Mock()
                mock_self.max_retries = 3
                
                # Execute the crew logic
                result = _execute_crew_logic(
                    mock_self,
                    str(sample_graph_id),
                    str(sample_thread_id),
                    str(sample_user_id),
                    sample_inputs
                )
                
                # Assert failure
                self.assertions.assert_execution_failure(result, "CrewAI execution failed")
    
    def test_execution_status_tracking(
        self,
        execution_test_data,
        mock_celery_task
    ):
        """Test execution status tracking through service."""
        with patch('services.async_execution_service.celery_app') as mock_celery:
            # Setup mock task
            mock_celery.AsyncResult.return_value = mock_celery_task
            
            # Get task status
            status = self.service.get_task_status("test-task-id")
            
            # Verify status structure
            assert status["task_id"] == "test-task-id"
            assert status["status"] == "SUCCESS"
            assert "result" in status
            assert "date_done" in status
    
    def test_execution_cancellation(self):
        """Test execution cancellation."""
        with patch('services.async_execution_service.celery_app') as mock_celery:
            # Test cancellation
            result = self.service.cancel_task("test-task-id")
            
            # Verify cancellation
            assert result is True
            mock_celery.control.revoke.assert_called_once_with("test-task-id", terminate=True)
    
    def test_execution_queue_management(
        self,
        sample_graph_id,
        sample_thread_id,
        sample_user_id,
        sample_inputs
    ):
        """Test execution queueing with different priorities."""
        with patch('services.async_execution_service.execute_crew_async') as mock_task:
            # Setup mock task
            mock_result = Mock()
            mock_result.id = "test-task-id"
            mock_task.apply_async.return_value = mock_result
            
            # Queue high priority execution
            task_id = self.service.queue_execution(
                sample_graph_id,
                sample_thread_id,
                sample_user_id,
                sample_inputs,
                priority=1
            )
            
            # Verify queueing
            assert task_id == "test-task-id"
            mock_task.apply_async.assert_called_once()
            
            # Verify priority was passed
            call_kwargs = mock_task.apply_async.call_args[1]
            assert call_kwargs["priority"] == 1
            assert call_kwargs["queue"] == "crew_execution"
    
    def test_execution_with_complex_graph(
        self,
        sample_thread_id,
        sample_user_id,
        sample_inputs
    ):
        """Test execution with complex multi-agent graph."""
        # Create complex graph data
        complex_graph_data = {
            "nodes": [
                {
                    "id": "researcher",
                    "type": "agent",
                    "data": {
                        "role": "Research Agent",
                        "goal": "Research topics thoroughly",
                        "backstory": "Expert researcher with access to various tools",
                        "tools": ["search_tool", "scraping_tool"]
                    }
                },
                {
                    "id": "writer",
                    "type": "agent",
                    "data": {
                        "role": "Content Writer",
                        "goal": "Write engaging content",
                        "backstory": "Skilled writer who creates compelling content",
                        "tools": []
                    }
                },
                {
                    "id": "research_task",
                    "type": "task",
                    "data": {
                        "description": "Research the given topic comprehensively",
                        "expected_output": "Detailed research report",
                        "agent": "researcher"
                    }
                },
                {
                    "id": "writing_task",
                    "type": "task",
                    "data": {
                        "description": "Write article based on research",
                        "expected_output": "Well-written article",
                        "agent": "writer"
                    }
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "source": "researcher",
                    "target": "research_task",
                    "type": "assignment"
                },
                {
                    "id": "edge2",
                    "source": "writer",
                    "target": "writing_task",
                    "type": "assignment"
                },
                {
                    "id": "edge3",
                    "source": "research_task",
                    "target": "writing_task",
                    "type": "dependency"
                }
            ]
        }
        
        # Create mock complex graph
        complex_graph = Mock(spec=Graph)
        complex_graph.id = uuid4()
        complex_graph.graph_data = complex_graph_data
        
        with mock_execution_environment() as env:
            # Setup mocks
            env["session"].query.return_value.filter.return_value.first.return_value = complex_graph
            
            # Mock execution
            mock_execution = Mock(spec=Execution)
            mock_execution.id = uuid4()
            mock_execution.start_execution = Mock()
            mock_execution.complete_execution = Mock()
            
            # Mock Execution constructor
            with patch('services.async_execution_service.Execution', return_value=mock_execution):
                # Create mock task context
                mock_self = Mock()
                mock_self.request = Mock()
                mock_self.request.id = "complex-task-id"
                mock_self.update_state = Mock()
                
                # Execute the crew logic
                result = _execute_crew_logic(
                    mock_self,
                    str(complex_graph.id),
                    str(sample_thread_id),
                    str(sample_user_id),
                    sample_inputs
                )
                
                # Assert success
                self.assertions.assert_execution_success(result)
                
                # Verify translation service was called with complex graph
                env["translation_service"].assert_called_once()
                translation_call = env["translation_service"].call_args[0]
                assert len(translation_call) > 0
    
    def test_execution_error_recovery(
        self,
        sample_graph_id,
        sample_thread_id,
        sample_user_id,
        sample_inputs,
        mock_graph,
        mock_execution
    ):
        """Test execution error recovery and retry logic."""
        with mock_execution_environment() as env:
            # Setup mocks
            env["session"].query.return_value.filter.return_value.first.return_value = mock_graph
            
            # Mock Execution constructor
            with patch('services.async_execution_service.Execution', return_value=mock_execution):
                # Create mock task context with retry capability
                mock_self = Mock()
                mock_self.request = Mock()
                mock_self.request.id = "retry-task-id"
                mock_self.request.retries = 1  # Second attempt
                mock_self.update_state = Mock()
                mock_self.retry = Mock()
                mock_self.max_retries = 3
                
                # Make crew execution fail first, then succeed
                env["crew"].kickoff.side_effect = [
                    Exception("Temporary failure"),
                    Mock(raw="Success after retry")
                ]
                
                # Execute the crew logic (should handle retry internally)
                result = _execute_crew_logic(
                    mock_self,
                    str(sample_graph_id),
                    str(sample_thread_id),
                    str(sample_user_id),
                    sample_inputs
                )
                
                # Should fail on first attempt but the logic itself doesn't retry
                # (retry is handled by Celery)
                self.assertions.assert_execution_failure(result, "Temporary failure")


class TestExecutionServiceIntegration:
    """Integration tests for AsyncExecutionService methods."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.service = AsyncExecutionService()
    
    def test_service_without_celery(self):
        """Test service behavior when Celery is not available."""
        with patch('services.async_execution_service.CELERY_AVAILABLE', False):
            # Queue execution should raise error
            with pytest.raises(RuntimeError, match="Celery is not available"):
                self.service.queue_execution(
                    uuid4(), uuid4(), uuid4(), {"test": "input"}
                )
            
            # Get status should return unavailable
            status = self.service.get_task_status("test-task-id")
            assert status["status"] == "UNAVAILABLE"
            assert "Celery not available" in status["error"]
    
    def test_service_with_celery_error(self):
        """Test service behavior when Celery operations fail."""
        with patch('services.async_execution_service.celery_app') as mock_celery:
            # Make apply_async fail
            mock_celery.AsyncResult.side_effect = Exception("Celery connection failed")
            
            # Get status should return error
            status = self.service.get_task_status("test-task-id")
            assert status["status"] == "UNKNOWN"
            assert "Celery connection failed" in status["error"] 