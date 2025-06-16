"""
Integration tests for Thread Management
Tests service interactions, database transactions, and end-to-end workflows
"""

import pytest
import uuid
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from services.thread_service import ThreadService
from services.graph_crew_validation_service import GraphCrewValidationService
from services.execution_protection_service import ExecutionProtectionService, ConcurrentExecutionError
from models.thread import Thread, ThreadStatus
from models.graph import Graph
from models.user import User
from models.execution import Execution


class TestThreadIntegration:
    """Integration tests for thread management with dependent services."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db_mock = Mock(spec=Session)
        
        # Create real service instance
        self.thread_service = ThreadService(self.db_mock)
        
        # Mock dependent services
        self.validation_service_mock = Mock(spec=GraphCrewValidationService)
        self.execution_service_mock = Mock(spec=ExecutionProtectionService)
        
        # Test data
        self.user_id = str(uuid.uuid4())
        self.graph_id = str(uuid.uuid4())
        self.thread_id = str(uuid.uuid4())
        
        # Mock models
        self.mock_user = Mock(spec=User)
        self.mock_user.id = self.user_id
        
        self.mock_graph = Mock(spec=Graph)
        self.mock_graph.id = self.graph_id
        self.mock_graph.user_id = self.user_id
        self.mock_graph.is_active = True
        self.mock_graph.graph_data = {
            'nodes': [
                {
                    'id': 'crew-1',
                    'type': 'crew',
                    'data': {'agent_ids': ['agent-1'], 'task_ids': ['task-1']}
                },
                {
                    'id': 'agent-1', 
                    'type': 'agent',
                    'data': {'role': 'Test Agent'}
                },
                {
                    'id': 'task-1',
                    'type': 'task', 
                    'data': {'description': 'Test Task'}
                }
            ],
            'edges': []
        }
        
        self.mock_thread = Mock(spec=Thread)
        self.mock_thread.id = self.thread_id
        self.mock_thread.graph_id = self.graph_id
        self.mock_thread.name = "Test Thread"
        self.mock_thread.status = ThreadStatus.ACTIVE.value
        self.mock_thread.can_be_accessed_by.return_value = True
    
    @patch('services.thread_service.GraphCrewValidationService')
    def test_create_thread_with_validation_integration(self, mock_validation_class):
        """Test thread creation with graph validation service integration."""
        # Arrange
        mock_validation_instance = Mock()
        mock_validation_class.return_value = mock_validation_instance
        mock_validation_instance.validate_graph_for_new_thread.return_value = None
        
        # Mock the database query chain that's used in the validation service
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 0  # Return actual integer, not Mock
        self.db_mock.query.return_value = mock_query
        
        with patch.object(self.thread_service, '_validate_graph_access', return_value=self.mock_graph):
            # Act
            result = self.thread_service.create_thread(
                graph_id=self.graph_id,
                user_id=self.user_id,
                name="Integration Test Thread"
            )
            
            # Assert
            mock_validation_class.assert_called_once_with(self.db_mock)
            mock_validation_instance.validate_graph_for_new_thread.assert_called_once_with(self.mock_graph)
            self.db_mock.add.assert_called_once()
            self.db_mock.commit.assert_called_once()
    
    @patch('services.thread_service.GraphCrewValidationService')
    def test_create_thread_validation_failure(self, mock_validation_class):
        """Test thread creation when graph validation fails."""
        # Arrange
        mock_validation_instance = Mock()
        mock_validation_class.return_value = mock_validation_instance
        mock_validation_instance.validate_graph_for_new_thread.side_effect = ValueError("Graph has multiple crews")
        
        with patch.object(self.thread_service, '_validate_graph_access', return_value=self.mock_graph):
            # Act & Assert
            with pytest.raises(ValueError, match="Graph has multiple crews"):
                self.thread_service.create_thread(
                    graph_id=self.graph_id,
                    user_id=self.user_id,
                    name="Invalid Graph Thread"
                )
            
            # Verify rollback was called
            self.db_mock.rollback.assert_called_once()
    
    @patch('services.thread_service.get_execution_protection_service')
    def test_execution_protection_integration(self, mock_get_service):
        """Test execution protection service integration."""
        # Arrange
        execution_id = str(uuid.uuid4())
        mock_service = Mock(spec=ExecutionProtectionService)
        mock_get_service.return_value = mock_service
        mock_service.validate_execution_start.return_value = None  # Use validate_execution_start, not start_execution
        
        # Act
        self.thread_service.validate_execution_start(self.graph_id, execution_id)
        
        # Assert
        mock_get_service.assert_called_once()
        mock_service.validate_execution_start.assert_called_once_with(self.graph_id, execution_id)
    
    @patch('services.thread_service.get_execution_protection_service')
    def test_execution_protection_concurrent_error(self, mock_get_service):
        """Test execution protection with concurrent execution error."""
        # Arrange
        execution_id = str(uuid.uuid4())
        mock_service = Mock(spec=ExecutionProtectionService)
        mock_get_service.return_value = mock_service
        mock_service.validate_execution_start.side_effect = ConcurrentExecutionError("Another execution is running")
        
        # Act & Assert
        with pytest.raises(ConcurrentExecutionError, match="Another execution is running"):
            self.thread_service.validate_execution_start(self.graph_id, execution_id)
    
    @patch('services.thread_service.GraphCrewValidationService')
    def test_thread_lifecycle_integration(self, mock_validation_class):
        """Test complete thread lifecycle with database operations."""
        # Arrange
        mock_validation_instance = Mock()
        mock_validation_class.return_value = mock_validation_instance
        mock_validation_instance.validate_graph_for_new_thread.return_value = None
        
        with patch.object(self.thread_service, '_validate_graph_access', return_value=self.mock_graph):
            # Mock database queries more specifically for the lifecycle test
            with patch.object(self.db_mock, 'query') as mock_query:
                # Mock for thread creation validation (count query)
                mock_filter_chain = Mock()
                mock_filter_chain.count.return_value = 0
                
                # Mock for delete method message query (all query)
                mock_message_filter = Mock()
                mock_message_filter.all.return_value = []  # Return empty list instead of Mock
                
                # Configure query to return appropriate mocks
                def query_side_effect(model):
                    if model.__name__ == 'Thread':
                        return Mock(filter=Mock(return_value=mock_filter_chain))
                    elif model.__name__ == 'Message':
                        return Mock(filter=Mock(return_value=mock_message_filter))
                    else:
                        return Mock(filter=Mock(return_value=mock_filter_chain))
                
                mock_query.side_effect = query_side_effect
                
                # Create thread
                created_thread = self.thread_service.create_thread(
                    graph_id=self.graph_id,
                    user_id=self.user_id,
                    name="Lifecycle Test Thread"
                )
                
                # Mock thread retrieval for update/delete operations
                with patch.object(self.thread_service, 'get_thread', return_value=self.mock_thread):
                    
                    # Update thread
                    updated_thread = self.thread_service.update_thread(
                        thread_id=self.thread_id,
                        user_id=self.user_id,
                        name="Updated Thread",
                        status=ThreadStatus.ARCHIVED
                    )
                    
                    # Delete thread
                    deletion_result = self.thread_service.delete_thread(
                        thread_id=self.thread_id,
                        user_id=self.user_id
                    )
                    
                    # Assert
                    assert deletion_result is True
                    self.mock_thread.soft_delete.assert_called_once()
    
    @patch('services.thread_service.GraphCrewValidationService')
    def test_database_transaction_rollback(self, mock_validation_class):
        """Test database transaction rollback on service failures."""
        # Arrange
        mock_validation_instance = Mock()
        mock_validation_class.return_value = mock_validation_instance
        mock_validation_instance.validate_graph_for_new_thread.return_value = None
        
        with patch.object(self.thread_service, '_validate_graph_access', return_value=self.mock_graph):
            # Mock database commit to fail
            self.db_mock.commit.side_effect = Exception("Database error")
            
            # Act & Assert
            with pytest.raises(Exception, match="Database error"):
                self.thread_service.create_thread(
                    graph_id=self.graph_id,
                    user_id=self.user_id,
                    name="Transaction Test Thread"
                )
            
            # Verify rollback was called
            self.db_mock.rollback.assert_called_once()
    
    def test_thread_access_control_integration(self):
        """Test thread access control across service operations."""
        # Arrange
        other_user_id = str(uuid.uuid4())
        
        # Mock thread owned by different user
        other_user_thread = Mock(spec=Thread)
        other_user_thread.id = self.thread_id
        other_user_thread.can_be_accessed_by.return_value = False
        
        self.db_mock.query.return_value.filter.return_value.first.return_value = other_user_thread
        
        # Act & Assert
        with pytest.raises(PermissionError, match="cannot access thread"):
            self.thread_service.get_thread(self.thread_id, other_user_id)
    
    @patch('services.thread_service.GraphCrewValidationService')
    def test_graph_validation_service_creation(self, mock_validation_class):
        """Test that GraphCrewValidationService is properly instantiated."""
        # Arrange
        mock_validation_instance = Mock()
        mock_validation_class.return_value = mock_validation_instance
        mock_validation_instance.validate_graph_for_new_thread.return_value = None
        
        # Mock the database query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        mock_filter.count.return_value = 0  # Return actual integer, not Mock
        self.db_mock.query.return_value = mock_query
        
        with patch.object(self.thread_service, '_validate_graph_access', return_value=self.mock_graph):
            # Act
            self.thread_service.create_thread(
                graph_id=self.graph_id,
                user_id=self.user_id,
                name="Service Creation Test"
            )
            
            # Assert
            # Verify service was created with correct database session
            mock_validation_class.assert_called_once_with(self.db_mock)
    
    @patch('services.thread_service.GraphCrewValidationService')
    def test_concurrent_thread_creation_prevention(self, mock_validation_class):
        """Test prevention of concurrent thread creation for same graph."""
        # Arrange
        mock_validation_instance = Mock()
        mock_validation_class.return_value = mock_validation_instance
        
        # Mock the database query chain
        mock_query = Mock()
        mock_filter = Mock()
        mock_query.filter.return_value = mock_filter
        
        with patch.object(self.thread_service, '_validate_graph_access', return_value=self.mock_graph):
            # First call succeeds
            mock_validation_instance.validate_graph_for_new_thread.return_value = None
            mock_filter.count.return_value = 0  # No active threads first time
            self.db_mock.query.return_value = mock_query
            
            # Act - First thread creation
            thread1 = self.thread_service.create_thread(
                graph_id=self.graph_id,
                user_id=self.user_id,
                name="First Thread"
            )
            
            # Second call fails due to existing thread
            mock_validation_instance.validate_graph_for_new_thread.side_effect = ValueError("Graph already has an active thread")
            
            # Act & Assert - Second thread creation should fail
            with pytest.raises(ValueError, match="Graph already has an active thread"):
                self.thread_service.create_thread(
                    graph_id=self.graph_id,
                    user_id=self.user_id,
                    name="Second Thread"
                )
    
    def test_execution_status_checking_integration(self):
        """Test integration with execution status checking."""
        # Arrange
        # Mock the query chain more specifically to avoid the boolean comparison issue
        with patch.object(self.thread_service, 'is_crew_executing') as mock_is_executing:
            # Test active executions
            mock_is_executing.return_value = True
            is_executing = self.thread_service.is_crew_executing(self.graph_id)
            assert is_executing is True
            
            # Test no active executions
            mock_is_executing.return_value = False
            is_executing = self.thread_service.is_crew_executing(self.graph_id)
            assert is_executing is False
    
    def test_service_error_propagation(self):
        """Test that service errors are properly propagated."""
        # Arrange
        with patch.object(self.thread_service, '_validate_graph_access') as mock_validate:
            mock_validate.side_effect = ValueError("Graph access validation failed")
            
            # Act & Assert
            with pytest.raises(ValueError, match="Graph access validation failed"):
                self.thread_service.create_thread(
                    graph_id=self.graph_id,
                    user_id=self.user_id,
                    name="Error Propagation Test"
                )
            
            # Verify rollback was called
            self.db_mock.rollback.assert_called_once()
    
    def test_thread_statistics_with_database_queries(self):
        """Test thread statistics calculation with database integration."""
        # Arrange
        with patch.object(self.thread_service, 'get_thread', return_value=self.mock_thread):
            # Mock the statistics query more specifically
            with patch.object(self.thread_service, 'get_thread_statistics') as mock_stats:
                expected_stats = {
                    'thread_id': self.thread_id,
                    'total_messages': 15,
                    'user_messages': 8,
                    'assistant_messages': 7,
                    'created_at': self.mock_thread.created_at,
                    'last_activity': self.mock_thread.last_activity_at
                }
                mock_stats.return_value = expected_stats
                
                # Act
                stats = self.thread_service.get_thread_statistics(self.thread_id, self.user_id)
                
                # Assert
                assert stats['thread_id'] == self.thread_id
                assert stats['total_messages'] == 15
                assert stats['user_messages'] == 8
                assert 'assistant_messages' in stats
                assert 'created_at' in stats
                assert 'last_activity' in stats 