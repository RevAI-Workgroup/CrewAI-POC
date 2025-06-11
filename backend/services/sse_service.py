"""
Server-Sent Events (SSE) service for real-time communication.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Set, Optional, Any, AsyncGenerator
from uuid import uuid4, UUID
from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse
import json

from schemas.sse_schemas import SSEEvent, HeartbeatEvent, ConnectionEvent, create_sse_event

logger = logging.getLogger(__name__)


class SSEConnectionManager:
    """Manages SSE connections and event broadcasting."""
    
    def __init__(self, heartbeat_interval: int = 30):
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.heartbeat_interval = heartbeat_interval
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    async def connect(self, request: Request, user_id: str) -> str:
        """Register a new SSE connection."""
        connection_id = str(uuid4())
        
        async with self._lock:
            # Store connection info
            self.connections[connection_id] = {
                "user_id": user_id,
                "connected_at": datetime.utcnow(),
                "last_heartbeat": datetime.utcnow(),
                "queue": asyncio.Queue(),
                "request": request
            }
            
            # Track user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        logger.info(f"SSE connection established: {connection_id} for user {user_id}")
        
        # Send connection event
        await self._send_to_connection(connection_id, ConnectionEvent(
            data=ConnectionEvent.Data(
                status="connected",
                message=f"Connected to SSE stream",
                client_id=connection_id
            )
        ))
        
        # Start heartbeat if not running
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect an SSE connection."""
        async with self._lock:
            if connection_id not in self.connections:
                return
            
            connection = self.connections[connection_id]
            user_id = connection["user_id"]
            
            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove connection
            del self.connections[connection_id]
        
        logger.info(f"SSE connection disconnected: {connection_id}")
    
    async def broadcast_to_user(self, user_id: str, event: SSEEvent):
        """Broadcast event to all connections for a specific user."""
        async with self._lock:
            if user_id not in self.user_connections:
                return
            
            connection_ids = list(self.user_connections[user_id])
        
        # Send to all user connections
        for connection_id in connection_ids:
            await self._send_to_connection(connection_id, event)
    
    async def broadcast_to_all(self, event: SSEEvent):
        """Broadcast event to all connected clients."""
        async with self._lock:
            connection_ids = list(self.connections.keys())
        
        # Send to all connections
        for connection_id in connection_ids:
            await self._send_to_connection(connection_id, event)
    
    async def broadcast_to_connections(self, connection_ids: Set[str], event: SSEEvent):
        """Broadcast event to specific connections."""
        for connection_id in connection_ids:
            await self._send_to_connection(connection_id, event)
    
    async def _send_to_connection(self, connection_id: str, event: SSEEvent):
        """Send event to a specific connection."""
        if connection_id not in self.connections:
            return
        
        try:
            queue = self.connections[connection_id]["queue"]
            await queue.put(event)
        except Exception as e:
            logger.error(f"Failed to send event to connection {connection_id}: {e}")
            await self.disconnect(connection_id)
    
    async def get_event_stream(self, connection_id: str) -> AsyncGenerator[str, None]:
        """Generate SSE event stream for a connection."""
        if connection_id not in self.connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        queue = self.connections[connection_id]["queue"]
        
        try:
            while True:
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield event.to_sse_format()
                except asyncio.TimeoutError:
                    # Send empty comment to keep connection alive
                    yield ": keepalive\n\n"
                except Exception as e:
                    logger.error(f"Error in event stream for {connection_id}: {e}")
                    break
        finally:
            await self.disconnect(connection_id)
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat to all connections."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Send heartbeat to all connections
                heartbeat_event = HeartbeatEvent(
                    data=HeartbeatEvent.Data()
                )
                
                await self.broadcast_to_all(heartbeat_event)
                
                # Cleanup stale connections
                await self._cleanup_stale_connections()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    async def _cleanup_stale_connections(self):
        """Remove stale connections that haven't responded to heartbeat."""
        stale_timeout = self.heartbeat_interval * 3  # 3 missed heartbeats
        now = datetime.utcnow()
        
        async with self._lock:
            stale_connections = []
            for connection_id, connection in self.connections.items():
                if (now - connection["last_heartbeat"]).total_seconds() > stale_timeout:
                    stale_connections.append(connection_id)
        
        for connection_id in stale_connections:
            logger.warning(f"Removing stale SSE connection: {connection_id}")
            await self.disconnect(connection_id)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.connections)
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of connections for a specific user."""
        return len(self.user_connections.get(user_id, set()))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self.connections),
            "unique_users": len(self.user_connections),
            "heartbeat_interval": self.heartbeat_interval,
            "user_stats": {
                user_id: len(connections) 
                for user_id, connections in self.user_connections.items()
            }
        }


# Global SSE manager instance
sse_manager = SSEConnectionManager()


class SSEService:
    """Service for SSE event management and broadcasting."""
    
    def __init__(self, manager: Optional[SSEConnectionManager] = None):
        self.manager = manager or sse_manager
    
    async def create_connection(self, request: Request, user_id: str) -> str:
        """Create a new SSE connection."""
        return await self.manager.connect(request, user_id)
    
    async def get_event_stream(self, connection_id: str) -> StreamingResponse:
        """Get SSE event stream for a connection."""
        return StreamingResponse(
            self.manager.get_event_stream(connection_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
    
    async def broadcast_execution_event(
        self,
        event_type: str,
        user_id: str,
        data: Dict[str, Any]
    ):
        """Broadcast execution-related event to user."""
        try:
            event = create_sse_event(event_type, data)
            await self.manager.broadcast_to_user(user_id, event)
            logger.debug(f"Broadcasted {event_type} event to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast {event_type} event: {e}")
    
    async def broadcast_system_event(
        self,
        event_type: str,
        data: Dict[str, Any]
    ):
        """Broadcast system-wide event to all users."""
        try:
            event = create_sse_event(event_type, data)
            await self.manager.broadcast_to_all(event)
            logger.debug(f"Broadcasted system {event_type} event")
        except Exception as e:
            logger.error(f"Failed to broadcast system {event_type} event: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get SSE connection statistics."""
        return self.manager.get_stats()


# Global SSE service instance
sse_service = SSEService() 