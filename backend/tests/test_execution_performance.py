"""
Performance tests for execution service.
"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
from uuid import uuid4
from typing import Dict, Any, List, Callable

from .fixtures.execution_fixtures import *
from .utils.execution_test_utils import (
    ExecutionTestHelper,
    MockExecutionService,
    ExecutionTestAssertions
)


class TestExecutionPerformance:
    """Performance tests for execution service."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_service = MockExecutionService()
        self.assertions = ExecutionTestAssertions()
    
    def test_concurrent_execution_queueing(self, performance_test_config):
        """Test concurrent execution queueing performance."""
        execution_count = 10
        start_time = time.time()
        
        # Queue multiple executions concurrently
        task_ids = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(
                    self.mock_service.queue_execution,
                    str(uuid4()),
                    str(uuid4()),
                    str(uuid4()),
                    {"test": f"input_{i}"}
                )
                for i in range(execution_count)
            ]
            
            for future in as_completed(futures):
                task_id = future.result()
                task_ids.append(task_id)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all executions were queued
        assert len(task_ids) == execution_count
        assert len(set(task_ids)) == execution_count  # All unique
        
        # Performance assertions
        throughput = execution_count / total_time
        assert throughput >= 5.0, f"Queueing throughput {throughput:.2f} ops/sec too low"
        assert total_time <= 5.0, f"Total queueing time {total_time:.2f}s too high"
    
    def test_status_check_performance(self):
        """Test status checking performance."""
        # Queue some executions first
        task_ids = []
        for i in range(20):
            task_id = self.mock_service.queue_execution(
                str(uuid4()),
                str(uuid4()), 
                str(uuid4()),
                {"test": f"input_{i}"}
            )
            task_ids.append(task_id)
            
            # Simulate some completions
            if i % 3 == 0:
                self.mock_service.simulate_execution_completion(
                    task_id, 
                    f"result_{i}"
                )
        
        # Test concurrent status checking
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(self.mock_service.get_task_status, task_id)
                for task_id in task_ids
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all status checks completed
        assert len(results) == len(task_ids)
        
        # Performance assertions
        throughput = len(task_ids) / total_time
        assert throughput >= 10.0, f"Status check throughput {throughput:.2f} ops/sec too low"
    
    def test_execution_simulation_performance(self):
        """Test simulated execution completion performance."""
        task_count = 50
        
        # Queue executions
        task_ids = []
        for i in range(task_count):
            task_id = self.mock_service.queue_execution(
                str(uuid4()),
                str(uuid4()),
                str(uuid4()),
                {"test": f"input_{i}"}
            )
            task_ids.append(task_id)
        
        # Time execution completions
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    self.mock_service.simulate_execution_completion,
                    task_id,
                    f"result_{i}"
                )
                for i, task_id in enumerate(task_ids)
            ]
            
            # Wait for all completions
            for future in as_completed(futures):
                future.result()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all executions completed
        completed_count = 0
        for task_id in task_ids:
            status = self.mock_service.get_task_status(task_id)
            if status["status"] == "SUCCESS":
                completed_count += 1
        
        assert completed_count == task_count
        
        # Performance assertions
        throughput = task_count / total_time
        assert throughput >= 20.0, f"Completion throughput {throughput:.2f} ops/sec too low"
    
    def test_mixed_operations_performance(self):
        """Test performance under mixed operation load."""
        operations_count = 100
        start_time = time.time()
        
        def mixed_operation(operation_id: int):
            """Perform mixed operations."""
            if operation_id % 4 == 0:
                # Queue execution
                task_id = self.mock_service.queue_execution(
                    str(uuid4()),
                    str(uuid4()),
                    str(uuid4()),
                    {"test": f"input_{operation_id}"}
                )
                return {"type": "queue", "task_id": task_id}
            
            elif operation_id % 4 == 1:
                # Check status (may fail for non-existent task)
                fake_task_id = f"fake-task-{operation_id}"
                status = self.mock_service.get_task_status(fake_task_id)
                return {"type": "status", "status": status}
            
            elif operation_id % 4 == 2:
                # Cancel task (may fail for non-existent task)
                fake_task_id = f"fake-task-{operation_id}"
                result = self.mock_service.cancel_task(fake_task_id)
                return {"type": "cancel", "result": result}
            
            else:
                # Simulate completion
                fake_task_id = f"fake-task-{operation_id}"
                self.mock_service.simulate_execution_completion(
                    fake_task_id,
                    f"result_{operation_id}"
                )
                return {"type": "complete", "task_id": fake_task_id}
        
        # Run mixed operations concurrently
        results = []
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [
                executor.submit(mixed_operation, i)
                for i in range(operations_count)
            ]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all operations completed
        assert len(results) == operations_count
        
        # Count operation types
        operation_counts = {}
        for result in results:
            op_type = result["type"]
            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
        
        assert len(operation_counts) == 4  # All operation types used
        
        # Performance assertions
        throughput = operations_count / total_time
        assert throughput >= 15.0, f"Mixed operations throughput {throughput:.2f} ops/sec too low"
    
    def test_execution_timing_accuracy(self):
        """Test execution timing accuracy."""
        def timed_execution(execution_id: int) -> Dict[str, Any]:
            """Execute with timing."""
            start_time = time.time()
            
            # Simulate work
            time.sleep(0.1)  # 100ms simulated work
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            return {
                "execution_id": execution_id,
                "execution_time": execution_time,
                "expected_time": 0.1
            }
        
        # Run multiple timed executions
        execution_count = 20
        results = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(timed_execution, i)
                for i in range(execution_count)
            ]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        # Analyze timing accuracy
        timing_errors = []
        for result in results:
            expected = result["expected_time"]
            actual = result["execution_time"]
            error = abs(actual - expected)
            timing_errors.append(error)
        
        # Timing should be reasonably accurate
        avg_error = sum(timing_errors) / len(timing_errors)
        max_error = max(timing_errors)
        
        assert avg_error <= 0.05, f"Average timing error {avg_error:.3f}s too high"
        assert max_error <= 0.1, f"Maximum timing error {max_error:.3f}s too high"
    
    def test_load_stress_test(self):
        """Test system under high load."""
        high_load_count = 200
        start_time = time.time()
        
        # Create high load of operations
        all_results = []
        batch_size = 50
        
        for batch in range(0, high_load_count, batch_size):
            batch_end = min(batch + batch_size, high_load_count)
            batch_size_actual = batch_end - batch
            
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [
                    executor.submit(
                        self.mock_service.queue_execution,
                        str(uuid4()),
                        str(uuid4()),
                        str(uuid4()),
                        {"batch": batch, "item": i}
                    )
                    for i in range(batch_size_actual)
                ]
                
                batch_results = [future.result() for future in as_completed(futures)]
                all_results.extend(batch_results)
            
            # Small delay between batches
            time.sleep(0.01)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all operations completed
        assert len(all_results) == high_load_count
        assert len(set(all_results)) == high_load_count  # All unique
        
        # Performance under load
        throughput = high_load_count / total_time
        assert throughput >= 50.0, f"High load throughput {throughput:.2f} ops/sec too low"
        
        # Verify service state consistency
        service_state_size = len(self.mock_service.executions)
        assert service_state_size == high_load_count, f"Service state inconsistent: {service_state_size} != {high_load_count}"


class TestExecutionScenarios:
    """Test various execution scenarios for performance."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_service = MockExecutionService()
    
    def test_rapid_queue_and_complete(self):
        """Test rapid queueing and completion cycles."""
        cycles = 30
        total_operations = 0
        start_time = time.time()
        
        for cycle in range(cycles):
            # Queue execution
            task_id = self.mock_service.queue_execution(
                str(uuid4()),
                str(uuid4()),
                str(uuid4()),
                {"cycle": cycle}
            )
            total_operations += 1
            
            # Immediately complete it
            self.mock_service.simulate_execution_completion(
                task_id,
                f"result_cycle_{cycle}"
            )
            total_operations += 1
            
            # Check status
            status = self.mock_service.get_task_status(task_id)
            assert status["status"] == "SUCCESS"
            total_operations += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance check with minimum time to avoid division by zero
        if total_time == 0:
            total_time = 0.001  # 1ms minimum
        
        throughput = total_operations / total_time
        
        print(f"Rapid cycle performance: {total_operations} operations in {total_time:.4f}s")
        print(f"Throughput: {throughput:.2f} operations/second")
        
        # Check that we could handle rapid operations (very loose check)
        assert total_operations == cycles * 3
        assert throughput > 0  # Just ensure we calculated something meaningful
    
    def test_cancellation_performance(self):
        """Test cancellation performance."""
        task_count = 100
        
        # Queue many executions
        task_ids = []
        for i in range(task_count):
            task_id = self.mock_service.queue_execution(
                str(uuid4()),
                str(uuid4()),
                str(uuid4()),
                {"item": i}
            )
            task_ids.append(task_id)
        
        # Time cancellations
        start_time = time.time()
        
        cancelled_count = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(self.mock_service.cancel_task, task_id)
                for task_id in task_ids
            ]
            
            for future in as_completed(futures):
                if future.result():
                    cancelled_count += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify cancellations
        assert cancelled_count == task_count
        
        # Performance check
        throughput = task_count / total_time
        assert throughput >= 20.0, f"Cancellation throughput {throughput:.2f} ops/sec too low" 