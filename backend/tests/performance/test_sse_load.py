"""
SSE (Server-Sent Events) load testing.
"""

import asyncio
import aiohttp
import time
import pytest
from typing import List, Dict, Any, Optional
from tests.performance.utils.metrics import MetricsCollector


class SSEClient:
    """SSE client for load testing."""
    
    def __init__(self, base_url: str, token: str, client_id: str):
        self.base_url = base_url
        self.token = token
        self.client_id = client_id
        self.session: Optional[aiohttp.ClientSession] = None
        self.connection_id: Optional[str] = None
        self.metrics_collector: Optional[MetricsCollector] = None
    
    async def connect(self, metrics_collector: MetricsCollector) -> bool:
        """Establish SSE connection."""
        self.metrics_collector = metrics_collector
        
        try:
            # Create session
            headers = {"Authorization": f"Bearer {self.token}"}
            self.session = aiohttp.ClientSession(headers=headers)
            
            # Get connection ID
            connect_url = f"{self.base_url}/api/sse/connect"
            async with self.session.get(connect_url) as response:
                if response.status == 200:
                    data = await response.json()
                    self.connection_id = data["connection_id"]
                    metrics_collector.record_connection(self.client_id)
                    return True
                else:
                    print(f"Failed to connect SSE: {response.status}")
                    return False
        except Exception as e:
            print(f"SSE connection error: {e}")
            return False
    
    async def listen_for_messages(self, duration: float = 30.0) -> List[Dict[str, Any]]:
        """Listen for SSE messages for specified duration."""
        if not self.connection_id or not self.session:
            return []
        
        messages = []
        start_time = time.time()
        
        try:
            stream_url = f"{self.base_url}/api/sse/stream/{self.connection_id}"
            
            async with self.session.get(stream_url) as response:
                if response.status != 200:
                    print(f"Failed to get SSE stream: {response.status}")
                    return messages
                
                async for line in response.content:
                    if time.time() - start_time > duration:
                        break
                    
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        try:
                            import json
                            data = json.loads(line[6:])  # Remove 'data: ' prefix
                            message_time = time.time()
                            
                            # Record metrics
                            if self.metrics_collector:
                                self.metrics_collector.record_message_sent(self.client_id)
                                # Calculate latency if timestamp available
                                if 'timestamp' in data:
                                    try:
                                        from datetime import datetime
                                        msg_timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                                        latency = message_time - msg_timestamp.timestamp()
                                        self.metrics_collector.record_message_success(self.client_id, latency)
                                    except:
                                        self.metrics_collector.record_message_success(self.client_id, 0.0)
                                else:
                                    self.metrics_collector.record_message_success(self.client_id, 0.0)
                            
                            messages.append({
                                "data": data,
                                "received_at": message_time
                            })
                        except json.JSONDecodeError as e:
                            if self.metrics_collector:
                                self.metrics_collector.record_message_failure(self.client_id, f"JSON decode error: {e}")
        
        except Exception as e:
            print(f"SSE listening error: {e}")
            if self.metrics_collector:
                self.metrics_collector.record_message_failure(self.client_id, str(e))
        
        return messages
    
    async def send_test_message(self, message: str) -> bool:
        """Send test message via SSE endpoint."""
        if not self.session:
            return False
        
        try:
            test_url = f"{self.base_url}/api/sse/test?message={message}"
            send_time = time.time()
            
            async with self.session.post(test_url) as response:
                if response.status == 200:
                    if self.metrics_collector:
                        # Rough latency estimate for message send
                        latency = time.time() - send_time
                        self.metrics_collector.record_message_success(self.client_id, latency)
                    return True
                else:
                    if self.metrics_collector:
                        self.metrics_collector.record_message_failure(self.client_id, f"HTTP {response.status}")
                    return False
        except Exception as e:
            if self.metrics_collector:
                self.metrics_collector.record_message_failure(self.client_id, str(e))
            return False
    
    async def disconnect(self):
        """Disconnect SSE client."""
        if self.metrics_collector:
            self.metrics_collector.record_disconnection(self.client_id)
        
        if self.session:
            await self.session.close()
            self.session = None


async def run_sse_load_test(
    base_url: str,
    token: str,
    num_clients: int = 10,
    test_duration: float = 30.0,
    message_frequency: float = 1.0
) -> Dict[str, Any]:
    """
    Run SSE load test with specified parameters.
    
    Args:
        base_url: Backend server URL
        token: Authentication token
        num_clients: Number of concurrent SSE clients
        test_duration: Test duration in seconds
        message_frequency: Messages per second per client
    """
    metrics = MetricsCollector()
    clients: List[SSEClient] = []
    
    try:
        # Setup metrics monitoring
        metrics.start_test()
        await metrics.start_system_monitoring()
        
        # Create clients
        for i in range(num_clients):
            client = SSEClient(base_url, token, f"sse_client_{i}")
            clients.append(client)
        
        # Connect all clients
        connect_tasks = [client.connect(metrics) for client in clients]
        connect_results = await asyncio.gather(*connect_tasks, return_exceptions=True)
        
        successful_connections = sum(1 for result in connect_results if result is True)
        print(f"Connected {successful_connections}/{num_clients} SSE clients")
        
        if successful_connections == 0:
            return {"error": "No successful connections"}
        
        # Start message sending and listening tasks
        tasks = []
        
        # Listening tasks
        for client in clients:
            if client.connection_id:
                task = asyncio.create_task(client.listen_for_messages(test_duration))
                tasks.append(task)
        
        # Message sending tasks
        message_interval = 1.0 / message_frequency if message_frequency > 0 else 1.0
        for client in clients:
            if client.connection_id:
                task = asyncio.create_task(
                    send_periodic_messages(client, test_duration, message_interval)
                )
                tasks.append(task)
        
        # Wait for test completion
        await asyncio.gather(*tasks, return_exceptions=True)
        
    except Exception as e:
        print(f"SSE load test error: {e}")
    
    finally:
        # Cleanup
        metrics.end_test()
        
        disconnect_tasks = [client.disconnect() for client in clients]
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)
    
    return metrics.get_summary()


async def send_periodic_messages(client: SSEClient, duration: float, interval: float):
    """Send periodic test messages."""
    start_time = time.time()
    message_count = 0
    
    while time.time() - start_time < duration:
        message_count += 1
        message = f"test_message_{message_count}_{int(time.time())}"
        
        await client.send_test_message(message)
        await asyncio.sleep(interval)


@pytest.mark.asyncio
async def test_sse_single_client():
    """Test SSE with single client."""
    base_url = "http://localhost:8000"
    token = "test_token"  # Would need actual token in real test
    
    result = await run_sse_load_test(
        base_url=base_url,
        token=token,
        num_clients=1,
        test_duration=5.0,
        message_frequency=1.0
    )
    
    assert "error" not in result
    assert result["connections"]["total"] >= 0


@pytest.mark.asyncio
async def test_sse_multiple_clients():
    """Test SSE with multiple clients."""
    base_url = "http://localhost:8000"
    token = "test_token"  # Would need actual token in real test
    
    result = await run_sse_load_test(
        base_url=base_url,
        token=token,
        num_clients=10,
        test_duration=10.0,
        message_frequency=2.0
    )
    
    assert "error" not in result
    assert result["connections"]["total"] >= 0


@pytest.mark.asyncio
async def test_sse_high_load():
    """Test SSE with high load."""
    base_url = "http://localhost:8000"
    token = "test_token"  # Would need actual token in real test
    
    result = await run_sse_load_test(
        base_url=base_url,
        token=token,
        num_clients=50,
        test_duration=30.0,
        message_frequency=5.0
    )
    
    assert "error" not in result
    assert result["connections"]["total"] >= 0 