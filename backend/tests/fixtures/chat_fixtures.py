"""
Test fixtures for chat integration testing.
Provides reusable test data and mock objects for chat functionality.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

from models.user import User
from models.graph import Graph
from models.thread import Thread, ThreadStatus
from models.message import Message, MessageType, MessageStatus
from models.execution import Execution
from schemas.message_schemas import ChatMessageRequest


@pytest.fixture
def sample_user(db_session):
    """Create a test user for chat testing."""
    user = User(
        id=str(uuid4()),
        pseudo="testuser",
        passphrase="test_passphrase_123"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_graph_data():
    """Sample graph data with single crew configuration."""
    return {
        "nodes": [
            {
                "id": "agent-1",
                "type": "agent",
                "data": {
                    "role": "Research Assistant",
                    "goal": "Provide comprehensive research and analysis",
                    "backstory": "You are an expert research assistant with deep knowledge across multiple domains."
                }
            },
            {
                "id": "task-1", 
                "type": "task",
                "data": {
                    "description": "Analyze the given topic thoroughly",
                    "expected_output": "A detailed analysis report"
                }
            },
            {
                "id": "crew-1",
                "type": "crew",
                "data": {
                    "process": "sequential",
                    "verbose": True
                }
            }
        ],
        "edges": [
            {
                "id": "edge-1",
                "source": "agent-1",
                "target": "task-1",
                "type": "assignment"
            },
            {
                "id": "edge-2", 
                "source": "task-1",
                "target": "crew-1",
                "type": "belongs_to"
            }
        ]
    }


@pytest.fixture
def sample_graph(db_session, sample_user, sample_graph_data):
    """Create a test graph with chat-compatible configuration."""
    graph = Graph(
        id=str(uuid4()),
        user_id=str(sample_user.id),
        name="Test Chat Graph",
        description="Graph for chat testing",
        graph_data=sample_graph_data,
        is_active=True
    )
    db_session.add(graph)
    db_session.commit()
    db_session.refresh(graph)
    return graph


@pytest.fixture
def sample_thread(db_session, sample_graph):
    """Create a test thread for chat testing."""
    thread = Thread(
        id=str(uuid4()),
        graph_id=str(sample_graph.id),
        name="Test Chat Thread",
        description="Thread for chat testing",
        status=ThreadStatus.ACTIVE,
        thread_config={}
    )
    db_session.add(thread)
    db_session.commit()
    db_session.refresh(thread)
    return thread


@pytest.fixture
def sample_chat_request(sample_thread):
    """Create a sample chat message request."""
    return ChatMessageRequest(
        message="Analyze the current state of renewable energy technology",
        output="A comprehensive report with key findings and recommendations",
        threadId=str(sample_thread.id)
    )


@pytest.fixture
def sample_user_message(db_session, sample_thread, sample_user):
    """Create a sample user message."""
    message = Message(
        id=str(uuid4()),
        thread_id=str(sample_thread.id),
        content="Test user message for chat",
        message_type=MessageType.USER,
        status=MessageStatus.COMPLETED,
        created_by_user_id=str(sample_user.id),
        triggers_execution=True
    )
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)
    return message


@pytest.fixture
def sample_assistant_message(db_session, sample_thread, sample_user):
    """Create a sample assistant message."""
    message = Message(
        id=str(uuid4()),
        thread_id=str(sample_thread.id),
        content="Test assistant response",
        message_type=MessageType.ASSISTANT,
        status=MessageStatus.PROCESSING,
        created_by_user_id=str(sample_user.id),
        triggers_execution=False
    )
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)
    return message


@pytest.fixture
def sample_execution(db_session, sample_graph, sample_user):
    """Create a sample execution record."""
    execution = Execution(
        id=str(uuid4()),
        graph_id=str(sample_graph.id),
        user_id=str(sample_user.id),
        status='running',
        execution_config={
            'message': 'Test chat message',
            'output': 'Expected output format',
            'thread_id': 'thread-123'
        }
    )
    db_session.add(execution)
    db_session.commit()
    db_session.refresh(execution)
    return execution


@pytest.fixture
def invalid_graph_data():
    """Graph data that should fail validation."""
    return {
        "nodes": [
            {
                "id": "crew-1",
                "type": "crew",
                "data": {"process": "sequential"}
            },
            {
                "id": "crew-2", 
                "type": "crew",
                "data": {"process": "hierarchical"}
            }
        ],
        "edges": []
    }


@pytest.fixture
def mock_crewai_crew():
    """Mock CrewAI crew for testing."""
    mock_crew = Mock()
    mock_crew.agents = [Mock(role="Test Agent")]
    mock_crew.tasks = []
    
    # Mock result object
    mock_result = Mock()
    mock_result.raw = "This is a test response from the CrewAI execution."
    
    mock_crew.kickoff.return_value = mock_result
    return mock_crew


@pytest.fixture
def mock_graph_translation_service():
    """Mock GraphTranslationService for testing."""
    service = Mock()
    service.translate_graph.return_value = Mock()
    return service


@pytest.fixture
def mock_streaming_chunks():
    """Sample streaming response chunks for testing."""
    return [
        "This is the first chunk of ",
        "the streaming response from ",
        "the CrewAI execution. It contains ",
        "detailed analysis and findings."
    ]


@pytest.fixture
def auth_headers(sample_user):
    """Create authentication headers for API testing."""
    # In real implementation, this would create a proper JWT token
    return {
        "Authorization": f"Bearer test-token-{sample_user.id}",
        "Content-Type": "application/json"
    }


@pytest.fixture
def chat_error_scenarios():
    """Various error scenarios for chat testing."""
    return {
        "thread_not_found": {
            "threadId": "non-existent-thread",
            "expected_status": 404,
            "expected_message": "Thread not found"
        },
        "graph_translation_error": {
            "error_type": "GraphTranslationError",
            "expected_status": 500,
            "expected_message": "Failed to translate graph"
        },
        "crewai_execution_error": {
            "error_type": "CrewExecutionError", 
            "expected_status": 500,
            "expected_message": "CrewAI execution failed"
        },
        "concurrent_execution": {
            "expected_status": 409,
            "expected_message": "Crew is already executing"
        }
    }


@pytest.fixture
def performance_test_data():
    """Data for performance testing scenarios."""
    return {
        "large_message": "A" * 5000,  # 5KB message
        "concurrent_users": 5,
        "max_response_time": 2.0,  # seconds
        "max_memory_usage": 100 * 1024 * 1024,  # 100MB
        "streaming_chunk_delay": 0.1  # seconds
    }


@pytest.fixture
def multiple_threads(db_session, sample_graph, sample_user):
    """Create multiple threads for testing."""
    threads = []
    for i in range(3):
        thread = Thread(
            id=str(uuid4()),
            graph_id=str(sample_graph.id),
            name=f"Test Thread {i+1}",
            description=f"Thread {i+1} for testing",
            status=ThreadStatus.ACTIVE,
            thread_config={}
        )
        db_session.add(thread)
        threads.append(thread)
    
    db_session.commit()
    for thread in threads:
        db_session.refresh(thread)
    return threads


@pytest.fixture
def chat_integration_config():
    """Configuration for chat integration testing."""
    return {
        "streaming_timeout": 30,
        "chunk_size": 50,
        "max_retries": 3,
        "test_isolation": True,
        "mock_external_services": True
    }


class MockStreamingResponse:
    """Mock streaming response for testing."""
    
    def __init__(self, chunks: List[str], include_error: bool = False):
        self.chunks = chunks
        self.include_error = include_error
        self._index = 0
    
    async def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self._index >= len(self.chunks):
            if self.include_error:
                raise StopAsyncIteration("Streaming error occurred")
            raise StopAsyncIteration
        
        chunk = self.chunks[self._index]
        self._index += 1
        
        # Format as event-stream data
        if self._index == len(self.chunks):
            return f"data: {json.dumps({'content': chunk, 'done': True})}\n\n"
        else:
            return f"data: {json.dumps({'content': chunk})}\n\n" 