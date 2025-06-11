"""
Tests for execution status management service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timedelta

from services.execution_status_service import ExecutionStatusService, StatusTransitionError
from models.execution import Execution, ExecutionStatus, ExecutionPriority


class TestExecutionStatusService:
    """Test cases for ExecutionStatusService."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_db = Mock()
        self.service = ExecutionStatusService(self.mock_db)
        self.execution_id = uuid4()
    
    def test_validate_transition_valid(self):
        """Test valid status transitions."""
        # Valid transitions
        assert self.service.validate_transition(ExecutionStatus.PENDING, ExecutionStatus.RUNNING)
        assert self.service.validate_transition(ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED)
        assert self.service.validate_transition(ExecutionStatus.RUNNING, ExecutionStatus.FAILED)
        assert self.service.validate_transition(ExecutionStatus.FAILED, ExecutionStatus.PENDING)
    
    def test_validate_transition_invalid(self):
        """Test invalid status transitions."""
        # Invalid transitions
        assert not self.service.validate_transition(ExecutionStatus.COMPLETED, ExecutionStatus.RUNNING)
        assert not self.service.validate_transition(ExecutionStatus.CANCELLED, ExecutionStatus.RUNNING)
        assert not self.service.validate_transition(ExecutionStatus.PENDING, ExecutionStatus.COMPLETED)
    
    def test_update_execution_status_success(self):
        """Test successful status update."""
        # Setup mock execution
        mock_execution = Mock(spec=Execution)
        mock_execution.status = ExecutionStatus.PENDING.value
        mock_execution.set_status = Mock()
        mock_execution.update_progress = Mock()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_execution
        
        # Execute
        result = self.service.update_execution_status(
            self.execution_id,
            ExecutionStatus.RUNNING,
            progress=25,
            current_step="Starting execution"
        )
        
        # Verify
        assert result == mock_execution
        mock_execution.set_status.assert_called_once_with(ExecutionStatus.RUNNING)
        mock_execution.update_progress.assert_called_once_with(25, "Starting execution")
        self.mock_db.commit.assert_called_once()
    
    def test_update_execution_status_invalid_transition(self):
        """Test status update with invalid transition."""
        # Setup mock execution
        mock_execution = Mock(spec=Execution)
        mock_execution.status = ExecutionStatus.COMPLETED.value
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_execution
        
        # Execute and verify exception
        with pytest.raises(StatusTransitionError) as exc_info:
            self.service.update_execution_status(
                self.execution_id,
                ExecutionStatus.RUNNING
            )
        
        assert "Invalid status transition" in str(exc_info.value)
        self.mock_db.rollback.assert_called_once()
    
    def test_update_execution_status_not_found(self):
        """Test status update with non-existent execution."""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError) as exc_info:
            self.service.update_execution_status(self.execution_id, ExecutionStatus.RUNNING)
        
        assert "not found" in str(exc_info.value)
    
    def test_update_execution_status_completion(self):
        """Test status update to completed with result data."""
        # Setup mock execution
        mock_execution = Mock(spec=Execution)
        mock_execution.status = ExecutionStatus.RUNNING.value
        mock_execution.set_status = Mock()
        mock_execution.complete_execution = Mock()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_execution
        
        result_data = {"output": "test result"}
        
        # Execute
        self.service.update_execution_status(
            self.execution_id,
            ExecutionStatus.COMPLETED,
            result_data=result_data
        )
        
        # Verify
        mock_execution.complete_execution.assert_called_once_with(result_data)
    
    def test_update_execution_status_failure(self):
        """Test status update to failed with error details."""
        # Setup mock execution
        mock_execution = Mock(spec=Execution)
        mock_execution.status = ExecutionStatus.RUNNING.value
        mock_execution.set_status = Mock()
        mock_execution.fail_execution = Mock()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_execution
        
        error_details = {"traceback": "test traceback"}
        
        # Execute
        self.service.update_execution_status(
            self.execution_id,
            ExecutionStatus.FAILED,
            error_message="Test error",
            error_details=error_details
        )
        
        # Verify
        mock_execution.fail_execution.assert_called_once_with("Test error", error_details)
    
    def test_get_execution_status(self):
        """Test getting execution status."""
        # Setup mock execution
        mock_execution = Mock(spec=Execution)
        mock_execution.id = str(self.execution_id)
        mock_execution.status = ExecutionStatus.RUNNING.value
        mock_execution.progress_percentage = 50
        mock_execution.current_step = "Processing"
        mock_execution.started_at = datetime.utcnow()
        mock_execution.completed_at = None
        mock_execution.duration_seconds = None
        mock_execution.error_message = None
        mock_execution.is_cancelled = False
        mock_execution.priority = ExecutionPriority.NORMAL.value
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_execution
        
        # Execute
        status = self.service.get_execution_status(self.execution_id)
        
        # Verify
        assert status["id"] == str(self.execution_id)
        assert status["status"] == ExecutionStatus.RUNNING.value
        assert status["progress_percentage"] == 50
        assert status["current_step"] == "Processing"
        assert status["started_at"] is not None
        assert status["completed_at"] is None
    
    def test_bulk_update_status(self):
        """Test bulk status update."""
        execution_ids = [uuid4(), uuid4(), uuid4()]
        
        # Mock successful updates
        with patch.object(self.service, 'update_execution_status') as mock_update:
            mock_update.return_value = Mock()
            
            # Execute
            result = self.service.bulk_update_status(
                execution_ids,
                ExecutionStatus.CANCELLED,
                reason="Test cancellation"
            )
            
            # Verify
            assert len(result["updated"]) == 3
            assert len(result["failed"]) == 0
            assert len(result["skipped"]) == 0
            assert mock_update.call_count == 3
    
    def test_bulk_update_status_with_failures(self):
        """Test bulk status update with some failures."""
        execution_ids = [uuid4(), uuid4(), uuid4()]
        
        # Mock mixed results
        def side_effect(exec_id, status, **kwargs):
            if exec_id == execution_ids[1]:
                raise StatusTransitionError("Invalid transition")
            elif exec_id == execution_ids[2]:
                raise ValueError("Execution not found")
            return Mock()
        
        with patch.object(self.service, 'update_execution_status', side_effect=side_effect):
            # Execute
            result = self.service.bulk_update_status(
                execution_ids,
                ExecutionStatus.CANCELLED
            )
            
            # Verify
            assert len(result["updated"]) == 1
            assert len(result["failed"]) == 1
            assert len(result["skipped"]) == 1
    
    def test_get_executions_by_status(self):
        """Test getting executions by status."""
        mock_executions = [Mock(), Mock()]
        
        self.mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = mock_executions
        
        # Execute
        executions = self.service.get_executions_by_status(
            ExecutionStatus.RUNNING,
            limit=10
        )
        
        # Verify
        assert executions == mock_executions
        self.mock_db.query.return_value.filter.assert_called()
        self.mock_db.query.return_value.filter.return_value.limit.assert_called_with(10)
    
    def test_get_stuck_executions(self):
        """Test getting stuck executions."""
        mock_executions = [Mock(), Mock()]
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_executions
        
        # Execute
        stuck = self.service.get_stuck_executions(timeout_minutes=30)
        
        # Verify
        assert stuck == mock_executions
        self.mock_db.query.return_value.filter.assert_called()
    
    def test_timeout_stuck_executions(self):
        """Test timing out stuck executions."""
        mock_executions = [Mock(), Mock()]
        mock_executions[0].id = str(uuid4())
        mock_executions[1].id = str(uuid4())
        
        with patch.object(self.service, 'get_stuck_executions', return_value=mock_executions):
            with patch.object(self.service, 'update_execution_status') as mock_update:
                mock_update.return_value = Mock()
                
                # Execute
                timed_out = self.service.timeout_stuck_executions(60)
                
                # Verify
                assert len(timed_out) == 2
                assert mock_update.call_count == 2
    
    def test_register_status_callback(self):
        """Test registering status callbacks."""
        callback = Mock()
        
        # Register callback
        self.service.register_status_callback(ExecutionStatus.COMPLETED, callback)
        
        # Verify callback is registered
        assert ExecutionStatus.COMPLETED in self.service._status_callbacks
        assert callback in self.service._status_callbacks[ExecutionStatus.COMPLETED]
    
    def test_execute_callbacks(self):
        """Test execution of status callbacks."""
        callback1 = Mock()
        callback2 = Mock()
        mock_execution = Mock()
        
        # Register callbacks
        self.service.register_status_callback(ExecutionStatus.COMPLETED, callback1)
        self.service.register_status_callback(ExecutionStatus.COMPLETED, callback2)
        
        # Execute callbacks
        self.service._execute_callbacks(ExecutionStatus.COMPLETED, mock_execution)
        
        # Verify callbacks were called
        callback1.assert_called_once_with(mock_execution)
        callback2.assert_called_once_with(mock_execution)
    
    def test_callback_exception_handling(self):
        """Test callback exception handling."""
        failing_callback = Mock(side_effect=Exception("Callback failed"))
        mock_execution = Mock()
        
        # Register failing callback
        self.service.register_status_callback(ExecutionStatus.COMPLETED, failing_callback)
        
        # Execute callbacks (should not raise exception)
        self.service._execute_callbacks(ExecutionStatus.COMPLETED, mock_execution)
        
        # Verify callback was attempted
        failing_callback.assert_called_once_with(mock_execution)
    
    def test_get_execution_statistics(self):
        """Test getting execution statistics."""
        # Setup mock executions
        mock_executions = []
        for i in range(10):
            exec_mock = Mock()
            exec_mock.status = ExecutionStatus.COMPLETED.value if i < 7 else ExecutionStatus.FAILED.value
            exec_mock.duration_seconds = 100.0 if exec_mock.status == ExecutionStatus.COMPLETED.value else None
            mock_executions.append(exec_mock)
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_executions
        
        # Execute
        stats = self.service.get_execution_statistics()
        
        # Verify
        assert stats["total"] == 10
        assert stats["by_status"][ExecutionStatus.COMPLETED.value] == 7
        assert stats["by_status"][ExecutionStatus.FAILED.value] == 3
        assert stats["avg_duration"] == 100.0
        assert stats["success_rate"] == 0.7  # 7 successful out of 10 finished
    
    def test_cleanup_old_executions(self):
        """Test cleanup of old executions."""
        mock_executions = [Mock(), Mock(), Mock()]
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_executions
        
        # Execute
        count = self.service.cleanup_old_executions(days=30)
        
        # Verify
        assert count == 3
        self.mock_db.query.return_value.filter.assert_called()


class TestExecutionStatusIntegration:
    """Integration tests for execution status service."""
    
    @pytest.mark.integration
    def test_status_workflow(self):
        """Test complete status workflow."""
        # This would require actual database setup
        pytest.skip("Integration test requires database setup") 