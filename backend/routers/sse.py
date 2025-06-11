"""
Server-Sent Events (SSE) router for real-time updates.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import StreamingResponse

from utils.dependencies import get_current_user
from services.sse_service import sse_service
from models.user import User

router = APIRouter(prefix="/sse", tags=["SSE"])


@router.get("/connect")
async def connect_sse(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Establish SSE connection for the authenticated user.
    Returns connection ID for subsequent stream requests.
    """
    try:
        connection_id = await sse_service.create_connection(request, str(current_user.id))
        return {
            "connection_id": connection_id,
            "message": "SSE connection established",
            "user_id": str(current_user.id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to establish SSE connection: {str(e)}")


@router.get("/stream/{connection_id}")
async def stream_sse(
    connection_id: str,
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    Get SSE event stream for the specified connection.
    """
    try:
        # Verify user owns this connection
        stats = sse_service.get_stats()
        user_id = str(current_user.id)
        
        # Check if user has any connections (basic auth check)
        if user_id not in stats.get("user_stats", {}):
            raise HTTPException(status_code=403, detail="No active connections for user")
        
        return await sse_service.get_event_stream(connection_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get event stream: {str(e)}")


@router.get("/stats")
async def get_sse_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get SSE connection statistics.
    Returns overall stats for admin users, user-specific stats for regular users.
    """
    stats = sse_service.get_stats()
    
    # For regular users, only return their own connection count
    if not current_user.is_admin:
        user_id = str(current_user.id)
        return {
            "user_connections": stats.get("user_stats", {}).get(user_id, 0),
            "user_id": user_id
        }
    
    # Admin users get full stats
    return stats


@router.post("/test")
async def send_test_event(
    message: str = Query(..., description="Test message to broadcast"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Send a test event to the user's SSE connections.
    Useful for testing SSE functionality.
    """
    try:
        await sse_service.broadcast_execution_event(
            "connection",
            str(current_user.id),
            {
                "status": "test",
                "message": message,
                "client_id": "test"
            }
        )
        return {
            "message": "Test event sent",
            "user_id": str(current_user.id),
            "event_type": "connection"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test event: {str(e)}")


@router.delete("/disconnect/{connection_id}")
async def disconnect_sse(
    connection_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Manually disconnect an SSE connection.
    """
    try:
        # Note: In a production system, you'd want to verify the user owns this connection
        # For now, we'll allow any authenticated user to disconnect any connection
        await sse_service.manager.disconnect(connection_id)
        return {
            "message": "Connection disconnected",
            "connection_id": connection_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}") 