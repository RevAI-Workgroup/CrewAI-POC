"""
Thread management router for conversation handling
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from db_config import get_db
from models.user import User
from models.thread import Thread, ThreadStatus
from models.graph import Graph
from schemas.thread_schemas import (
    ThreadCreateRequest, ThreadResponse, ThreadListResponse, 
    ThreadUpdateRequest
)
from services.thread_service import ThreadService
from utils.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/threads", tags=["Threads"])


@router.post("/", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    request: ThreadCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ThreadResponse:
    """Create a new thread for a graph"""
    try:
        service = ThreadService(db)
        thread = service.create_thread(
            graph_id=request.graph_id,
            user_id=str(current_user.id),
            name=request.name,
            description=request.description,
            thread_config=request.thread_config
        )
        
        return ThreadResponse.from_orm(thread)
        
    except ValueError as e:
        logger.warning(f"Invalid request for creating thread: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for creating thread: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create thread: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to create thread"
        )


@router.get("/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ThreadResponse:
    """Get a specific thread by ID"""
    try:
        service = ThreadService(db)
        thread = service.get_thread(thread_id, str(current_user.id))
        
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Thread not found"
            )
        
        return ThreadResponse.from_orm(thread)
        
    except HTTPException:
        raise
    except PermissionError as e:
        logger.warning(f"Permission denied for getting thread {thread_id}: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve thread"
        )


@router.get("/graph/{graph_id}", response_model=ThreadListResponse)
async def get_graph_threads(
    graph_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ThreadListResponse:
    """Get all threads for a specific graph"""
    try:
        service = ThreadService(db)
        threads = service.get_graph_threads(graph_id, str(current_user.id))
        
        thread_responses = [ThreadResponse.from_orm(thread) for thread in threads]
        
        return ThreadListResponse(
            threads=thread_responses,
            total=len(thread_responses),
            graph_id=graph_id
        )
        
    except ValueError as e:
        logger.warning(f"Invalid request for getting graph threads: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for getting graph {graph_id} threads: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get threads for graph {graph_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve threads"
        )


@router.put("/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: str,
    request: ThreadUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ThreadResponse:
    """Update a thread"""
    try:
        service = ThreadService(db)
        thread = service.update_thread(
            thread_id=thread_id,
            user_id=str(current_user.id),
            name=request.name,
            description=request.description,
            status=ThreadStatus(request.status) if request.status else None,
            thread_config=request.thread_config
        )
        
        return ThreadResponse.from_orm(thread)
        
    except ValueError as e:
        logger.warning(f"Invalid request for updating thread {thread_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for updating thread {thread_id}: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update thread"
        )


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a thread (soft delete)"""
    try:
        service = ThreadService(db)
        success = service.delete_thread(thread_id, str(current_user.id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread not found"
            )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid request for deleting thread {thread_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for deleting thread {thread_id}: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete thread"
        )


@router.get("/", response_model=List[ThreadResponse])
async def list_user_threads(
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[ThreadResponse]:
    """List all threads accessible by the current user"""
    try:
        service = ThreadService(db)
        
        # Convert status filter to enum if provided
        status_enum = None
        if status_filter:
            try:
                status_enum = ThreadStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        # Validate pagination parameters
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        if offset < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Offset must be non-negative"
            )
        
        threads = service.list_user_threads(
            user_id=str(current_user.id),
            status_filter=status_enum,
            limit=limit,
            offset=offset
        )
        
        return [ThreadResponse.from_orm(thread) for thread in threads]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list threads for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve threads"
        )


@router.post("/{thread_id}/archive", response_model=ThreadResponse)
async def archive_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ThreadResponse:
    """Archive a thread"""
    try:
        service = ThreadService(db)
        thread = service.archive_thread(thread_id, str(current_user.id))
        
        return ThreadResponse.from_orm(thread)
        
    except ValueError as e:
        logger.warning(f"Invalid request for archiving thread {thread_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for archiving thread {thread_id}: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to archive thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to archive thread"
        )


@router.post("/{thread_id}/activate", response_model=ThreadResponse)
async def activate_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ThreadResponse:
    """Activate an archived thread"""
    try:
        service = ThreadService(db)
        thread = service.activate_thread(thread_id, str(current_user.id))
        
        return ThreadResponse.from_orm(thread)
        
    except ValueError as e:
        logger.warning(f"Invalid request for activating thread {thread_id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        logger.warning(f"Permission denied for activating thread {thread_id}: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to activate thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate thread"
        ) 