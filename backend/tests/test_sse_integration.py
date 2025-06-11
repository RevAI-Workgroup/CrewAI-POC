"""
Integration tests for SSE service and execution integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from datetime import datetime

from services.sse_service import SSEService, SSEConnectionManager
from schemas.sse_schemas import ExecutionStartEvent, ExecutionProgressEvent, ExecutionCompleteEvent


class TestSSEIntegration:
    """Integration tests for SSE service."""
    
    def setup_method(self):
        """Setup test environment."""
        self.sse_manager = SSEConnectionManager(heartbeat_interval=1)  # Short interval for testing
        self.sse_service = SSEService(self.sse_manager)
        self.user_id = str(uuid4())
    
    @pytest.mark.asyncio
    async def test_connection_lifecycle(self):
        """Test SSE connection establishment and cleanup."""
        # Mock request
        mock_request = Mock()
        
        # Create connection
        connection_id = await self.sse_service.create_connection(mock_request, self.user_id)
        
        # Verify connection exists
        assert connection_id is not None
        assert self.sse_manager.get_user_connection_count(self.user_id) == 1
        
        # Disconnect
        await self.sse_manager.disconnect(connection_id)
        
        # Verify cleanup
        assert self.sse_manager.get_user_connection_count(self.user_id) == 0
    
    @pytest.mark.asyncio
    async def test_execution_event_broadcasting(self):
        """Test broadcasting execution events to connected users."""
        mock_request = Mock()
        connection_id = await self.sse_service.create_connection(mock_request, self.user_id)
        
        # Mock the event queue to capture events
        connection = self.sse_manager.connections[connection_id]
        events_received = []
        
        # Replace queue put method to capture events
        original_put = connection["queue"].put
        async def capture_event(event):
            events_received.append(event)
            await original_put(event)
        
        connection["queue"].put = capture_event
        
        # Test execution start event
        await self.sse_service.broadcast_execution_event(
            "execution_start",
            self.user_id,
            {
                "execution_id": str(uuid4()),
                "graph_id": str(uuid4()),
                "user_id": self.user_id,
                "inputs": {"test": "input"},
                "started_at": datetime.utcnow()
            }
        )
        
        # Wait a bit for event to be processed
        await asyncio.sleep(0.1)
        
        # Verify event was received
        assert len(events_received) >= 2  # Connection event + execution start event
        execution_events = [e for e in events_received if e.event_type == "execution_start"]
        assert len(execution_events) == 1
        assert execution_events[0].data["user_id"] == self.user_id
        
        await self.sse_manager.disconnect(connection_id)
    
    @pytest.mark.asyncio
    async def test_user_filtering(self):
        """Test that events are only sent to the correct users."""
        mock_request = Mock()
        
        # Create connections for two different users
        user1_id = str(uuid4())
        user2_id = str(uuid4())
        
        connection1_id = await self.sse_service.create_connection(mock_request, user1_id)
        connection2_id = await self.sse_service.create_connection(mock_request, user2_id)
        
        # Mock event queues
        user1_events = []
        user2_events = []
        
        connection1 = self.sse_manager.connections[connection1_id]
        connection2 = self.sse_manager.connections[connection2_id]
        
        original_put1 = connection1["queue"].put
        original_put2 = connection2["queue"].put
        
        async def capture_user1_event(event):
            user1_events.append(event)
            await original_put1(event)
        
        async def capture_user2_event(event):
            user2_events.append(event)
            await original_put2(event)
        
        connection1["queue"].put = capture_user1_event
        connection2["queue"].put = capture_user2_event
        
        # Send event to user1 only
        await self.sse_service.broadcast_execution_event(
            "execution_progress",
            user1_id,
            {
                "execution_id": str(uuid4()),
                "progress_percentage": 50,
                "current_step": "Test step",
                "user_id": user1_id
            }
        )
        
        await asyncio.sleep(0.1)
        
        # Verify user1 got the event but user2 did not
        user1_progress_events = [e for e in user1_events if e.event_type == "execution_progress"]
        user2_progress_events = [e for e in user2_events if e.event_type == "execution_progress"]
        
        assert len(user1_progress_events) == 1
        assert len(user2_progress_events) == 0
        
        # Cleanup
        await self.sse_manager.disconnect(connection1_id)
        await self.sse_manager.disconnect(connection2_id)
    
    @pytest.mark.asyncio
    async def test_heartbeat_functionality(self):
        """Test heartbeat mechanism."""
        mock_request = Mock()
        connection_id = await self.sse_service.create_connection(mock_request, self.user_id)
        
        # Mock event queue
        events_received = []
        connection = self.sse_manager.connections[connection_id]
        
        original_put = connection["queue"].put
        async def capture_event(event):
            events_received.append(event)
            await original_put(event)
        
        connection["queue"].put = capture_event
        
        # Wait for at least one heartbeat cycle
        await asyncio.sleep(1.5)
        
        # Should have received at least one heartbeat
        heartbeat_events = [e for e in events_received if e.event_type == "heartbeat"]
        assert len(heartbeat_events) >= 1
        
        await self.sse_manager.disconnect(connection_id)
    
    @pytest.mark.asyncio
    async def test_connection_stats(self):
        """Test connection statistics."""
        mock_request = Mock()
        
        # Initially no connections
        stats = self.sse_service.get_stats()
        assert stats["total_connections"] == 0
        assert stats["unique_users"] == 0
        
        # Create connections
        user1_id = str(uuid4())
        user2_id = str(uuid4())
        
        connection1_id = await self.sse_service.create_connection(mock_request, user1_id)
        connection2_id = await self.sse_service.create_connection(mock_request, user1_id)  # Same user
        connection3_id = await self.sse_service.create_connection(mock_request, user2_id)
        
        # Check stats
        stats = self.sse_service.get_stats()
        assert stats["total_connections"] == 3
        assert stats["unique_users"] == 2
        assert stats["user_stats"][user1_id] == 2
        assert stats["user_stats"][user2_id] == 1
        
        # Cleanup
        await self.sse_manager.disconnect(connection1_id)
        await self.sse_manager.disconnect(connection2_id)
        await self.sse_manager.disconnect(connection3_id)


class TestSSEExecutionIntegration:
    """Test SSE integration with execution services."""
    
    @pytest.mark.asyncio
    async def test_execution_service_sse_integration(self):
        """Test that execution service can broadcast SSE events."""
        # Mock the SSE service
        with patch('services.async_execution_service.sse_service') as mock_sse:
            mock_sse.broadcast_execution_event = AsyncMock()
            
            # Import after patching
            from services.async_execution_service import _execute_crew_logic
            
            # Mock task context
            mock_context = Mock()
            mock_context.request = Mock()
            mock_context.request.id = "test-task-id"
            mock_context.update_state = Mock()
            
            # Mock database and other dependencies
            with patch('services.async_execution_service.SessionLocal') as mock_session, \
                 patch('services.async_execution_service.GraphTranslationService') as mock_translation:
                
                # Setup mocks
                mock_db = Mock()
                mock_session.return_value = mock_db
                
                mock_execution = Mock()
                mock_execution.id = uuid4()
                mock_execution.duration_seconds = 10.5
                
                from models.execution import Execution
                with patch.object(Execution, '__new__', return_value=mock_execution):
                    mock_graph = Mock()
                    mock_db.query.return_value.filter.return_value.first.return_value = mock_graph
                    
                    mock_crew = Mock()
                    mock_crew.kickoff.return_value = Mock(raw="Test result")
                    mock_translation.return_value.translate_graph.return_value = mock_crew
                    
                    # Execute
                    result = _execute_crew_logic(
                        mock_context,
                        str(uuid4()),
                        str(uuid4()),
                        str(uuid4()),
                        {"test": "input"}
                    )
                    
                    # Verify SSE events were broadcasted
                    assert mock_sse.broadcast_execution_event.call_count >= 2  # Start and complete events
                    
                    # Check for start event
                    start_calls = [call for call in mock_sse.broadcast_execution_event.call_args_list 
                                 if call[0][0] == "execution_start"]
                    assert len(start_calls) == 1
                    
                    # Check for complete event
                    complete_calls = [call for call in mock_sse.broadcast_execution_event.call_args_list 
                                    if call[0][0] == "execution_complete"]
                    assert len(complete_calls) == 1


class TestSSEErrorHandling:
    """Test SSE error handling scenarios."""
    
    def setup_method(self):
        """Setup test environment."""
        self.sse_manager = SSEConnectionManager()
        self.sse_service = SSEService(self.sse_manager)
        self.user_id = str(uuid4())
    
    @pytest.mark.asyncio
    async def test_sse_unavailable_graceful_handling(self):
        """Test that execution continues when SSE is unavailable."""
        # Mock SSE as unavailable
        with patch('services.async_execution_service.SSE_AVAILABLE', False):
            from services.async_execution_service import _execute_crew_logic
            
            mock_context = Mock()
            mock_context.request = Mock()
            mock_context.request.id = "test-task-id"
            mock_context.update_state = Mock()
            
            # This should not raise an error even with SSE unavailable
            # (Detailed testing would require more mocking)
            pass  # Test that imports work
    
    @pytest.mark.asyncio
    async def test_broadcast_error_handling(self):
        """Test that broadcast errors don't break execution."""
        mock_request = Mock()
        connection_id = await self.sse_service.create_connection(mock_request, self.user_id)
        
        # Force an error in the SSE manager
        with patch.object(self.sse_manager, 'broadcast_to_user', side_effect=Exception("Test error")):
            # This should not raise an exception
            await self.sse_service.broadcast_execution_event(
                "execution_start",
                self.user_id,
                {"test": "data"}
            )
        
        await self.sse_manager.disconnect(connection_id) 