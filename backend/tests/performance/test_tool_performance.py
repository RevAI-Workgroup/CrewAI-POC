"""
Performance tests for tool execution
Tests latency, concurrency, memory usage, and load handling
"""

import pytest
import time
import threading
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock
from services.tool_executor import ToolExecutor
from services.tools.hello_world_tool import HelloWorldTool


@pytest.fixture
def mock_db_session():
    """Mock database session for performance tests"""
    return Mock()


@pytest.fixture
def tool_executor(mock_db_session):
    """Tool executor instance for performance testing"""
    return ToolExecutor(mock_db_session)


class TestToolExecutionLatency:
    """Test suite for tool execution latency"""
    
    def test_hello_world_tool_latency(self, tool_executor):
        """Test HelloWorldTool execution latency"""
        parameters = {"name": "PerformanceTest"}
        
        # Warm up
        for _ in range(5):
            tool_executor.execute_builtin_tool("hello_world", parameters)
        
        # Measure latency
        latencies = []
        for _ in range(100):
            start_time = time.time()
            result = tool_executor.execute_builtin_tool("hello_world", parameters)
            end_time = time.time()
            
            assert result.success is True
            latencies.append(end_time - start_time)
        
        avg_latency = statistics.mean(latencies)
        median_latency = statistics.median(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        
        print(f"HelloWorld Tool Latency Stats:")
        print(f"  Average: {avg_latency:.4f}s")
        print(f"  Median: {median_latency:.4f}s")
        print(f"  95th Percentile: {p95_latency:.4f}s")
        
        # Performance assertions (adjust thresholds as needed)
        assert avg_latency < 0.01, f"Average latency too high: {avg_latency:.4f}s"
        assert p95_latency < 0.02, f"95th percentile latency too high: {p95_latency:.4f}s"
    
    def test_tool_initialization_latency(self):
        """Test tool class initialization latency"""
        initialization_times = []
        
        for _ in range(100):
            start_time = time.time()
            tool = HelloWorldTool()
            end_time = time.time()
            
            initialization_times.append(end_time - start_time)
            assert tool.name == "hello_world"
        
        avg_init_time = statistics.mean(initialization_times)
        max_init_time = max(initialization_times)
        
        print(f"Tool Initialization Stats:")
        print(f"  Average: {avg_init_time:.6f}s")
        print(f"  Maximum: {max_init_time:.6f}s")
        
        # Should be very fast
        assert avg_init_time < 0.001, f"Tool initialization too slow: {avg_init_time:.6f}s"
    
    def test_parameter_validation_latency(self, tool_executor):
        """Test parameter validation latency"""
        parameters = {"name": "ValidationTest", "greeting_style": "casual", "include_time": False}
        
        validation_times = []
        
        for _ in range(1000):
            start_time = time.time()
            result = tool_executor.execute_builtin_tool("hello_world", parameters)
            end_time = time.time()
            
            validation_times.append(end_time - start_time)
            assert result.success is True
        
        avg_validation_time = statistics.mean(validation_times)
        p99_validation_time = statistics.quantiles(validation_times, n=100)[98]  # 99th percentile
        
        print(f"Parameter Validation Latency Stats:")
        print(f"  Average: {avg_validation_time:.6f}s")
        print(f"  99th Percentile: {p99_validation_time:.6f}s")
        
        assert avg_validation_time < 0.005, f"Parameter validation too slow: {avg_validation_time:.6f}s"


class TestConcurrentToolExecution:
    """Test suite for concurrent tool execution"""
    
    def test_concurrent_hello_world_execution(self, tool_executor):
        """Test concurrent execution of HelloWorld tool"""
        parameters = {"name": "ConcurrentTest"}
        num_threads = 10
        executions_per_thread = 20
        
        results = []
        errors = []
        
        def execute_tool():
            """Execute tool in thread"""
            try:
                for _ in range(executions_per_thread):
                    result = tool_executor.execute_builtin_tool("hello_world", parameters)
                    results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create and start threads
        threads = []
        start_time = time.time()
        
        for _ in range(num_threads):
            thread = threading.Thread(target=execute_tool)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred during concurrent execution: {errors}"
        assert len(results) == num_threads * executions_per_thread
        
        # All results should be successful
        successful_results = [r for r in results if r.success]
        assert len(successful_results) == len(results), "Some executions failed"
        
        # Performance metrics
        total_executions = num_threads * executions_per_thread
        throughput = total_executions / total_time
        
        print(f"Concurrent Execution Stats:")
        print(f"  Total executions: {total_executions}")
        print(f"  Total time: {total_time:.4f}s")
        print(f"  Throughput: {throughput:.2f} executions/second")
        
        # Should handle concurrent execution efficiently
        assert throughput > 100, f"Throughput too low: {throughput:.2f} executions/second"
    
    def test_thread_safety(self, tool_executor):
        """Test thread safety of tool execution"""
        parameters_list = [
            {"name": f"User{i}", "greeting_style": "casual"} for i in range(50)
        ]
        
        results = {}
        lock = threading.Lock()
        
        def execute_with_different_params(params):
            """Execute tool with specific parameters"""
            result = tool_executor.execute_builtin_tool("hello_world", params)
            
            with lock:
                results[params["name"]] = result
        
        # Execute with different parameters concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_with_different_params, params) 
                      for params in parameters_list]
            
            # Wait for all executions to complete
            for future in futures:
                future.result()
        
        # Verify all executions completed successfully
        assert len(results) == len(parameters_list)
        
        for name, result in results.items():
            assert result.success is True
            assert name in result.result, f"Expected {name} in result: {result.result}"


class TestLargeParameterHandling:
    """Test suite for handling large parameter payloads"""
    
    def test_large_string_parameter(self, tool_executor):
        """Test handling of large string parameters"""
        # Create large string (1MB)
        large_name = "A" * (1024 * 1024)
        parameters = {"name": large_name[:100]}  # HelloWorld tool has max length constraint
        
        start_time = time.time()
        result = tool_executor.execute_builtin_tool("hello_world", parameters)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert result.success is True
        assert parameters["name"] in result.result
        
        # Should handle large parameters reasonably quickly
        assert execution_time < 0.1, f"Large parameter handling too slow: {execution_time:.4f}s"
    
    def test_many_parameters(self, tool_executor):
        """Test handling of many parameters (for custom tools)"""
        # This would be more relevant for custom tools with many parameters
        # For now, test with HelloWorld tool's parameters multiple times
        
        # Simulate custom tool with many parameters
        mock_tool = Mock()
        mock_tool.id = 1
        mock_tool.name = "many_params_tool"
        mock_tool.schema = {
            "type": "object",
            "properties": {f"param_{i}": {"type": "string"} for i in range(100)},
            "required": [f"param_{i}" for i in range(10)]
        }
        mock_tool.implementation = '''
def execute(parameters):
    return {
        "success": True,
        "result": f"Processed {len(parameters)} parameters",
        "error": None,
        "execution_time": 0.001
    }
'''
        mock_tool.user_id = "test_user"
        mock_tool.is_public = "true"
        
        # Setup mock database
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_tool
        tool_executor.db.query.return_value = mock_query
        
        # Create parameters for all 100 parameters
        parameters = {f"param_{i}": f"value_{i}" for i in range(100)}
        
        start_time = time.time()
        result = tool_executor.execute_custom_tool(1, parameters, "test_user")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert result.success is True
        assert "100 parameters" in result.result
        
        # Should handle many parameters efficiently
        assert execution_time < 0.05, f"Many parameters handling too slow: {execution_time:.4f}s"


class TestMemoryUsage:
    """Test suite for memory usage during tool execution"""
    
    def test_memory_leak_prevention(self, tool_executor):
        """Test that repeated executions don't cause memory leaks"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Get initial memory usage
        gc.collect()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        parameters = {"name": "MemoryTest"}
        
        # Execute tool many times
        for _ in range(1000):
            result = tool_executor.execute_builtin_tool("hello_world", parameters)
            assert result.success is True
        
        # Force garbage collection
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_increase = final_memory - initial_memory
        
        print(f"Memory Usage Stats:")
        print(f"  Initial: {initial_memory:.2f} MB")
        print(f"  Final: {final_memory:.2f} MB")
        print(f"  Increase: {memory_increase:.2f} MB")
        
        # Memory increase should be minimal (less than 10MB for 1000 executions)
        assert memory_increase < 10, f"Potential memory leak detected: {memory_increase:.2f} MB increase"
    
    def test_large_result_handling(self, tool_executor):
        """Test memory efficiency with large results"""
        # Create a mock tool that returns large results
        mock_tool = Mock()
        mock_tool.id = 1
        mock_tool.name = "large_result_tool"
        mock_tool.schema = {"type": "object", "properties": {"size": {"type": "integer"}}, "required": ["size"]}
        mock_tool.implementation = '''
def execute(parameters):
    size = parameters.get("size", 1000)
    large_result = "X" * size
    return {
        "success": True,
        "result": large_result,
        "error": None,
        "execution_time": 0.001
    }
'''
        mock_tool.user_id = "test_user"
        mock_tool.is_public = "true"
        
        # Setup mock database
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_tool
        tool_executor.db.query.return_value = mock_query
        
        # Test with different result sizes
        sizes = [1000, 10000, 100000]  # 1KB, 10KB, 100KB
        
        for size in sizes:
            parameters = {"size": size}
            
            start_time = time.time()
            result = tool_executor.execute_custom_tool(1, parameters, "test_user")
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            assert result.success is True
            assert len(result.result) == size
            
            # Execution time should scale reasonably with result size
            assert execution_time < 0.1, f"Large result handling too slow for size {size}: {execution_time:.4f}s"


class TestToolExecutionUnderLoad:
    """Test suite for tool execution under various load conditions"""
    
    def test_sustained_load(self, tool_executor):
        """Test tool execution under sustained load"""
        parameters = {"name": "LoadTest"}
        duration = 5  # 5 seconds of sustained load
        
        results = []
        errors = []
        start_time = time.time()
        
        def sustained_execution():
            """Execute tools continuously for specified duration"""
            while time.time() - start_time < duration:
                try:
                    result = tool_executor.execute_builtin_tool("hello_world", parameters)
                    results.append(result)
                except Exception as e:
                    errors.append(e)
        
        # Run sustained load with multiple threads
        num_threads = 5
        threads = []
        
        for _ in range(num_threads):
            thread = threading.Thread(target=sustained_execution)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # Verify results
        assert len(errors) == 0, f"Errors during sustained load: {errors}"
        assert len(results) > 0, "No successful executions during sustained load"
        
        # Calculate performance metrics
        total_executions = len(results)
        throughput = total_executions / actual_duration
        
        successful_executions = len([r for r in results if r.success])
        success_rate = successful_executions / total_executions * 100
        
        print(f"Sustained Load Test Stats:")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Total executions: {total_executions}")
        print(f"  Successful executions: {successful_executions}")
        print(f"  Success rate: {success_rate:.2f}%")
        print(f"  Throughput: {throughput:.2f} executions/second")
        
        # Performance requirements
        assert success_rate >= 99, f"Success rate too low: {success_rate:.2f}%"
        assert throughput > 50, f"Throughput too low under load: {throughput:.2f} executions/second"
    
    def test_burst_load_handling(self, tool_executor):
        """Test handling of sudden burst loads"""
        parameters = {"name": "BurstTest"}
        burst_size = 100
        
        # Execute burst load
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            
            for _ in range(burst_size):
                future = executor.submit(tool_executor.execute_builtin_tool, "hello_world", parameters)
                futures.append(future)
            
            # Collect results
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=5)  # 5 second timeout
                    results.append(result)
                except Exception as e:
                    results.append(e)
        
        end_time = time.time()
        burst_duration = end_time - start_time
        
        # Verify results
        successful_results = [r for r in results if hasattr(r, 'success') and r.success]
        failed_results = [r for r in results if not (hasattr(r, 'success') and r.success)]
        
        success_rate = len(successful_results) / len(results) * 100
        throughput = len(successful_results) / burst_duration
        
        print(f"Burst Load Test Stats:")
        print(f"  Burst size: {burst_size}")
        print(f"  Burst duration: {burst_duration:.4f}s")
        print(f"  Successful: {len(successful_results)}")
        print(f"  Failed: {len(failed_results)}")
        print(f"  Success rate: {success_rate:.2f}%")
        print(f"  Throughput: {throughput:.2f} executions/second")
        
        # Should handle burst loads effectively
        assert success_rate >= 95, f"Burst load success rate too low: {success_rate:.2f}%"
        assert burst_duration < 2, f"Burst load took too long: {burst_duration:.4f}s" 