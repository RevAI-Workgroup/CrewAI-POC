"""
WebSocket router for real-time updates.
Alternative to SSE for performance comparison.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.security import HTTPBearer

from utils.dependencies import get_current_user_websocket, get_current_user
from services.websocket_service import websocket_service
from models.user import User

router = APIRouter(prefix="/ws", tags=["WebSocket"])

security = HTTPBearer()


@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket endpoint for real-time communication.
    Requires JWT token as query parameter for authentication.
    """
    try:
        # Authenticate user via token
        user = await get_current_user_websocket(token)
        if not user:
            await websocket.close(code=4001, reason="Unauthorized")
            return
        
        # Accept connection
        await websocket.accept()
        
        # Register connection
        connection_id = await websocket_service.connect(websocket, str(user.id))
        
        # Send connection confirmation
        await websocket.send_json({
            "event": "connected",
            "connection_id": connection_id,
            "user_id": str(user.id),
            "message": "WebSocket connection established"
        })
        
        try:
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_json()
                
                # Handle ping/pong for connection health
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("type") == "test":
                    # Echo test messages
                    await websocket.send_json({
                        "event": "test_response",
                        "original_message": data.get("message", ""),
                        "timestamp": data.get("timestamp")
                    })
                    
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            # Clean up connection
            await websocket_service.disconnect(connection_id)
            
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=4000, reason="Connection error")
        except:
            pass


@router.get("/stats")
async def get_websocket_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get WebSocket connection statistics.
    Returns overall stats for admin users, user-specific stats for regular users.
    """
    stats = websocket_service.get_stats()
    
    # For regular users, only return their own connection count
    if not current_user.is_admin:
        user_id = str(current_user.id)
        return {
            "user_connections": stats.get("user_stats", {}).get(user_id, 0),
            "user_id": user_id
        }
    
    # Admin users get full stats
    return stats


@router.post("/broadcast")
async def send_test_message(
    message: str = Query(..., description="Test message to broadcast"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Send a test message to the user's WebSocket connections.
    Useful for testing WebSocket functionality.
    """
    try:
        await websocket_service.broadcast_to_user(
            str(current_user.id),
            {
                "event": "test_message",
                "message": message,
                "from_user": str(current_user.id)
            }
        )
        return {
            "message": "Test message sent",
            "user_id": str(current_user.id),
            "event_type": "test_message"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test message: {str(e)}")


@router.delete("/disconnect/{connection_id}")
async def disconnect_websocket(
    connection_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Manually disconnect a WebSocket connection.
    """
    try:
        await websocket_service.disconnect(connection_id)
        return {
            "message": "WebSocket connection disconnected",
            "connection_id": connection_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}") 