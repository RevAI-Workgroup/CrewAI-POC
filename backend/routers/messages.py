"""
Message API router for CRUD operations and execution triggering
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from models.user import User
from models.message import MessageType, MessageStatus
from schemas.message_schemas import (
    MessageCreateRequest, MessageUpdateRequest, MessageResponse, 
    MessageListResponse, MessageProcessingRequest, MessageProcessingResponse,
    MessageStatusSchema
)
from services.message_processing_service import MessageProcessingService
from utils.dependencies import get_current_user, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    request: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """Create a new message in a thread."""
    
    try:
        with MessageProcessingService(db) as service:
            message = service.create_message(
                thread_id=request.thread_id,
                content=request.content,
                user_id=str(current_user.id),
                message_type=MessageType(request.message_type.value),
                triggers_execution=request.triggers_execution,
                metadata=request.message_metadata
            )
            
            return MessageResponse.from_orm(message)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create message"
        )


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """Get a message by ID."""
    
    try:
        with MessageProcessingService(db) as service:
            message = service.get_message(message_id, str(current_user.id))
            
            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message {message_id} not found"
                )
            
            return MessageResponse.from_orm(message)
    
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve message"
        )


@router.get("/thread/{thread_id}", response_model=MessageListResponse)
async def get_thread_messages(
    thread_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Messages per page"),
    include_system: bool = Query(True, description="Include system messages"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageListResponse:
    """Get messages for a thread with pagination."""
    
    try:
        with MessageProcessingService(db) as service:
            messages, total = service.get_thread_messages(
                thread_id=thread_id,
                user_id=str(current_user.id),
                page=page,
                page_size=page_size,
                include_system=include_system
            )
            
            message_responses = [MessageResponse.from_orm(msg) for msg in messages]
            
            has_next = page * page_size < total
            has_prev = page > 1
            
            return MessageListResponse(
                messages=message_responses,
                total=total,
                page=page,
                page_size=page_size,
                has_next=has_next,
                has_prev=has_prev
            )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get messages for thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )


@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: str,
    request: MessageUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """Update a message."""
    
    try:
        with MessageProcessingService(db) as service:
            status_enum = None
            if request.status:
                status_enum = MessageStatus(request.status.value)
            
            message = service.update_message(
                message_id=message_id,
                user_id=str(current_user.id),
                content=request.content,
                status=status_enum,
                metadata=request.message_metadata
            )
            
            return MessageResponse.from_orm(message)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message"
        )


@router.post("/{message_id}/process", response_model=MessageProcessingResponse)
async def process_message(
    message_id: str,
    request: MessageProcessingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageProcessingResponse:
    """Process a message to trigger execution."""
    
    try:
        with MessageProcessingService(db) as service:
            execution_id = service.process_message_for_execution(
                message_id=message_id,
                user_id=str(current_user.id),
                execution_config=request.execution_config
            )
            
            # Get updated message status
            message = service.get_message(message_id, str(current_user.id))
            if not message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message {message_id} not found"
                )
            
            processing_started = execution_id is not None
            status_msg = "Execution triggered" if processing_started else "Message does not trigger execution"
            
            # Convert status to schema enum
            message_status = getattr(message, 'status', 'unknown')
            status_schema = MessageStatusSchema(message_status) if message_status in [e.value for e in MessageStatusSchema] else MessageStatusSchema.PENDING
            
            return MessageProcessingResponse(
                message_id=message_id,
                status=status_schema,
                execution_id=execution_id,
                processing_started=processing_started,
                message=status_msg
            )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to process message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a message (soft delete by marking as failed/cancelled)."""
    
    try:
        with MessageProcessingService(db) as service:
            # Update message status to mark as deleted/cancelled
            service.update_message(
                message_id=message_id,
                user_id=str(current_user.id),
                status=MessageStatus.FAILED,
                metadata={"deleted": True, "deleted_at": datetime.utcnow().isoformat()}
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message"
        ) 