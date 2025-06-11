"""
WebSocket service for managing real-time WebSocket connections.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import WebSocket

import logging
logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections with user association.
    """
    
    def __init__(self):
        # Store active connections: connection_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Map users to their connections: user_id -> List[connection_id]
        self.user_connections: Dict[str, list] = {}
        # Store connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """
        Register a new WebSocket connection for a user.
        Returns connection ID.
        """
        connection_id = str(uuid.uuid4())
        
        # Store connection
        self.active_connections[connection_id] = websocket
        
        # Associate with user
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
        
        # Store metadata
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "last_ping": datetime.utcnow().isoformat()
        }
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """
        Disconnect and clean up a WebSocket connection.
        """
        if connection_id in self.active_connections:
            # Get user ID for cleanup
            user_id = self.connection_metadata.get(connection_id, {}).get("user_id")
            
            # Remove from active connections
            websocket = self.active_connections.pop(connection_id)
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                if connection_id in self.user_connections[user_id]:
                    self.user_connections[user_id].remove(connection_id)
                # Clean up empty user lists
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove metadata
            self.connection_metadata.pop(connection_id, None)
            
            logger.info(f"WebSocket disconnected: {connection_id}")
            
            # Close the WebSocket if still open
            try:
                await websocket.close()
            except:
                pass
    
    async def send_message(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """
        Send a message to a specific connection.
        Returns True if successful, False if connection is dead.
        """
        if connection_id not in self.active_connections:
            return False
        
        websocket = self.active_connections[connection_id]
        
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to {connection_id}: {e}")
            # Connection is dead, clean it up
            await self.disconnect(connection_id)
            return False
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """
        Broadcast a message to all connections for a specific user.
        Returns number of successful sends.
        """
        if user_id not in self.user_connections:
            return 0
        
        connection_ids = self.user_connections[user_id].copy()  # Copy to avoid modification during iteration
        success_count = 0
        
        for connection_id in connection_ids:
            if await self.send_message(connection_id, message):
                success_count += 1
        
        return success_count
    
    async def broadcast_to_all(self, message: Dict[str, Any]) -> int:
        """
        Broadcast a message to all active connections.
        Returns number of successful sends.
        """
        connection_ids = list(self.active_connections.keys())
        success_count = 0
        
        for connection_id in connection_ids:
            if await self.send_message(connection_id, message):
                success_count += 1
        
        return success_count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.
        """
        user_stats = {
            user_id: len(connections) 
            for user_id, connections in self.user_connections.items()
        }
        
        return {
            "total_connections": len(self.active_connections),
            "total_users": len(self.user_connections),
            "user_stats": user_stats,
            "connection_metadata": self.connection_metadata
        }


class WebSocketService:
    """
    Main WebSocket service with high-level operations.
    """
    
    def __init__(self):
        self.manager = WebSocketManager()
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """
        Connect a WebSocket for a user.
        """
        return await self.manager.connect(websocket, user_id)
    
    async def disconnect(self, connection_id: str):
        """
        Disconnect a WebSocket connection.
        """
        await self.manager.disconnect(connection_id)
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """
        Send message to all user's connections.
        """
        return await self.manager.broadcast_to_user(user_id, message)
    
    async def broadcast_execution_event(self, event_type: str, user_id: str, data: Dict[str, Any]):
        """
        Broadcast execution-related events to user's connections.
        Compatible with SSE event format.
        """
        message = {
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.manager.broadcast_to_user(user_id, message)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.
        """
        return self.manager.get_stats()


# Global WebSocket service instance
websocket_service = WebSocketService() 