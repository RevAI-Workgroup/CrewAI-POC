"""
Message Processing Service

Handles message lifecycle, execution triggering, and status management.
Integrates with AsyncExecutionService to trigger CrewAI executions based on messages.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.message import Message, MessageType, MessageStatus
from models.thread import Thread
from models.execution import Execution, ExecutionStatus
from services.async_execution_service import AsyncExecutionService
from db_config import SessionLocal

# Import SSE service for real-time updates
try:
    from services.sse_service import sse_service
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False
    sse_service = None

logger = logging.getLogger(__name__)


class MessageProcessingService:
    """Service for processing messages and triggering executions."""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()
        self._should_close_db = db is None
        self.execution_service = AsyncExecutionService()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close_db:
            self.db.close()
    
    def create_message(
        self,
        thread_id: str,
        content: str,
        user_id: str,
        message_type: MessageType = MessageType.USER,
        triggers_execution: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Create a new message and optionally trigger execution."""
        
        # Validate thread exists and user has access
        thread = self.db.query(Thread).filter(Thread.id == thread_id).first()
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")
        
        if not thread.can_be_accessed_by(user_id):
            raise PermissionError(f"User {user_id} cannot access thread {thread_id}")
        
        # Get next sequence number for this thread
        last_message = self.db.query(Message).filter(
            Message.thread_id == thread_id
        ).order_by(desc(Message.sequence_number)).first()
        
        sequence_number = (getattr(last_message, 'sequence_number', 0) + 1) if last_message else 1
        
        # Create message
        message = Message(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            content=content,
            message_type=message_type.value,
            status=MessageStatus.PENDING.value,
            message_metadata=metadata,
            sequence_number=sequence_number,
            triggers_execution=triggers_execution
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        logger.info(f"Created message {getattr(message, 'id')} in thread {thread_id}")
        
        # Broadcast message creation via SSE
        self._broadcast_message_event("message_created", message, user_id)
        
        # Trigger execution if requested
        if triggers_execution:
            try:
                self.process_message_for_execution(getattr(message, 'id'), user_id)
            except Exception as e:
                logger.error(f"Failed to trigger execution for message {getattr(message, 'id')}: {e}")
                # Don't fail message creation if execution trigger fails
        
        return message
    
    def get_message(self, message_id: str, user_id: str) -> Optional[Message]:
        """Get a message by ID with authorization check."""
        message = self.db.query(Message).filter(Message.id == message_id).first()
        
        if not message:
            return None
        
        if not message.can_be_accessed_by(user_id):
            raise PermissionError(f"User {user_id} cannot access message {message_id}")
        
        return message
    
    def get_thread_messages(
        self,
        thread_id: str,
        user_id: str,
        page: int = 1,
        page_size: int = 50,
        include_system: bool = True
    ) -> Tuple[List[Message], int]:
        """Get messages for a thread with pagination."""
        
        # Validate thread access
        thread = self.db.query(Thread).filter(Thread.id == thread_id).first()
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")
        
        if not thread.can_be_accessed_by(user_id):
            raise PermissionError(f"User {user_id} cannot access thread {thread_id}")
        
        # Build query
        query = self.db.query(Message).filter(Message.thread_id == thread_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        messages = query.order_by(Message.sequence_number).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return messages, total
    
    def update_message(
        self,
        message_id: str,
        user_id: str,
        content: Optional[str] = None,
        status: Optional[MessageStatus] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Update a message with authorization check."""
        
        message = self.get_message(message_id, user_id)
        if not message:
            raise ValueError(f"Message {message_id} not found")
        
        # Update fields using setattr for proper SQLAlchemy handling
        if content is not None:
            setattr(message, 'content', content)
        
        if status is not None:
            message.set_status(status)
        
        if metadata is not None:
            message.set_metadata(metadata)
        
        self.db.commit()
        self.db.refresh(message)
        
        logger.info(f"Updated message {message_id}")
        
        # Broadcast message update via SSE
        self._broadcast_message_event("message_updated", message, user_id)
        
        return message
    
    def process_message_for_execution(
        self,
        message_id: str,
        user_id: str,
        execution_config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Process a message to trigger execution if conditions are met."""
        
        message = self.get_message(message_id, user_id)
        if not message:
            raise ValueError(f"Message {message_id} not found")
        
        # Check if message should trigger execution
        triggers_execution = getattr(message, 'triggers_execution', False)
        if not triggers_execution:
            logger.info(f"Message {message_id} does not trigger execution")
            return None
        
        # Check if message is already linked to an execution
        execution_id = getattr(message, 'execution_id', None)
        if execution_id:
            logger.info(f"Message {message_id} already linked to execution {execution_id}")
            return execution_id
        
        # Check if message is in a valid state for processing
        if not message.is_pending():
            current_status = getattr(message, 'status', 'unknown')
            logger.warning(f"Message {message_id} is not in pending state (current: {current_status})")
            return None
        
        # Get thread and graph information
        thread = message.thread
        if not thread or not getattr(thread, 'graph', None):
            thread_id = getattr(message, 'thread_id', 'unknown')
            raise ValueError(f"Thread {thread_id} or graph not found")
        
        # Mark message as processing
        message.mark_processing()
        self.db.commit()
        
        logger.info(f"Processing message {message_id} for execution")
        
        # Broadcast processing start
        self._broadcast_message_event("message_processing", message, user_id)
        
        try:
            # Prepare execution inputs from message content and metadata
            message_content = getattr(message, 'content', '')
            message_thread_id = getattr(message, 'thread_id', '')
            inputs = {
                "message_content": message_content,
                "message_id": message_id,
                "thread_id": message_thread_id,
                "user_inputs": message.get_metadata().get("user_inputs", {})
            }
            
            # Add any custom execution config
            if execution_config:
                inputs.update(execution_config)
            
            # Queue execution - convert strings to UUID where needed
            graph_id = getattr(thread, 'graph_id', '')
            task_id = self.execution_service.queue_execution(
                graph_id=UUID(graph_id),
                thread_id=UUID(message_thread_id),
                user_id=UUID(user_id),
                inputs=inputs
            )
            
            # Create execution record and link to message
            execution = Execution(
                id=str(uuid.uuid4()),
                graph_id=graph_id,
                trigger_message_id=message_id,
                status=ExecutionStatus.PENDING.value,
                execution_config={
                    "task_id": task_id,
                    "inputs": inputs,
                    "triggered_by_message": True
                }
            )
            
            self.db.add(execution)
            self.db.commit()
            
            # Link message to execution
            execution_id_str = getattr(execution, 'id', '')
            message.link_execution(execution_id_str)
            self.db.commit()
            
            logger.info(f"Triggered execution {execution_id_str} for message {message_id} (task: {task_id})")
            
            # Broadcast execution trigger
            self._broadcast_message_event("execution_triggered", message, user_id, {
                "execution_id": execution_id_str,
                "task_id": task_id
            })
            
            return execution_id_str
            
        except Exception as e:
            logger.error(f"Failed to trigger execution for message {message_id}: {e}")
            
            # Mark message as failed
            message.mark_failed()
            message.set_metadata({
                **message.get_metadata(),
                "execution_error": str(e),
                "failed_at": datetime.utcnow().isoformat()
            })
            self.db.commit()
            
            # Broadcast failure
            self._broadcast_message_event("execution_trigger_failed", message, user_id, {
                "error": str(e)
            })
            
            raise
    
    def handle_execution_completion(
        self,
        execution_id: str,
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Handle execution completion and update related message."""
        
        # Find the message that triggered this execution
        execution = self.db.query(Execution).filter(Execution.id == execution_id).first()
        trigger_message_id = getattr(execution, 'trigger_message_id', None) if execution else None
        
        if not execution or not trigger_message_id:
            logger.warning(f"No triggering message found for execution {execution_id}")
            return
        
        message = self.db.query(Message).filter(Message.id == trigger_message_id).first()
        if not message:
            logger.warning(f"Triggering message {trigger_message_id} not found")
            return
        
        # Update message status based on execution result
        if error_message:
            message.mark_failed()
            message.set_metadata({
                **message.get_metadata(),
                "execution_error": error_message,
                "execution_completed_at": datetime.utcnow().isoformat()
            })
        else:
            message.mark_completed()
            message.set_metadata({
                **message.get_metadata(),
                "execution_result": result_data,
                "execution_completed_at": datetime.utcnow().isoformat()
            })
        
        self.db.commit()
        
        # Get user ID for broadcasting
        user_id = message.get_user_id()
        if user_id:
            event_type = "execution_completed" if not error_message else "execution_failed"
            self._broadcast_message_event(event_type, message, user_id, {
                "execution_id": execution_id,
                "result": result_data,
                "error": error_message
            })
        
        message_id = getattr(message, 'id', 'unknown')
        logger.info(f"Updated message {message_id} for execution {execution_id} completion")
    
    def _broadcast_message_event(
        self,
        event_type: str,
        message: Message,
        user_id: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Broadcast message event via SSE if available."""
        
        if not SSE_AVAILABLE or not sse_service:
            return
        
        try:
            import asyncio
            
            event_data = {
                "message_id": getattr(message, 'id', ''),
                "thread_id": getattr(message, 'thread_id', ''),
                "status": getattr(message, 'status', ''),
                "sequence_number": getattr(message, 'sequence_number', 0),
                "triggers_execution": getattr(message, 'triggers_execution', False),
                "execution_id": getattr(message, 'execution_id', None),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if additional_data:
                event_data.update(additional_data)
            
            # Create async task to broadcast event
            asyncio.create_task(sse_service.broadcast_execution_event(
                event_type,
                user_id,
                event_data
            ))
            
        except Exception as e:
            logger.warning(f"Failed to broadcast message event {event_type}: {e}")
    
    def close(self):
        """Close database session if we created it."""
        if self._should_close_db and self.db:
            self.db.close() 