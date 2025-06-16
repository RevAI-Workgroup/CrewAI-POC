"""
WebSocket load testing.
"""

import asyncio
import websockets
import json
import time
import pytest
from typing import List, Dict, Any, Optional
from tests.performance.utils.metrics import MetricsCollector


class WebSocketClient:
    """WebSocket client for load testing."""
    
    def __init__(self, base_url: str, token: str, client_id: str):
        self.base_url = base_url
        self.token = token
        self.client_id = client_id
        self.websocket = None
        self.metrics_collector: Optional[MetricsCollector] = None
    
    async def connect(self, metrics_collector: MetricsCollector) -> bool:
        """Establish WebSocket connection."""
        self.metrics_collector = metrics_collector
        
        try:
            # Convert HTTP URL to WebSocket URL
            ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
            ws_url = f"{ws_url}/api/ws/connect?token={self.token}"
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(ws_url)
            
            # Wait for connection confirmation
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if data.get("event") == "connected":
                metrics_collector.record_connection(self.client_id)
                return True
            else:
                print(f"Unexpected connection response: {data}")
                return False
                
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            return False
    
    async def listen_for_messages(self, duration: float = 30.0) -> List[Dict[str, Any]]:
        """Listen for WebSocket messages for specified duration."""
        if not self.websocket:
            return []
        
        messages = []
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    message_time = time.time()
                    
                    try:
                        data = json.loads(message)
                        
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
                
                except asyncio.TimeoutError:
                    # No message received within timeout - continue
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print(f"WebSocket connection closed for {self.client_id}")
                    break
        
        except Exception as e:
            print(f"WebSocket listening error: {e}")
            if self.metrics_collector:
                self.metrics_collector.record_message_failure(self.client_id, str(e))
        
        return messages
    
    async def send_test_message(self, message: str) -> bool:
        """Send test message via WebSocket."""
        if not self.websocket:
            return False
        
        try:
            send_time = time.time()
            
            # Send test message
            test_data = {
                "type": "test",
                "message": message,
                "timestamp": send_time
            }
            
            await self.websocket.send(json.dumps(test_data))
            
            if self.metrics_collector:
                # Rough latency estimate for message send
                latency = time.time() - send_time
                self.metrics_collector.record_message_success(self.client_id, latency)
            
            return True
            
        except Exception as e:
            if self.metrics_collector:
                self.metrics_collector.record_message_failure(self.client_id, str(e))
            return False
    
    async def send_ping(self) -> bool:
        """Send ping message to keep connection alive."""
        if not self.websocket:
            return False
        
        try:
            ping_data = {"type": "ping"}
            await self.websocket.send(json.dumps(ping_data))
            return True
        except Exception as e:
            print(f"Ping error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect WebSocket client."""
        if self.metrics_collector:
            self.metrics_collector.record_disconnection(self.client_id)
        
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            self.websocket = None


async def run_websocket_load_test(
    base_url: str,
    token: str,
    num_clients: int = 10,
    test_duration: float = 30.0,
    message_frequency: float = 1.0
) -> Dict[str, Any]:
    """
    Run WebSocket load test with specified parameters.
    
    Args:
        base_url: Backend server URL
        token: Authentication token
        num_clients: Number of concurrent WebSocket clients
        test_duration: Test duration in seconds
        message_frequency: Messages per second per client
    """
    metrics = MetricsCollector()
    clients: List[WebSocketClient] = []
    
    try:
        # Setup metrics monitoring
        metrics.start_test()
        await metrics.start_system_monitoring()
        
        # Create clients
        for i in range(num_clients):
            client = WebSocketClient(base_url, token, f"ws_client_{i}")
            clients.append(client)
        
        # Connect all clients
        connect_tasks = [client.connect(metrics) for client in clients]
        connect_results = await asyncio.gather(*connect_tasks, return_exceptions=True)
        
        successful_connections = sum(1 for result in connect_results if result is True)
        print(f"Connected {successful_connections}/{num_clients} WebSocket clients")
        
        if successful_connections == 0:
            return {"error": "No successful connections"}
        
        # Start message sending and listening tasks
        tasks = []
        
        # Listening tasks
        for client in clients:
            if client.websocket:
                task = asyncio.create_task(client.listen_for_messages(test_duration))
                tasks.append(task)
        
        # Message sending tasks
        message_interval = 1.0 / message_frequency if message_frequency > 0 else 1.0
        for client in clients:
            if client.websocket:
                task = asyncio.create_task(
                    send_periodic_ws_messages(client, test_duration, message_interval)
                )
                tasks.append(task)
        
        # Ping tasks (keep connections alive)
        for client in clients:
            if client.websocket:
                task = asyncio.create_task(
                    send_periodic_pings(client, test_duration)
                )
                tasks.append(task)
        
        # Wait for test completion
        await asyncio.gather(*tasks, return_exceptions=True)
        
    except Exception as e:
        print(f"WebSocket load test error: {e}")
    
    finally:
        # Cleanup
        metrics.end_test()
        
        disconnect_tasks = [client.disconnect() for client in clients]
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)
    
    return metrics.get_summary()


async def send_periodic_ws_messages(client: WebSocketClient, duration: float, interval: float):
    """Send periodic test messages via WebSocket."""
    start_time = time.time()
    message_count = 0
    
    while time.time() - start_time < duration:
        message_count += 1
        message = f"ws_test_message_{message_count}_{int(time.time())}"
        
        await client.send_test_message(message)
        await asyncio.sleep(interval)


async def send_periodic_pings(client: WebSocketClient, duration: float):
    """Send periodic ping messages to keep connection alive."""
    start_time = time.time()
    
    while time.time() - start_time < duration:
        await client.send_ping()
        await asyncio.sleep(10.0)  # Ping every 10 seconds


# SSE comparison function removed - SSE infrastructure disabled for chat implementation


@pytest.mark.asyncio
async def test_websocket_single_client():
    """Test WebSocket with single client."""
    base_url = "http://localhost:8000"
    token = "test_token"  # Would need actual token in real test
    
    result = await run_websocket_load_test(
        base_url=base_url,
        token=token,
        num_clients=1,
        test_duration=5.0,
        message_frequency=1.0
    )
    
    assert "error" not in result
    assert result["connections"]["total"] >= 0


@pytest.mark.asyncio
async def test_websocket_multiple_clients():
    """Test WebSocket with multiple clients."""
    base_url = "http://localhost:8000"
    token = "test_token"  # Would need actual token in real test
    
    result = await run_websocket_load_test(
        base_url=base_url,
        token=token,
        num_clients=10,
        test_duration=10.0,
        message_frequency=2.0
    )
    
    assert "error" not in result
    assert result["connections"]["total"] >= 0


@pytest.mark.asyncio
async def test_websocket_high_load():
    """Test WebSocket with high load."""
    base_url = "http://localhost:8000"
    token = "test_token"  # Would need actual token in real test
    
    result = await run_websocket_load_test(
        base_url=base_url,
        token=token,
        num_clients=50,
        test_duration=30.0,
        message_frequency=5.0
    )
    
    assert "error" not in result
    assert result["connections"]["total"] >= 0


# SSE comparison test removed - SSE infrastructure disabled for chat implementation 