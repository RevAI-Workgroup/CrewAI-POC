"""
Test fixtures for execution testing.
"""

import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import Dict, Any, List

from models.execution import Execution, ExecutionStatus, ExecutionPriority
from models.graph import Graph
from models.user import User
from models.thread import Thread


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return uuid4()


@pytest.fixture
def sample_graph_id():
    """Sample graph ID for testing."""
    return uuid4()


@pytest.fixture
def sample_thread_id():
    """Sample thread ID for testing."""
    return uuid4()


@pytest.fixture
def sample_execution_id():
    """Sample execution ID for testing."""
    return uuid4()


@pytest.fixture
def sample_inputs():
    """Sample execution inputs for testing."""
    return {
        "query": "test query",
        "context": "test context",
        "parameters": {"param1": "value1", "param2": 42}
    }


@pytest.fixture
def sample_graph_data():
    """Sample graph data for testing."""
    return {
        "nodes": [
            {
                "id": "agent1",
                "type": "agent",
                "data": {
                    "role": "Research Assistant",
                    "goal": "Research and analyze information",
                    "backstory": "You are an expert researcher",
                    "tools": []
                }
            },
            {
                "id": "task1",
                "type": "task",
                "data": {
                    "description": "Research the given topic",
                    "expected_output": "Comprehensive research report",
                    "agent": "agent1"
                }
            }
        ],
        "edges": [
            {
                "id": "edge1",
                "source": "agent1",
                "target": "task1",
                "type": "assignment"
            }
        ]
    }


@pytest.fixture
def mock_graph(sample_graph_id, sample_graph_data):
    """Mock graph object for testing."""
    graph = Mock(spec=Graph)
    graph.id = sample_graph_id
    graph.graph_data = sample_graph_data
    graph.name = "Test Graph"
    graph.description = "Test graph for execution testing"
    return graph


@pytest.fixture
def mock_execution(sample_execution_id, sample_graph_id):
    """Mock execution object for testing."""
    execution = Mock(spec=Execution)
    execution.id = sample_execution_id
    execution.graph_id = sample_graph_id
    execution.status = ExecutionStatus.PENDING
    execution.priority = ExecutionPriority.NORMAL
    execution.execution_config = {"test": "config"}
    execution.started_at = None
    execution.completed_at = None
    execution.result_data = None
    execution.error_message = None
    execution.progress_percentage = 0
    
    # Mock methods
    execution.start_execution = Mock()
    execution.complete_execution = Mock()
    execution.fail_execution = Mock()
    execution.update_progress = Mock()
    
    return execution


@pytest.fixture
def mock_crew():
    """Mock CrewAI crew for testing."""
    crew = Mock()
    crew.kickoff = Mock()
    crew.kickoff.return_value = Mock()
    crew.kickoff.return_value.raw = "Test execution result"
    return crew


@pytest.fixture
def mock_celery_task():
    """Mock Celery task for testing."""
    task = Mock()
    task.id = "test-task-id"
    task.status = "SUCCESS"
    task.result = {"test": "result"}
    task.ready.return_value = True
    task.failed.return_value = False
    task.date_done = datetime.utcnow()
    return task


@pytest.fixture
def execution_test_data():
    """Complete test data set for execution testing."""
    return {
        "graph_id": str(uuid4()),
        "thread_id": str(uuid4()),
        "user_id": str(uuid4()),
        "inputs": {"query": "test", "context": "context"},
        "expected_result": "execution result",
        "task_id": "test-task-id"
    }


@pytest.fixture
def error_scenarios():
    """Different error scenarios for testing."""
    return [
        {
            "name": "graph_not_found",
            "error": ValueError("Graph not found"),
            "expected_status": ExecutionStatus.FAILED,
            "should_retry": False
        },
        {
            "name": "crewai_error",
            "error": Exception("CrewAI execution failed"),
            "expected_status": ExecutionStatus.FAILED,
            "should_retry": True
        },
        {
            "name": "timeout_error",
            "error": TimeoutError("Execution timeout"),
            "expected_status": ExecutionStatus.TIMEOUT,
            "should_retry": False
        },
        {
            "name": "database_error",
            "error": Exception("Database connection failed"),
            "expected_status": ExecutionStatus.FAILED,
            "should_retry": True
        }
    ]


@pytest.fixture
def performance_test_config():
    """Configuration for performance testing."""
    return {
        "concurrent_executions": [1, 5, 10, 20],
        "execution_timeout": 30,
        "max_response_time": 5.0,
        "min_throughput": 2.0,  # executions per second
        "memory_limit_mb": 512
    }


@pytest.fixture
def mock_database_session():
    """Mock database session for testing."""
    session = Mock()
    session.query.return_value = session
    session.filter.return_value = session
    session.first.return_value = None
    session.add.return_value = None
    session.commit.return_value = None
    session.rollback.return_value = None
    session.close.return_value = None
    return session


@pytest.fixture
def sample_execution_logs():
    """Sample execution logs for testing."""
    return [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": "Starting crew execution",
            "metadata": {"step": "initialization"}
        },
        {
            "timestamp": (datetime.utcnow() + timedelta(seconds=1)).isoformat(),
            "level": "INFO", 
            "message": "Agent executing task",
            "metadata": {"step": "execution", "agent": "Research Assistant"}
        },
        {
            "timestamp": (datetime.utcnow() + timedelta(seconds=5)).isoformat(),
            "level": "INFO",
            "message": "Execution completed",
            "metadata": {"step": "completion", "duration": 5.2}
        }
    ]


@pytest.fixture
def sample_metrics():
    """Sample execution metrics for testing."""
    return {
        "execution_time": 5.23,
        "memory_usage_mb": 128.5,
        "cpu_usage_percent": 45.2,
        "agent_count": 1,
        "task_count": 1,
        "tool_calls": 3,
        "tokens_used": 1250,
        "cost_estimate": 0.05
    } 