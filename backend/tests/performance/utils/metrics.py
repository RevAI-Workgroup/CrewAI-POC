"""
Metrics collection utilities for performance testing.
"""

import time
import psutil
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ConnectionMetrics:
    """Metrics for a single connection."""
    connection_id: str
    connect_time: float
    total_messages: int = 0
    successful_messages: int = 0
    failed_messages: int = 0
    latencies: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    disconnect_time: Optional[float] = None
    
    @property
    def connection_duration(self) -> Optional[float]:
        """Calculate connection duration."""
        if self.disconnect_time is not None:
            return self.disconnect_time - self.connect_time
        return None
    
    @property
    def average_latency(self) -> float:
        """Calculate average message latency."""
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate message success rate."""
        return (self.successful_messages / self.total_messages) if self.total_messages > 0 else 0.0


@dataclass
class SystemMetrics:
    """System resource metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    network_bytes_sent: int
    network_bytes_recv: int


class MetricsCollector:
    """Collects and aggregates performance metrics."""
    
    def __init__(self):
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        self.system_metrics: List[SystemMetrics] = []
        self.test_start_time: Optional[float] = None
        self.test_end_time: Optional[float] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._stop_monitoring = False
    
    def start_test(self):
        """Mark test start time."""
        self.test_start_time = time.time()
        self._stop_monitoring = False
    
    def end_test(self):
        """Mark test end time."""
        self.test_end_time = time.time()
        self._stop_monitoring = True
        if self._monitoring_task:
            self._monitoring_task.cancel()
    
    def record_connection(self, connection_id: str) -> ConnectionMetrics:
        """Record a new connection."""
        metrics = ConnectionMetrics(
            connection_id=connection_id,
            connect_time=time.time()
        )
        self.connection_metrics[connection_id] = metrics
        return metrics
    
    def record_disconnection(self, connection_id: str):
        """Record connection disconnection."""
        if connection_id in self.connection_metrics:
            self.connection_metrics[connection_id].disconnect_time = time.time()
    
    def record_message_sent(self, connection_id: str):
        """Record a message being sent."""
        if connection_id in self.connection_metrics:
            self.connection_metrics[connection_id].total_messages += 1
    
    def record_message_success(self, connection_id: str, latency: float):
        """Record successful message with latency."""
        if connection_id in self.connection_metrics:
            metrics = self.connection_metrics[connection_id]
            metrics.successful_messages += 1
            metrics.latencies.append(latency)
    
    def record_message_failure(self, connection_id: str, error: str):
        """Record failed message."""
        if connection_id in self.connection_metrics:
            metrics = self.connection_metrics[connection_id]
            metrics.failed_messages += 1
            metrics.errors.append(error)
    
    async def start_system_monitoring(self, interval: float = 1.0):
        """Start monitoring system metrics."""
        self._monitoring_task = asyncio.create_task(self._monitor_system(interval))
    
    async def _monitor_system(self, interval: float):
        """Monitor system metrics continuously."""
        process = psutil.Process()
        
        while not self._stop_monitoring:
            try:
                # Get network stats
                net_io = psutil.net_io_counters()
                
                # Record metrics
                metrics = SystemMetrics(
                    timestamp=datetime.utcnow(),
                    cpu_percent=process.cpu_percent(),
                    memory_mb=process.memory_info().rss / 1024 / 1024,
                    memory_percent=process.memory_percent(),
                    network_bytes_sent=net_io.bytes_sent,
                    network_bytes_recv=net_io.bytes_recv
                )
                
                self.system_metrics.append(metrics)
                
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error collecting system metrics: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance test summary."""
        if not self.connection_metrics:
            return {"error": "No metrics collected"}
        
        # Connection statistics
        total_connections = len(self.connection_metrics)
        successful_connections = sum(
            1 for m in self.connection_metrics.values() 
            if m.disconnect_time is not None
        )
        
        # Message statistics
        total_messages = sum(m.total_messages for m in self.connection_metrics.values())
        successful_messages = sum(m.successful_messages for m in self.connection_metrics.values())
        failed_messages = sum(m.failed_messages for m in self.connection_metrics.values())
        
        # Latency statistics
        all_latencies = []
        for metrics in self.connection_metrics.values():
            all_latencies.extend(metrics.latencies)
        
        latency_stats = {}
        if all_latencies:
            all_latencies.sort()
            latency_stats = {
                "min": min(all_latencies),
                "max": max(all_latencies),
                "avg": sum(all_latencies) / len(all_latencies),
                "p50": all_latencies[len(all_latencies) // 2],
                "p95": all_latencies[int(len(all_latencies) * 0.95)],
                "p99": all_latencies[int(len(all_latencies) * 0.99)]
            }
        
        # Test duration
        test_duration = None
        if self.test_start_time and self.test_end_time:
            test_duration = self.test_end_time - self.test_start_time
        
        # System resource stats
        system_stats = {}
        if self.system_metrics:
            cpu_values = [m.cpu_percent for m in self.system_metrics]
            memory_values = [m.memory_mb for m in self.system_metrics]
            
            system_stats = {
                "avg_cpu_percent": sum(cpu_values) / len(cpu_values),
                "max_cpu_percent": max(cpu_values),
                "avg_memory_mb": sum(memory_values) / len(memory_values),
                "max_memory_mb": max(memory_values),
                "sample_count": len(self.system_metrics)
            }
        
        return {
            "test_duration": test_duration,
            "connections": {
                "total": total_connections,
                "successful": successful_connections,
                "success_rate": successful_connections / total_connections if total_connections > 0 else 0
            },
            "messages": {
                "total": total_messages,
                "successful": successful_messages,
                "failed": failed_messages,
                "success_rate": successful_messages / total_messages if total_messages > 0 else 0,
                "throughput": total_messages / test_duration if test_duration and test_duration > 0 else 0
            },
            "latency": latency_stats,
            "system": system_stats
        } 