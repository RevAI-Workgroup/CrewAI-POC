"""
Thread management service for conversation handling

Handles thread lifecycle, validation, and business logic for the chat interface.
Provides CRUD operations with proper user access control and graph validation.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from models.thread import Thread, ThreadStatus
from models.graph import Graph
from models.message import Message, MessageStatus
from models.execution import Execution, ExecutionStatus
from models.node_types import NodeTypeEnum
from services.graph_crew_validation_service import GraphCrewValidationService

logger = logging.getLogger(__name__)


class ThreadService:
    """Service for managing conversation threads."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_thread(
        self, 
        graph_id: str, 
        user_id: str, 
        name: str, 
        description: Optional[str] = None,
        thread_config: Optional[Dict[str, Any]] = None
    ) -> Thread:
        """Create a new thread with validation."""
        try:
            # Validate graph access
            graph = self._validate_graph_access(graph_id, user_id)
            
            # Validate graph for chat (single crew restriction + no existing threads)
            validation_service = GraphCrewValidationService(self.db)
            validation_service.validate_graph_for_new_thread(graph)
            
            # Create thread
            thread = Thread(
                id=str(uuid.uuid4()),
                graph_id=graph_id,
                name=name,
                description=description,
                status=ThreadStatus.ACTIVE.value,
                thread_config=thread_config or {}
            )
            
            self.db.add(thread)
            self.db.commit()
            self.db.refresh(thread)
            
            logger.info(f"Created thread {thread.id} for graph {graph_id}")
            return thread
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create thread: {e}")
            raise
    
    def get_thread(self, thread_id: str, user_id: str) -> Optional[Thread]:
        """Get a specific thread by ID with user access validation."""
        thread = self.db.query(Thread).filter(
            Thread.id == thread_id,
            Thread.status != ThreadStatus.DELETED.value  # type: ignore
        ).first()
        
        if not thread:
            return None
        
        # Validate user access through graph ownership
        if not thread.can_be_accessed_by(user_id):
            raise PermissionError(f"User {user_id} cannot access thread {thread_id}")
        
        # Add message count
        message_count = self.db.query(func.count(Message.id)).filter(
            Message.thread_id == thread_id
        ).scalar()
        thread.message_count = message_count or 0
        
        return thread
    
    def get_graph_threads(self, graph_id: str, user_id: str) -> List[Thread]:
        """Get all threads for a specific graph."""
        # Validate graph access first
        self._validate_graph_access(graph_id, user_id)
        
        threads = self.db.query(Thread).filter(
            and_(
                Thread.graph_id == graph_id,
                Thread.status != ThreadStatus.DELETED.value  # type: ignore
            )
        ).order_by(desc(Thread.updated_at)).all()  # type: ignore
        
        # Add message count to each thread
        for thread in threads:
            message_count = self.db.query(func.count(Message.id)).filter(
                Message.thread_id == thread.id
            ).scalar()
            thread.message_count = message_count or 0
        
        return threads
    
    def list_user_threads(
        self, 
        user_id: str, 
        status_filter: Optional[ThreadStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Thread]:
        """List all threads accessible by a user with optional filtering."""
        try:
            # Build query to find threads through graph ownership
            query = self.db.query(Thread).join(Graph).filter(
                Graph.user_id == user_id,
                Thread.status != ThreadStatus.DELETED.value  # type: ignore
            )
            
            # Apply status filter if provided
            if status_filter:
                query = query.filter(Thread.status == status_filter.value)  # type: ignore
            
            # Apply pagination and ordering
            threads = query.order_by(
                desc(Thread.updated_at)  # type: ignore
            ).offset(offset).limit(limit).all()
            
            # Add message count to each thread
            for thread in threads:
                message_count = self.db.query(func.count(Message.id)).filter(
                    Message.thread_id == thread.id
                ).scalar()
                thread.message_count = message_count or 0
            
            return threads
            
        except Exception as e:
            logger.error(f"Failed to list threads for user {user_id}: {e}")
            raise
    
    def update_thread(
        self,
        thread_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[ThreadStatus] = None,
        thread_config: Optional[Dict[str, Any]] = None
    ) -> Thread:
        """Update a thread with validation."""
        try:
            thread = self.get_thread(thread_id, user_id)
            if not thread:
                raise ValueError(f"Thread {thread_id} not found")
            
            # Validate status transitions if changing status
            if status is not None:
                self._validate_status_transition(thread, status)
            
            # Update fields if provided
            if name is not None:
                if not name.strip():
                    raise ValueError("Thread name cannot be empty")
                if len(name) > 200:
                    raise ValueError("Thread name cannot exceed 200 characters")
                setattr(thread, 'name', name.strip())
            
            if description is not None:
                setattr(thread, 'description', description)
            
            if status is not None:
                thread.set_status(status)
            
            if thread_config is not None:
                thread.set_thread_config(thread_config)
            
            # Update activity timestamp
            thread.update_last_activity()
            
            self.db.commit()
            self.db.refresh(thread)
            
            logger.info(f"Updated thread {thread_id}")
            return thread
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update thread {thread_id}: {e}")
            raise
    
    def delete_thread(self, thread_id: str, user_id: str) -> bool:
        """Soft delete a thread and handle cleanup."""
        try:
            thread = self.get_thread(thread_id, user_id)
            if not thread:
                return False
            
            # Soft delete the thread
            thread.soft_delete()
            
            # Update any pending messages in this thread
            pending_messages = self.db.query(Message).filter(
                and_(
                    Message.thread_id == thread_id,
                    Message.status == MessageStatus.PENDING.value  # type: ignore
                )
            ).all()
            
            for message in pending_messages:
                message.set_status(MessageStatus.FAILED)
            
            self.db.commit()
            
            logger.info(f"Deleted thread {thread_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete thread {thread_id}: {e}")
            raise
    
    def archive_thread(self, thread_id: str, user_id: str) -> Thread:
        """Archive a thread."""
        return self.update_thread(
            thread_id=thread_id,
            user_id=user_id,
            status=ThreadStatus.ARCHIVED
        )
    
    def activate_thread(self, thread_id: str, user_id: str) -> Thread:
        """Activate an archived thread."""
        return self.update_thread(
            thread_id=thread_id,
            user_id=user_id,
            status=ThreadStatus.ACTIVE
        )
    
    def is_crew_executing(self, graph_id: str) -> bool:
        """Check if any crew is currently executing for the given graph."""
        active_executions = self.db.query(Execution).filter(
            and_(
                Execution.graph_id == graph_id,
                or_(
                    Execution.status == ExecutionStatus.RUNNING.value,  # type: ignore
                    Execution.status == ExecutionStatus.PENDING.value  # type: ignore
                )
            )
        ).count()
        
        return active_executions > 0
    
    def get_thread_statistics(self, thread_id: str, user_id: str) -> Dict[str, Any]:
        """Get statistics for a thread."""
        thread = self.get_thread(thread_id, user_id)
        if not thread:
            raise ValueError(f"Thread {thread_id} not found")
        
        # Get message statistics
        message_stats = self.db.query(
            func.count(Message.id).label('total_messages'),
            func.count(Message.id).filter(Message.message_type == 'user').label('user_messages'),  # type: ignore
            func.count(Message.id).filter(Message.message_type == 'assistant').label('assistant_messages'),  # type: ignore
            func.count(Message.id).filter(Message.triggers_execution == True).label('execution_triggers')  # type: ignore
        ).filter(Message.thread_id == thread_id).first()
        
        # Get execution statistics  
        execution_stats = self.db.query(
            func.count(Execution.id).label('total_executions'),
            func.count(Execution.id).filter(Execution.status == ExecutionStatus.COMPLETED.value).label('completed_executions'),  # type: ignore
            func.count(Execution.id).filter(Execution.status == ExecutionStatus.FAILED.value).label('failed_executions')  # type: ignore
        ).join(Message, Execution.id == Message.execution_id).filter(
            Message.thread_id == thread_id
        ).first()
        
        return {
            'thread_id': thread_id,
            'total_messages': getattr(message_stats, 'total_messages', 0) or 0,
            'user_messages': getattr(message_stats, 'user_messages', 0) or 0,
            'assistant_messages': getattr(message_stats, 'assistant_messages', 0) or 0,
            'execution_triggers': getattr(message_stats, 'execution_triggers', 0) or 0,
            'total_executions': getattr(execution_stats, 'total_executions', 0) or 0,
            'completed_executions': getattr(execution_stats, 'completed_executions', 0) or 0,
            'failed_executions': getattr(execution_stats, 'failed_executions', 0) or 0,
            'last_activity': thread.last_activity_at,
            'created_at': thread.created_at,
            'status': thread.status
        }
    
    # Private validation methods
    
    def _validate_graph_access(self, graph_id: str, user_id: str) -> Graph:
        """Validate that the graph exists and user has access."""
        graph = self.db.query(Graph).filter(Graph.id == graph_id).first()
        
        if not graph:
            raise ValueError(f"Graph {graph_id} not found")
        
        if not graph.can_be_accessed_by(user_id):
            raise PermissionError(f"User {user_id} cannot access graph {graph_id}")
        
        if not getattr(graph, 'is_active', True):
            raise ValueError(f"Graph {graph_id} is not active")
        
        return graph
    

    
    def _validate_status_transition(self, thread: Thread, new_status: ThreadStatus) -> None:
        """Validate status transitions are allowed."""
        current_status = ThreadStatus(thread.status)
        
        # Define allowed transitions
        allowed_transitions = {
            ThreadStatus.ACTIVE: [ThreadStatus.ARCHIVED, ThreadStatus.DELETED],
            ThreadStatus.ARCHIVED: [ThreadStatus.ACTIVE, ThreadStatus.DELETED],
            ThreadStatus.DELETED: []  # No transitions from deleted
        }
        
        if new_status not in allowed_transitions.get(current_status, []):
            raise ValueError(f"Cannot transition thread from {current_status.value} to {new_status.value}")
    
    def validate_thread_config(self, config: Dict[str, Any]) -> bool:
        """Validate thread configuration structure."""
        if not isinstance(config, dict):
            raise ValueError("Thread configuration must be a dictionary")
        
        # Add any specific validation rules for thread config here
        # For now, we accept any valid JSON structure
        
        return True 