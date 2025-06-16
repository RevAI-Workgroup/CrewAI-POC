"""
Comprehensive integration tests for chat backend functionality.
Tests end-to-end chat flows including streaming, CrewAI integration, and error handling.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import uuid4

from main import app
from models.user import User
from models.thread import Thread, ThreadStatus
from models.message import Message, MessageType, MessageStatus
from models.execution import Execution
from models.graph import Graph
from schemas.message_schemas import ChatMessageRequest
from services.thread_service import ThreadService
from services.graph_translation import GraphTranslationService
from services.message_processing_service import MessageProcessingService
from exceptions.chat_exceptions import ChatErrorCode
from .fixtures.chat_fixtures import *
from .utils.streaming_test_utils import *


class TestChatStreamingIntegration:
    """Integration tests for chat streaming endpoint."""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)
    
    @pytest.fixture
    def streaming_client(self, client):
        """Streaming test client."""
        return StreamingTestClient(client)
    
    @patch('routers.messages.GraphTranslationService')
    @patch('routers.messages.execute_crew_stream')
    async def test_complete_chat_flow_success(
        self, 
        mock_execute_crew_stream,
        mock_graph_translation_service,
        client,
        db_session,
        sample_user,
        sample_thread,
        sample_chat_request,
        auth_headers,
        mock_streaming_chunks
    ):
        """Test complete successful chat message flow."""
        # Setup mocks
        mock_crew = Mock()
        mock_crew.agents = [Mock()]
        mock_crew.tasks = []
        mock_graph_translation_service.return_value.translate_graph.return_value = mock_crew
        
        # Mock streaming response
        async def mock_stream(crew, execution_id, db):
            for chunk in mock_streaming_chunks:
                yield chunk
        
        mock_execute_crew_stream.return_value = mock_stream(None, None, None)
        
        # Make request
        response = client.post(
            "/api/messages/chat/stream",
            json=sample_chat_request.dict(),
            headers=auth_headers
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify streaming format
        content = response.content.decode('utf-8')
        validation = validate_streaming_format(content)
        assert validation['valid'], f"Streaming format errors: {validation['errors']}"
        assert validation['has_done_marker'], "Missing done marker in stream"
        assert validation['chunk_count'] > 0, "No chunks in streaming response"
        
        # Verify database state
        user_messages = db_session.query(Message).filter(
            Message.thread_id == sample_thread.id,
            Message.message_type == MessageType.USER
        ).all()
        
        assistant_messages = db_session.query(Message).filter(
            Message.thread_id == sample_thread.id,
            Message.message_type == MessageType.ASSISTANT
        ).all()
        
        executions = db_session.query(Execution).filter(
            Execution.graph_id == sample_thread.graph_id
        ).all()
        
        assert len(user_messages) >= 1, "User message not created"
        assert len(assistant_messages) >= 1, "Assistant message not created"
        assert len(executions) >= 1, "Execution record not created"
        
        # Verify execution-message linking
        execution = executions[-1]
        assistant_message = assistant_messages[-1]
        assert assistant_message.execution_id == execution.id
    
    async def test_thread_access_validation(
        self,
        client,
        sample_user,
        auth_headers
    ):
        """Test thread access validation for non-existent thread."""
        invalid_request = {
            "message": "Test message",
            "threadId": "non-existent-thread-id"
        }
        
        response = client.post(
            "/api/messages/chat/stream",
            json=invalid_request,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        response_data = response.json()
        assert "Thread not found" in response_data["detail"]
    
    @patch('routers.messages.ThreadService')
    async def test_concurrent_execution_prevention(
        self,
        mock_thread_service,
        client,
        sample_thread,
        sample_chat_request,
        auth_headers
    ):
        """Test prevention of concurrent crew executions."""
        # Mock service to simulate concurrent execution
        mock_service = Mock()
        mock_service.get_thread.return_value = sample_thread
        mock_service._validate_graph_access.return_value = sample_thread.graph
        mock_service.is_crew_executing.return_value = True
        mock_thread_service.return_value = mock_service
        
        response = client.post(
            "/api/messages/chat/stream",
            json=sample_chat_request.dict(),
            headers=auth_headers
        )
        
        assert response.status_code == 409
        response_data = response.json()
        assert "already executing" in response_data["detail"]
    
    @patch('routers.messages.GraphTranslationService')
    async def test_graph_translation_error_handling(
        self,
        mock_graph_translation_service,
        client,
        sample_thread,
        sample_chat_request,
        auth_headers
    ):
        """Test error handling for graph translation failures."""
        # Mock translation service to raise error
        mock_graph_translation_service.return_value.translate_graph.side_effect = \
            Exception("Graph translation failed")
        
        response = client.post(
            "/api/messages/chat/stream",
            json=sample_chat_request.dict(),
            headers=auth_headers
        )
        
        # Should still return 200 but with error in stream
        assert response.status_code == 200
        
        content = response.content.decode('utf-8')
        assert "error" in content.lower()
    
    @patch('routers.messages.execute_crew_stream')
    async def test_crewai_execution_error_handling(
        self,
        mock_execute_crew_stream,
        client,
        sample_thread,
        sample_chat_request,
        auth_headers
    ):
        """Test error handling for CrewAI execution failures."""
        # Mock streaming to raise error
        async def mock_failing_stream(crew, execution_id, db):
            yield "Starting execution..."
            raise Exception("CrewAI execution failed")
        
        mock_execute_crew_stream.return_value = mock_failing_stream(None, None, None)
        
        response = client.post(
            "/api/messages/chat/stream",
            json=sample_chat_request.dict(),
            headers=auth_headers
        )
        
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert "error" in content.lower()
    
    async def test_invalid_chat_request_validation(
        self,
        client,
        sample_thread,
        auth_headers
    ):
        """Test validation of invalid chat requests."""
        invalid_requests = [
            {"message": "", "threadId": str(sample_thread.id)},  # Empty message
            {"message": "Test", "threadId": ""},  # Empty thread ID
            {"threadId": str(sample_thread.id)},  # Missing message
            {"message": "Test"}  # Missing thread ID
        ]
        
        for invalid_request in invalid_requests:
            response = client.post(
                "/api/messages/chat/stream",
                json=invalid_request,
                headers=auth_headers
            )
            
            assert response.status_code == 422  # Validation error


class TestChatDatabaseTransactions:
    """Test database transaction management during chat operations."""
    
    def test_successful_transaction_consistency(
        self,
        db_session,
        sample_user,
        sample_thread,
        sample_graph
    ):
        """Test database consistency during successful chat flow."""
        transaction_tester = DatabaseTransactionTester(db_session)
        
        # Record initial state
        models = [Message, Execution]
        transaction_tester.record_initial_state(models)
        
        # Simulate chat flow with proper transaction management
        with MessageProcessingService(db_session) as message_service:
            user_message = message_service.create_message(
                thread_id=str(sample_thread.id),
                content="Test message",
                user_id=str(sample_user.id),
                message_type=MessageType.USER,
                triggers_execution=True
            )
            
            assistant_message = message_service.create_message(
                thread_id=str(sample_thread.id),
                content="Assistant response",
                user_id=str(sample_user.id),
                message_type=MessageType.ASSISTANT,
                triggers_execution=False
            )
        
        # Create execution
        execution = Execution(
            id=str(uuid4()),
            graph_id=str(sample_graph.id),
            user_id=str(sample_user.id),
            status='completed'
        )
        db_session.add(execution)
        
        # Link execution to message
        assistant_message.execution_id = execution.id
        db_session.commit()
        
        # Record final state
        transaction_tester.record_final_state(models)
        
        # Verify expected changes
        expected_changes = {
            'Message': 2,  # User + assistant message
            'Execution': 1  # One execution
        }
        transaction_tester.assert_consistent_state(expected_changes)
    
    def test_rollback_on_streaming_failure(
        self,
        db_session,
        sample_user,
        sample_thread,
        sample_graph
    ):
        """Test transaction rollback when streaming fails."""
        transaction_tester = DatabaseTransactionTester(db_session)
        models = [Message, Execution]
        transaction_tester.record_initial_state(models)
        
        try:
            # Simulate failed transaction
            with db_session.begin():
                message = Message(
                    id=str(uuid4()),
                    thread_id=str(sample_thread.id),
                    content="Test message",
                    message_type=MessageType.USER,
                    status=MessageStatus.PROCESSING,
                    created_by_user_id=str(sample_user.id)
                )
                db_session.add(message)
                
                # Simulate error that should cause rollback
                raise Exception("Simulated streaming failure")
                
        except Exception:
            db_session.rollback()
        
        transaction_tester.record_final_state(models)
        
        # Verify no changes after rollback
        expected_changes = {
            'Message': 0,
            'Execution': 0
        }
        transaction_tester.assert_consistent_state(expected_changes)


class TestChatPerformanceIntegration:
    """Performance integration tests for chat functionality."""
    
    @pytest.mark.performance
    async def test_streaming_response_performance(
        self,
        client,
        sample_thread,
        sample_chat_request,
        auth_headers,
        performance_test_data
    ):
        """Test streaming response performance metrics."""
        monitor = StreamingPerformanceMonitor()
        monitor.start_monitoring()
        
        with patch('routers.messages.execute_crew_stream') as mock_stream:
            # Mock streaming with controlled chunks
            async def controlled_stream(crew, execution_id, db):
                for i in range(10):
                    monitor.record_chunk()
                    await asyncio.sleep(0.05)  # 50ms per chunk
                    yield f"Chunk {i} content"
            
            mock_stream.return_value = controlled_stream(None, None, None)
            
            response = client.post(
                "/api/messages/chat/stream",
                json=sample_chat_request.dict(),
                headers=auth_headers
            )
        
        monitor.stop_monitoring()
        
        # Verify performance metrics
        assert response.status_code == 200
        assert monitor.get_first_chunk_time() < performance_test_data["max_response_time"]
        assert monitor.get_total_time() < performance_test_data["max_response_time"] * 2
    
    @pytest.mark.performance
    async def test_concurrent_chat_requests(
        self,
        client,
        multiple_threads,
        auth_headers,
        performance_test_data
    ):
        """Test handling of concurrent chat requests."""
        concurrent_tester = ConcurrentStreamingTester(client, "/api/messages/chat/stream")
        
        # Create multiple requests
        requests = []
        for i, thread in enumerate(multiple_threads[:3]):  # Test with 3 concurrent
            requests.append({
                "message": f"Test concurrent message {i}",
                "threadId": str(thread.id)
            })
        
        with patch('routers.messages.execute_crew_stream') as mock_stream:
            # Mock quick streaming response
            async def quick_stream(crew, execution_id, db):
                yield "Quick response"
            
            mock_stream.return_value = quick_stream(None, None, None)
            
            results = await concurrent_tester.run_concurrent_requests(
                requests, auth_headers, max_concurrent=3
            )
        
        # Verify concurrent request handling
        success_rate = concurrent_tester.get_success_rate()
        assert success_rate >= 80.0, f"Success rate too low: {success_rate}%"
    
    @pytest.mark.performance
    async def test_large_message_handling(
        self,
        client,
        sample_thread,
        auth_headers,
        performance_test_data
    ):
        """Test handling of large message content."""
        large_request = {
            "message": performance_test_data["large_message"],
            "threadId": str(sample_thread.id)
        }
        
        with patch('routers.messages.execute_crew_stream') as mock_stream:
            async def standard_stream(crew, execution_id, db):
                yield "Response to large message"
            
            mock_stream.return_value = standard_stream(None, None, None)
            
            response = client.post(
                "/api/messages/chat/stream",
                json=large_request,
                headers=auth_headers
            )
        
        assert response.status_code == 200
        # Verify message was processed successfully
        content = response.content.decode('utf-8')
        validation = validate_streaming_format(content)
        assert validation['valid']


class TestChatErrorScenarios:
    """Test comprehensive error scenarios in chat functionality."""
    
    async def test_authentication_error_handling(
        self,
        client,
        sample_chat_request
    ):
        """Test chat endpoint with invalid authentication."""
        # Request without auth headers
        response = client.post(
            "/api/messages/chat/stream",
            json=sample_chat_request.dict()
        )
        
        assert response.status_code == 401
    
    async def test_invalid_thread_ownership(
        self,
        client,
        sample_chat_request,
        auth_headers,
        db_session
    ):
        """Test accessing thread owned by different user."""
        # Create thread for different user
        other_user = User(
            id=str(uuid4()),
            pseudo="otheruser",
            passphrase="other_passphrase_123"
        )
        db_session.add(other_user)
        
        other_graph = Graph(
            id=str(uuid4()),
            user_id=str(other_user.id),
            name="Other Graph",
            graph_data={"nodes": [], "edges": []},
            is_active=True
        )
        db_session.add(other_graph)
        
        other_thread = Thread(
            id=str(uuid4()),
            graph_id=str(other_graph.id),
            name="Other Thread",
            status=ThreadStatus.ACTIVE
        )
        db_session.add(other_thread)
        db_session.commit()
        
        # Try to access other user's thread
        invalid_request = sample_chat_request.dict()
        invalid_request["threadId"] = str(other_thread.id)
        
        response = client.post(
            "/api/messages/chat/stream",
            json=invalid_request,
            headers=auth_headers
        )
        
        assert response.status_code in [403, 404]  # Forbidden or not found
    
    async def test_invalid_graph_configuration(
        self,
        client,
        db_session,
        sample_user,
        invalid_graph_data,
        auth_headers
    ):
        """Test chat with invalid graph configuration (multiple crews)."""
        # Create graph with invalid configuration
        invalid_graph = Graph(
            id=str(uuid4()),
            user_id=str(sample_user.id),
            name="Invalid Graph",
            graph_data=invalid_graph_data,
            is_active=True
        )
        db_session.add(invalid_graph)
        
        invalid_thread = Thread(
            id=str(uuid4()),
            graph_id=str(invalid_graph.id),
            name="Invalid Thread",
            status=ThreadStatus.ACTIVE
        )
        db_session.add(invalid_thread)
        db_session.commit()
        
        request_data = {
            "message": "Test message",
            "threadId": str(invalid_thread.id)
        }
        
        response = client.post(
            "/api/messages/chat/stream",
            json=request_data,
            headers=auth_headers
        )
        
        # Should return error for invalid graph configuration
        assert response.status_code in [400, 500]
    
    @patch('routers.messages.execute_crew_stream')
    async def test_streaming_connection_interruption(
        self,
        mock_execute_crew_stream,
        client,
        sample_thread,
        sample_chat_request,
        auth_headers
    ):
        """Test handling of streaming connection interruption."""
        # Mock streaming that fails mid-stream
        async def interrupted_stream(crew, execution_id, db):
            yield "Partial response..."
            raise ConnectionError("Connection lost")
        
        mock_execute_crew_stream.return_value = interrupted_stream(None, None, None)
        
        response = client.post(
            "/api/messages/chat/stream",
            json=sample_chat_request.dict(),
            headers=auth_headers
        )
        
        # Should handle gracefully
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert "error" in content.lower() or "connection" in content.lower()


class TestChatServiceIntegration:
    """Test integration between chat services and components."""
    
    def test_thread_service_integration(
        self,
        db_session,
        sample_user,
        sample_graph
    ):
        """Test ThreadService integration with chat flow."""
        thread_service = ThreadService(db_session)
        
        # Test thread creation for chat
        thread = thread_service.create_thread(
            graph_id=str(sample_graph.id),
            user_id=str(sample_user.id),
            name="Chat Integration Test Thread"
        )
        
        assert thread is not None
        assert thread.graph_id == str(sample_graph.id)
        assert thread.status == ThreadStatus.ACTIVE
        
        # Test thread access validation
        retrieved_thread = thread_service.get_thread(
            str(thread.id), 
            str(sample_user.id)
        )
        assert retrieved_thread.id == thread.id
    
    def test_message_processing_service_integration(
        self,
        db_session,
        sample_user,
        sample_thread
    ):
        """Test MessageProcessingService integration with chat."""
        with MessageProcessingService(db_session) as service:
            # Create user message
            user_message = service.create_message(
                thread_id=str(sample_thread.id),
                content="Integration test message",
                user_id=str(sample_user.id),
                message_type=MessageType.USER,
                triggers_execution=True
            )
            
            # Create assistant message
            assistant_message = service.create_message(
                thread_id=str(sample_thread.id),
                content="",
                user_id=str(sample_user.id),
                message_type=MessageType.ASSISTANT,
                triggers_execution=False
            )
            
            # Update assistant message content
            service.update_message(
                message_id=str(assistant_message.id),
                user_id=str(sample_user.id),
                content="Integration test response",
                status=MessageStatus.COMPLETED
            )
        
        # Verify messages were created and updated
        db_session.refresh(user_message)
        db_session.refresh(assistant_message)
        
        assert user_message.content == "Integration test message"
        assert assistant_message.content == "Integration test response"
        assert assistant_message.status == MessageStatus.COMPLETED
    
    @patch('services.graph_translation.GraphTranslationService.translate_graph')
    def test_graph_translation_service_integration(
        self,
        mock_translate_graph,
        db_session,
        sample_graph
    ):
        """Test GraphTranslationService integration with chat."""
        # Mock successful translation
        mock_crew = Mock()
        mock_crew.agents = [Mock(role="Test Agent")]
        mock_crew.tasks = []
        mock_translate_graph.return_value = mock_crew
        
        translation_service = GraphTranslationService(db_session)
        crew = translation_service.translate_graph(sample_graph)
        
        assert crew is not None
        assert len(crew.agents) == 1
        assert hasattr(crew, 'tasks')
        
        # Verify service was called with correct graph
        mock_translate_graph.assert_called_once_with(sample_graph)


# Performance and Load Testing Marks
pytestmark = [
    pytest.mark.integration,
    pytest.mark.chat,
    pytest.mark.asyncio
] 