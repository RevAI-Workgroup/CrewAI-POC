"""
Test utilities for execution testing.
"""

import asyncio
import time
import threading
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from typing import Dict, Any, List, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
from contextlib import contextmanager
from uuid import uuid4

from models.execution import Execution, ExecutionStatus
from services.async_execution_service import AsyncExecutionService


class ExecutionTestHelper:
    """Helper class for execution testing."""
    
    @staticmethod
    def create_test_execution(
        graph_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: ExecutionStatus = ExecutionStatus.PENDING,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a test execution configuration."""
        return {
            "graph_id": graph_id or str(uuid4()),
            "thread_id": thread_id or str(uuid4()),
            "user_id": user_id or str(uuid4()),
            "status": status,
            "inputs": {"test": "input"},
            "execution_config": {"test": "config"},
            **kwargs
        }
    
    @staticmethod
    def mock_celery_task(
        task_id: str = "test-task-id",
        status: str = "SUCCESS",
        result: Any = None,
        error: Optional[Exception] = None
    ) -> Mock:
        """Create a mock Celery task."""
        task = Mock()
        task.id = task_id
        task.status = status
        task.result = result if result is not None else {"test": "result"}
        task.ready.return_value = status in ["SUCCESS", "FAILURE", "REVOKED"]
        task.failed.return_value = status == "FAILURE"
        task.successful.return_value = status == "SUCCESS"
        
        if error:
            task.traceback = str(error)
            task.result = error
        
        return task
    
    @staticmethod
    def mock_crew_execution(result: str = "Test execution result", error: Optional[Exception] = None):
        """Create a mock CrewAI crew execution."""
        crew = Mock()
        if error:
            crew.kickoff.side_effect = error
        else:
            crew.kickoff.return_value = Mock(raw=result)
        return crew
    
    @staticmethod
    def simulate_execution_progress(
        update_callback: Callable[[int, str], None],
        steps: Optional[List[Dict[str, Any]]] = None
    ):
        """Simulate execution progress with callbacks."""
        if steps is None:
            steps = [
                {"progress": 10, "message": "Initializing execution"},
                {"progress": 25, "message": "Loading graph"},
                {"progress": 50, "message": "Executing crew"},
                {"progress": 75, "message": "Processing results"},
                {"progress": 100, "message": "Execution completed"}
            ]
        
        for step in steps:
            update_callback(step["progress"], step["message"])
            time.sleep(0.1)  # Simulate processing time


class PerformanceTestRunner:
    """Performance testing utilities for execution service."""
    
    def __init__(self):
        self.results = []
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process()
        else:
            self.process = None
    
    def run_concurrent_executions(
        self,
        execution_count: int,
        execution_function: Callable,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Run multiple executions concurrently and measure performance."""
        start_time = time.time()
        start_memory = 0.0
        if self.process is not None:
            start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=execution_count) as executor:
            # Submit all executions
            futures = [
                executor.submit(self._timed_execution, execution_function, i)
                for i in range(execution_count)
            ]
            
            # Collect results
            for future in as_completed(futures, timeout=timeout):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    errors.append(str(e))
        
        end_time = time.time()
        end_memory = 0.0
        if self.process is not None:
            end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        total_time = end_time - start_time
        memory_delta = end_memory - start_memory
        
        return {
            "execution_count": execution_count,
            "total_time": total_time,
            "average_time": total_time / execution_count if execution_count > 0 else 0,
            "throughput": execution_count / total_time if total_time > 0 else 0,
            "memory_delta_mb": memory_delta,
            "success_count": len(results),
            "error_count": len(errors),
            "success_rate": len(results) / execution_count if execution_count > 0 else 0,
            "errors": errors,
            "individual_times": [r["execution_time"] for r in results]
        }
    
    def _timed_execution(self, execution_function: Callable, execution_id: int) -> Dict[str, Any]:
        """Execute a function and measure its performance."""
        start_time = time.time()
        try:
            result = execution_function(execution_id)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        
        return {
            "execution_id": execution_id,
            "execution_time": end_time - start_time,
            "success": success,
            "result": result,
            "error": error
        }
    
    def measure_memory_usage(self, execution_function: Callable) -> Dict[str, float]:
        """Measure memory usage during execution."""
        if self.process is None:
            # Return zero values when psutil is not available
            return {
                "initial_memory_mb": 0.0,
                "final_memory_mb": 0.0,
                "memory_delta_mb": 0.0
            }
        
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        execution_function()
        
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_delta_mb": final_memory - initial_memory
        }


class MockExecutionService:
    """Mock execution service for testing without external dependencies."""
    
    def __init__(self):
        self.executions = {}
        self.task_counter = 0
    
    def queue_execution(
        self,
        graph_id: str,
        thread_id: str,
        user_id: str,
        inputs: Dict[str, Any],
        priority: int = 5
    ) -> str:
        """Mock execution queueing."""
        self.task_counter += 1
        task_id = f"mock-task-{self.task_counter}"
        
        self.executions[task_id] = {
            "task_id": task_id,
            "graph_id": graph_id,
            "thread_id": thread_id,
            "user_id": user_id,
            "inputs": inputs,
            "priority": priority,
            "status": "PENDING",
            "result": None,
            "error": None
        }
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Mock task status retrieval."""
        if task_id not in self.executions:
            return {"task_id": task_id, "status": "UNKNOWN", "error": "Task not found"}
        
        return self.executions[task_id]
    
    def simulate_execution_completion(
        self,
        task_id: str,
        result: Any = None,
        error: Optional[str] = None
    ):
        """Simulate execution completion for testing."""
        if task_id in self.executions:
            if error:
                self.executions[task_id]["status"] = "FAILURE"
                self.executions[task_id]["error"] = error
            else:
                self.executions[task_id]["status"] = "SUCCESS"
                self.executions[task_id]["result"] = result or "Mock execution result"
    
    def cancel_task(self, task_id: str) -> bool:
        """Mock task cancellation."""
        if task_id in self.executions:
            self.executions[task_id]["status"] = "REVOKED"
            return True
        return False


@contextmanager
def mock_execution_environment():
    """Context manager to mock execution environment for testing."""
    with patch('services.async_execution_service.celery_app') as mock_celery, \
         patch('services.async_execution_service.SessionLocal') as mock_session, \
         patch('services.async_execution_service.GraphTranslationService') as mock_translation:
        
        # Setup mock database session
        mock_db = Mock()
        mock_session.return_value = mock_db
        
        # Setup mock Celery app
        mock_task = Mock()
        mock_task.id = "test-task-id"
        mock_celery.AsyncResult.return_value = mock_task
        
        # Setup mock translation service
        mock_crew = Mock()
        mock_crew.kickoff.return_value = Mock(raw="Test result")
        mock_translation.return_value.translate_graph.return_value = mock_crew
        
        yield {
            "celery_app": mock_celery,
            "session": mock_db,
            "translation_service": mock_translation,
            "crew": mock_crew
        }


class ExecutionTestAssertions:
    """Custom assertions for execution testing."""
    
    @staticmethod
    def assert_execution_success(result: Dict[str, Any]):
        """Assert that execution completed successfully."""
        assert result["status"] == "success", f"Execution failed: {result.get('error', 'Unknown error')}"
        assert "execution_id" in result, "Result missing execution_id"
        assert "result" in result, "Result missing execution result"
    
    @staticmethod
    def assert_execution_failure(result: Dict[str, Any], expected_error: Optional[str] = None):
        """Assert that execution failed as expected."""
        assert result["status"] == "failed", f"Expected failure but got: {result['status']}"
        assert "error" in result, "Result missing error information"
        
        if expected_error:
            assert expected_error in result["error"], f"Expected error '{expected_error}' not found in '{result['error']}'"
    
    @staticmethod
    def assert_performance_within_limits(
        performance_result: Dict[str, Any],
        max_response_time: float = 5.0,
        min_success_rate: float = 0.95,
        max_memory_mb: float = 500.0
    ):
        """Assert that performance metrics are within acceptable limits."""
        assert performance_result["average_time"] <= max_response_time, \
            f"Average response time {performance_result['average_time']}s exceeds limit {max_response_time}s"
        
        assert performance_result["success_rate"] >= min_success_rate, \
            f"Success rate {performance_result['success_rate']} below minimum {min_success_rate}"
        
        if "memory_delta_mb" in performance_result:
            assert performance_result["memory_delta_mb"] <= max_memory_mb, \
                f"Memory usage {performance_result['memory_delta_mb']}MB exceeds limit {max_memory_mb}MB"


def create_test_graph_data(agent_count: int = 1, task_count: int = 1) -> Dict[str, Any]:
    """Create test graph data with specified number of agents and tasks."""
    nodes = []
    edges = []
    
    # Create agents
    for i in range(agent_count):
        nodes.append({
            "id": f"agent{i+1}",
            "type": "agent",
            "data": {
                "role": f"Test Agent {i+1}",
                "goal": f"Complete assigned tasks {i+1}",
                "backstory": f"You are test agent number {i+1}",
                "tools": []
            }
        })
    
    # Create tasks
    for i in range(task_count):
        agent_id = f"agent{(i % agent_count) + 1}"  # Round-robin assignment
        nodes.append({
            "id": f"task{i+1}",
            "type": "task",
            "data": {
                "description": f"Test task {i+1}",
                "expected_output": f"Output for task {i+1}",
                "agent": agent_id
            }
        })
        
        # Create edge from agent to task
        edges.append({
            "id": f"edge{i+1}",
            "source": agent_id,
            "target": f"task{i+1}",
            "type": "assignment"
        })
    
    return {"nodes": nodes, "edges": edges} 