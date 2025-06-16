"""
Message API router for CRUD operations and execution triggering
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from models.user import User
from models.message import MessageType, MessageStatus
from models.execution import Execution
from schemas.message_schemas import (
    MessageCreateRequest, MessageUpdateRequest, MessageResponse, 
    MessageListResponse, MessageProcessingRequest, MessageProcessingResponse,
    MessageStatusSchema, ChatMessageRequest
)
from services.message_processing_service import MessageProcessingService
from services.thread_service import ThreadService
from services.graph_translation import GraphTranslationService
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


@router.post("/chat/stream")
async def send_chat_message_stream(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """Send chat message and return streaming CrewAI execution response."""
    
    try:
        # Validate thread access
        thread_service = ThreadService(db)
        thread = thread_service.get_thread(request.threadId, str(current_user.id))
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Validate graph access through thread service
        graph = thread_service._validate_graph_access(str(thread.graph_id), str(current_user.id))
        
        # Check if crew is already executing for this graph
        if thread_service.is_crew_executing(str(thread.graph_id)):
            raise HTTPException(status_code=409, detail="Crew is already executing for this graph")
        
        # Validate graph for chat (single crew restriction) - using placeholder validation
        graph_data = getattr(graph, 'graph_data', None)
        if not graph_data:
            raise HTTPException(status_code=400, detail="Graph has no data")
        
        nodes = graph_data.get("nodes", [])
        crew_nodes = [n for n in nodes if n.get("type") == "crew"]
        
        if not crew_nodes:
            raise HTTPException(status_code=400, detail="Graph must have at least one crew node for chat")
        
        if len(crew_nodes) > 1:
            raise HTTPException(status_code=400, detail="Graph can only have one crew node for chat functionality")
        
        # Create streaming response generator
        async def generate_stream():
            execution = None
            assistant_message = None
            
            try:
                # Create user message
                with MessageProcessingService(db) as message_service:
                    user_message = message_service.create_message(
                        thread_id=request.threadId,
                        content=request.message,
                        user_id=str(current_user.id),
                        message_type=MessageType.USER,
                        triggers_execution=True
                    )
                
                    # Create assistant message placeholder
                    assistant_message = message_service.create_message(
                        thread_id=request.threadId,
                        content="",
                        user_id=str(current_user.id),
                        message_type=MessageType.ASSISTANT,
                        triggers_execution=False
                    )
                    assistant_message.mark_processing()
                
                # Create execution record before starting
                execution_id = str(uuid4())
                execution = Execution(
                    id=execution_id,
                    graph_id=str(thread.graph_id),
                    user_id=str(current_user.id),
                    status='running',
                    execution_config={
                        'message': request.message,
                        'output': request.output,
                        'thread_id': request.threadId
                    }
                )
                db.add(execution)
                
                # Link execution to message
                assistant_message.link_execution(execution_id)
                db.commit()
                
                # Translate graph to CrewAI objects
                translation_service = GraphTranslationService(db)
                crew = translation_service.translate_graph(graph)
                
                # Create a new task from the message (dynamic task creation will be in task 3-11)
                # For now, execute existing crew with kickoff inputs
                kickoff_inputs = {
                    'user_message': request.message,
                    'expected_output': request.output or "A helpful and detailed response"
                }
                
                # Execute CrewAI and stream response
                accumulated_content = ""
                async for chunk in execute_crew_stream(crew, execution_id, db, kickoff_inputs):
                    accumulated_content += chunk
                    
                    # Update assistant message content via service
                    with MessageProcessingService(db) as msg_service:
                        msg_service.update_message(
                            message_id=str(assistant_message.id),
                            user_id=str(current_user.id),
                            content=accumulated_content
                        )
                    
                    # Stream chunk
                    yield f"data: {json.dumps({'content': chunk, 'message_id': str(assistant_message.id)})}\n\n"
                
                # Mark execution and message as completed
                execution.status = 'completed'
                execution.result_data = {'content': accumulated_content}
                assistant_message.mark_completed()
                db.commit()
                
                yield f"data: {json.dumps({'done': True, 'message_id': assistant_message.id})}\n\n"
                
            except Exception as e:
                logger.error(f"Chat stream error: {e}")
                
                # Mark execution as failed
                if execution:
                    execution.status = 'failed'
                    execution.error_message = str(e)
                
                # Mark assistant message as failed
                if assistant_message:
                    with MessageProcessingService(db) as msg_service:
                        msg_service.update_message(
                            message_id=str(assistant_message.id),
                            user_id=str(current_user.id),
                            content=f"Error: {str(e)}",
                            status=MessageStatus.FAILED
                        )
                
                db.commit()
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat message processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


async def execute_crew_stream(crew, execution_id: str, db: Session, inputs: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """Execute CrewAI crew and yield streaming response chunks."""
    try:
        # Update execution status
        execution = db.query(Execution).filter(Execution.id == execution_id).first()
        if execution:
            execution.started_at = datetime.utcnow()
            db.commit()
        
        # Execute crew with inputs
        result = crew.kickoff(inputs=inputs)
        
        # Get content from result
        content = str(result.raw) if hasattr(result, 'raw') else str(result)
        
        # Split content into chunks for streaming effect
        chunk_size = 50
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            yield chunk
            # Small delay to simulate streaming
            import asyncio
            await asyncio.sleep(0.1)
        
        # Update execution completion
        if execution:
            execution.completed_at = datetime.utcnow()
            db.commit()
            
    except Exception as e:
        # Update execution with error
        if execution:
            execution.error_message = str(e)
            execution.status = 'failed'
            execution.completed_at = datetime.utcnow()
            db.commit()
        
        yield f"Error executing CrewAI: {str(e)}"


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