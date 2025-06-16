"""
Utilities for testing HTTP streaming responses in chat functionality.
Provides helper functions for parsing and validating streaming data.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncIterator
from unittest.mock import Mock, AsyncMock
import time


class StreamingTestClient:
    """Helper class for testing streaming HTTP responses."""
    
    def __init__(self, fastapi_client):
        self.client = fastapi_client
    
    async def post_streaming(self, url: str, json_data: Dict[str, Any], 
                           headers: Optional[Dict[str, str]] = None) -> 'StreamingTestResponse':
        """Send POST request and return streaming response handler."""
        response = self.client.post(url, json=json_data, headers=headers)
        return StreamingTestResponse(response)


class StreamingTestResponse:
    """Helper class for handling streaming test responses."""
    
    def __init__(self, response):
        self.response = response
        self.status_code = response.status_code
        self.headers = response.headers
        self.chunks = []
        self.parse_errors = []
        
    async def collect_chunks(self, timeout: float = 10.0) -> List[Dict[str, Any]]:
        """Collect all chunks from streaming response with timeout."""
        chunks = []
        start_time = time.time()
        
        try:
            # Simulate streaming response parsing
            content = self.response.content.decode('utf-8')
            lines = content.split('\n')
            
            for line in lines:
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Streaming timeout after {timeout}s")
                
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])  # Remove 'data: ' prefix
                        chunks.append(data)
                        
                        # Stop if done
                        if data.get('done'):
                            break
                            
                    except json.JSONDecodeError as e:
                        self.parse_errors.append(f"JSON parse error: {e}")
                        
        except Exception as e:
            self.parse_errors.append(f"Streaming error: {e}")
        
        self.chunks = chunks
        return chunks
    
    def get_full_content(self) -> str:
        """Get concatenated content from all chunks."""
        content = ""
        for chunk in self.chunks:
            if 'content' in chunk:
                content += chunk['content']
        return content
    
    def has_errors(self) -> bool:
        """Check if any errors occurred during streaming."""
        return len(self.parse_errors) > 0 or any('error' in chunk for chunk in self.chunks)
    
    def get_error_messages(self) -> List[str]:
        """Get all error messages from streaming response."""
        errors = self.parse_errors.copy()
        for chunk in self.chunks:
            if 'error' in chunk:
                errors.append(chunk['error'])
        return errors


class MockCrewAIService:
    """Mock CrewAI service for controlled testing."""
    
    def __init__(self, response_chunks: List[str], delay: float = 0.1, 
                 should_fail: bool = False, fail_at_chunk: int = -1):
        self.response_chunks = response_chunks
        self.delay = delay
        self.should_fail = should_fail
        self.fail_at_chunk = fail_at_chunk
        self.execution_count = 0
    
    async def execute_crew_stream(self, crew, execution_id: str, db_session) -> AsyncIterator[str]:
        """Mock crew execution that yields chunks."""
        self.execution_count += 1
        
        for i, chunk in enumerate(self.response_chunks):
            if self.should_fail and i == self.fail_at_chunk:
                raise Exception(f"Mock crew execution failed at chunk {i}")
            
            await asyncio.sleep(self.delay)
            yield chunk
    
    def get_execution_count(self) -> int:
        """Get number of times crew was executed."""
        return self.execution_count


class StreamingPerformanceMonitor:
    """Monitor performance metrics during streaming tests."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.chunk_times = []
        self.memory_usage = []
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.chunk_times = []
        self.memory_usage = []
    
    def record_chunk(self):
        """Record timestamp for received chunk."""
        if self.start_time:
            self.chunk_times.append(time.time() - self.start_time)
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.end_time = time.time()
    
    def get_total_time(self) -> float:
        """Get total execution time."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    def get_first_chunk_time(self) -> float:
        """Get time to first chunk."""
        return self.chunk_times[0] if self.chunk_times else 0.0
    
    def get_avg_chunk_interval(self) -> float:
        """Get average time between chunks."""
        if len(self.chunk_times) < 2:
            return 0.0
        
        intervals = []
        for i in range(1, len(self.chunk_times)):
            intervals.append(self.chunk_times[i] - self.chunk_times[i-1])
        
        return sum(intervals) / len(intervals)


def create_test_streaming_response(chunks: List[str], include_done: bool = True) -> str:
    """Create a mock streaming response content."""
    lines = []
    
    for chunk in chunks:
        data = json.dumps({'content': chunk})
        lines.append(f"data: {data}")
    
    if include_done:
        done_data = json.dumps({'done': True})
        lines.append(f"data: {done_data}")
    
    return '\n'.join(lines)


def create_error_streaming_response(error_message: str) -> str:
    """Create a mock streaming response with error."""
    data = json.dumps({'error': error_message, 'done': True})
    return f"data: {data}"


class ConcurrentStreamingTester:
    """Helper for testing concurrent streaming requests."""
    
    def __init__(self, client, endpoint: str):
        self.client = client
        self.endpoint = endpoint
        self.results = []
    
    async def run_concurrent_requests(self, requests: List[Dict[str, Any]], 
                                    headers: Dict[str, str], max_concurrent: int = 5):
        """Run multiple streaming requests concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = []
        
        async def make_request(request_data: Dict[str, Any]):
            async with semaphore:
                streaming_client = StreamingTestClient(self.client)
                response = await streaming_client.post_streaming(
                    self.endpoint, request_data, headers
                )
                chunks = await response.collect_chunks()
                return {
                    'request': request_data,
                    'response': response,
                    'chunks': chunks,
                    'success': not response.has_errors()
                }
        
        # Create tasks for all requests
        for request_data in requests:
            task = asyncio.create_task(make_request(request_data))
            tasks.append(task)
        
        # Wait for all tasks to complete
        self.results = await asyncio.gather(*tasks, return_exceptions=True)
        return self.results
    
    def get_success_rate(self) -> float:
        """Get percentage of successful concurrent requests."""
        if not self.results:
            return 0.0
        
        successful = sum(1 for result in self.results 
                        if isinstance(result, dict) and result.get('success'))
        
        return (successful / len(self.results)) * 100.0
    
    def get_average_response_time(self) -> float:
        """Get average response time for all requests."""
        if not self.results:
            return 0.0
        
        times = []
        for result in self.results:
            if isinstance(result, dict) and 'response' in result:
                # Would calculate actual response time in real implementation
                times.append(1.0)  # Placeholder
        
        return sum(times) / len(times) if times else 0.0


def validate_streaming_format(content: str) -> Dict[str, Any]:
    """Validate that content follows proper streaming format."""
    validation_result = {
        'valid': True,
        'errors': [],
        'chunk_count': 0,
        'has_done_marker': False
    }
    
    lines = content.split('\n')
    
    for line in lines:
        if line.startswith('data: '):
            try:
                data = json.loads(line[6:])
                validation_result['chunk_count'] += 1
                
                if data.get('done'):
                    validation_result['has_done_marker'] = True
                
                # Validate chunk structure
                if 'content' not in data and 'error' not in data and not data.get('done'):
                    validation_result['errors'].append(f"Invalid chunk structure: {data}")
                    validation_result['valid'] = False
                    
            except json.JSONDecodeError as e:
                validation_result['errors'].append(f"JSON decode error: {e}")
                validation_result['valid'] = False
    
    return validation_result


class DatabaseTransactionTester:
    """Helper for testing database transactions during streaming."""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.initial_counts = {}
        self.final_counts = {}
    
    def record_initial_state(self, models: List[Any]):
        """Record initial database state."""
        for model in models:
            count = self.db_session.query(model).count()
            self.initial_counts[model.__name__] = count
    
    def record_final_state(self, models: List[Any]):
        """Record final database state."""
        for model in models:
            count = self.db_session.query(model).count()
            self.final_counts[model.__name__] = count
    
    def get_changes(self) -> Dict[str, int]:
        """Get changes in record counts."""
        changes = {}
        for model_name in self.initial_counts:
            initial = self.initial_counts[model_name]
            final = self.final_counts.get(model_name, initial)
            changes[model_name] = final - initial
        return changes
    
    def assert_consistent_state(self, expected_changes: Dict[str, int]):
        """Assert that database changes match expectations."""
        actual_changes = self.get_changes()
        
        for model_name, expected_change in expected_changes.items():
            actual_change = actual_changes.get(model_name, 0)
            assert actual_change == expected_change, \
                f"Expected {expected_change} {model_name} records, got {actual_change}" 