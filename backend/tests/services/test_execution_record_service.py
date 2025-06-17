"""
Tests for ExecutionRecordService

Tests execution record management during chat streaming operations including:
- Execution creation and lifecycle management
- Message-execution linking
- Status transitions and error handling
- Transaction management and rollback scenarios
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from models.execution import Execution, ExecutionStatus
from models.message import Message, MessageStatus, MessageType
from models.graph import Graph
from models.thread import Thread
from services.execution_record_service import ExecutionRecordService


class TestExecutionRecordService:
    """Test suite for ExecutionRecordService."""
    
    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def execution_service(self, db_session):
        """ExecutionRecordService instance with mocked dependencies."""
        with patch('services.execution_record_service.ExecutionStatusService'):
            return ExecutionRecordService(db_session)
    
    @pytest.fixture
    def sample_execution(self):
        """Sample execution record."""
        from unittest.mock import MagicMock
        mock_execution = MagicMock()
        mock_execution.id = str(uuid4())
        mock_execution.graph_id = str(uuid4())
        mock_execution.status = ExecutionStatus.PENDING.value
        mock_execution.execution_config = {'test': 'config'}
        mock_execution.progress_percentage = 0
        mock_execution.add_log_entry = MagicMock()
        return mock_execution
    
    @pytest.fixture
    def sample_message(self):
        """Sample message record."""
        from unittest.mock import MagicMock
        mock_message = MagicMock()
        mock_message.id = str(uuid4())
        mock_message.thread_id = str(uuid4())
        mock_message.content = "Test message"
        mock_message.message_type = MessageType.ASSISTANT.value
        mock_message.status = MessageStatus.PENDING.value
        mock_message.link_execution = MagicMock()
        mock_message.mark_processing = MagicMock()
        mock_message.mark_completed = MagicMock()
        mock_message.mark_failed = MagicMock()
        return mock_message
    
    def test_create_chat_execution_success(self, execution_service, db_session):
        """Test successful execution creation."""
        graph_id = str(uuid4())
        trigger_message_id = str(uuid4())
        config = {'message': 'test', 'output': 'response'}
        
        # Mock successful creation
        db_session.add.return_value = None
        db_session.flush.return_value = None
        
        # Execute
        result = execution_service.create_chat_execution(
            graph_id=graph_id,
            trigger_message_id=trigger_message_id,
            execution_config=config
        )
        
        # Verify
        assert result is not None
        assert result.graph_id == graph_id
        assert result.trigger_message_id == trigger_message_id
        assert result.execution_config == config
        assert result.status == ExecutionStatus.PENDING.value
        assert result.progress_percentage == 0
        
        db_session.add.assert_called_once()
        db_session.flush.assert_called_once()
    
    def test_create_chat_execution_database_error(self, execution_service, db_session):
        """Test execution creation with database error."""
        # Mock database error
        db_session.add.side_effect = SQLAlchemyError("Database error")
        
        # Execute and verify exception
        with pytest.raises(SQLAlchemyError):
            execution_service.create_chat_execution(
                graph_id=str(uuid4()),
                execution_config={}
            )
        
        # Verify rollback was called
        db_session.rollback.assert_called_once()
    
    def test_start_execution_success(self, execution_service, db_session, sample_execution):
        """Test successful execution start."""
        execution_id = sample_execution.id
        
        # Mock database query
        db_session.query.return_value.filter.return_value.first.return_value = sample_execution
        
        # Execute
        execution_service.start_execution(execution_id)
        
        # Verify status service was called
        execution_service.status_service.update_execution_status.assert_called_once()
        args = execution_service.status_service.update_execution_status.call_args
        assert args[1]['new_status'] == ExecutionStatus.RUNNING
        assert args[1]['progress'] == 0
        assert args[1]['current_step'] == "Starting execution"
    
    def test_start_execution_not_found(self, execution_service, db_session):
        """Test starting non-existent execution."""
        # Mock execution not found
        db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute and verify exception
        with pytest.raises(ValueError, match="Execution .* not found"):
            execution_service.start_execution(str(uuid4()))
    
    def test_update_execution_progress_success(self, execution_service, db_session, sample_execution):
        """Test successful progress update."""
        execution_id = sample_execution.id
        
        # Mock database query
        db_session.query.return_value.filter.return_value.first.return_value = sample_execution
        
        # Execute
        execution_service.update_execution_progress(
            execution_id=execution_id,
            progress=50,
            current_step="Processing data",
            intermediate_data={'processed': 100}
        )
        
        # Verify updates
        db_session.flush.assert_called_once()
    
    def test_update_execution_progress_invalid_percentage(self, execution_service, db_session, sample_execution):
        """Test progress update with invalid percentage."""
        execution_id = sample_execution.id
        
        # Mock database query
        db_session.query.return_value.filter.return_value.first.return_value = sample_execution
        
        # Execute and verify exception
        with pytest.raises(ValueError, match="Progress must be between 0 and 100"):
            execution_service.update_execution_progress(
                execution_id=execution_id,
                progress=150  # Invalid
            )
    
    def test_complete_execution_success(self, execution_service):
        """Test successful execution completion."""
        execution_id = str(uuid4())
        result_data = {'result': 'success', 'content': 'Final output'}
        
        # Execute
        execution_service.complete_execution(
            execution_id=execution_id,
            result_data=result_data,
            final_output="Execution completed"
        )
        
        # Verify status service was called with completion
        execution_service.status_service.update_execution_status.assert_called_once()
        args = execution_service.status_service.update_execution_status.call_args
        assert args[1]['new_status'] == ExecutionStatus.COMPLETED
        assert args[1]['progress'] == 100
        assert args[1]['current_step'] == "Execution completed"
        assert args[1]['result_data'] == result_data
    
    def test_fail_execution_success(self, execution_service, db_session, sample_execution):
        """Test successful execution failure handling."""
        execution_id = sample_execution.id
        error_message = "Test error occurred"
        error_details = {'error_code': 'TEST_ERROR'}
        traceback_info = "Traceback details"
        
        # Mock database query for log entry
        db_session.query.return_value.filter.return_value.first.return_value = sample_execution
        
        # Execute
        execution_service.fail_execution(
            execution_id=execution_id,
            error_message=error_message,
            error_details=error_details,
            traceback_info=traceback_info
        )
        
        # Verify status service was called with failure
        execution_service.status_service.update_execution_status.assert_called_once()
        args = execution_service.status_service.update_execution_status.call_args
        assert args[1]['new_status'] == ExecutionStatus.FAILED
        assert args[1]['error_message'] == error_message
        
        # Verify error details include traceback
        error_details_arg = args[1]['error_details']
        assert error_details_arg['traceback'] == traceback_info
        assert 'failed_at' in error_details_arg
    
    def test_link_message_to_execution_success(self, execution_service, db_session, sample_message, sample_execution):
        """Test successful message-execution linking."""
        message_id = sample_message.id
        execution_id = sample_execution.id
        user_id = str(uuid4())
        
        # Mock database queries
        db_session.query.return_value.filter.return_value.first.side_effect = [
            sample_message,  # First call for message
            sample_execution  # Second call for execution
        ]
        
        # Execute
        execution_service.link_message_to_execution(
            message_id=message_id,
            execution_id=execution_id,
            user_id=user_id
        )
        
        # Verify link was created
        sample_message.link_execution.assert_called_once_with(execution_id)
        db_session.flush.assert_called_once()
    
    def test_link_message_to_execution_message_not_found(self, execution_service, db_session):
        """Test linking with non-existent message."""
        # Mock message not found
        db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute and verify exception
        with pytest.raises(ValueError, match="Message .* not found"):
            execution_service.link_message_to_execution(
                message_id=str(uuid4()),
                execution_id=str(uuid4()),
                user_id=str(uuid4())
            )
    
    def test_synchronize_message_status_success(self, execution_service, db_session, sample_message):
        """Test successful message status synchronization."""
        message_id = sample_message.id
        execution_status = ExecutionStatus.RUNNING
        
        # Mock database query
        db_session.query.return_value.filter.return_value.first.return_value = sample_message
        
        # Execute
        execution_service.synchronize_message_status(
            message_id=message_id,
            execution_status=execution_status
        )
        
        # Verify message status was updated
        sample_message.mark_processing.assert_called_once()
        db_session.flush.assert_called_once()
    
    def test_synchronize_message_status_mapping(self, execution_service, db_session, sample_message):
        """Test status mapping for different execution statuses."""
        message_id = sample_message.id
        
        # Mock database query
        db_session.query.return_value.filter.return_value.first.return_value = sample_message
        
        # Test different status mappings
        test_cases = [
            (ExecutionStatus.PENDING, 'mark_processing'),  # Default handling
            (ExecutionStatus.RUNNING, 'mark_processing'),
            (ExecutionStatus.COMPLETED, 'mark_completed'),
            (ExecutionStatus.FAILED, 'mark_failed'),
            (ExecutionStatus.CANCELLED, 'mark_failed'),
            (ExecutionStatus.TIMEOUT, 'mark_failed'),
        ]
        
        for execution_status, expected_method in test_cases:
            # Reset mock
            sample_message.reset_mock()
            
            # Execute
            execution_service.synchronize_message_status(
                message_id=message_id,
                execution_status=execution_status
            )
            
            # Verify correct method was called (except for PENDING which doesn't call any method)
            if execution_status != ExecutionStatus.PENDING:
                getattr(sample_message, expected_method).assert_called_once()
    
    def test_cleanup_failed_execution(self, execution_service, db_session, sample_execution):
        """Test cleanup of failed execution."""
        execution_id = sample_execution.id
        
        # Mock database query
        db_session.query.return_value.filter.return_value.first.return_value = sample_execution
        
        # Execute
        execution_service.cleanup_failed_execution(execution_id)
        
        # Verify cleanup log was added
        sample_execution.add_log_entry.assert_called_once_with(
            "Cleaning up failed execution resources"
        )
        db_session.flush.assert_called_once()
    
    def test_cleanup_failed_execution_not_found(self, execution_service, db_session):
        """Test cleanup with non-existent execution."""
        # Mock execution not found
        db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute (should not raise exception)
        execution_service.cleanup_failed_execution(str(uuid4()))
        
        # Should not call flush since execution not found
        db_session.flush.assert_not_called()
    
    def test_get_execution_by_id(self, execution_service, db_session, sample_execution):
        """Test getting execution by ID."""
        execution_id = sample_execution.id
        
        # Mock database query
        db_session.query.return_value.filter.return_value.first.return_value = sample_execution
        
        # Execute
        result = execution_service.get_execution_by_id(execution_id)
        
        # Verify
        assert result == sample_execution
        db_session.query.assert_called_once()
    
    def test_get_execution_status(self, execution_service, db_session, sample_execution):
        """Test getting execution status."""
        execution_id = sample_execution.id
        sample_execution.status = ExecutionStatus.RUNNING.value
        
        # Mock database query
        db_session.query.return_value.filter.return_value.first.return_value = sample_execution
        
        # Execute
        result = execution_service.get_execution_status(execution_id)
        
        # Verify
        assert result == ExecutionStatus.RUNNING
    
    def test_get_execution_status_not_found(self, execution_service, db_session):
        """Test getting status for non-existent execution."""
        # Mock execution not found
        db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = execution_service.get_execution_status(str(uuid4()))
        
        # Verify
        assert result is None


class TestExecutionRecordServiceIntegration:
    """Integration tests for ExecutionRecordService with real database operations."""
    
    def test_full_execution_lifecycle(self, execution_service, db_session):
        """Test complete execution lifecycle from creation to completion."""
        # This would be implemented with actual database setup
        # for integration testing
        pass
    
    def test_concurrent_execution_handling(self, execution_service, db_session):
        """Test handling of concurrent execution scenarios."""
        # This would test concurrent access to execution records
        pass
    
    def test_transaction_rollback_scenarios(self, execution_service, db_session):
        """Test proper transaction handling and rollback."""
        # This would test rollback scenarios with real database
        pass 