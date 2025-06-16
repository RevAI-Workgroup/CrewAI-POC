"""
Execution Record Management Service for Chat Streaming

Handles execution lifecycle during chat streaming operations including:
- Creation of execution records before streaming
- Status updates throughout streaming lifecycle
- Message-execution linking and synchronization
- Proper transaction management and error handling
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from models.execution import Execution, ExecutionStatus
from models.message import Message, MessageStatus
from services.execution_status_service import ExecutionStatusService

logger = logging.getLogger(__name__)


class ExecutionRecordService:
    """Service for managing execution records during chat streaming."""
    
    def __init__(self, db: Session):
        self.db = db
        self.status_service = ExecutionStatusService(db)
    
    def create_chat_execution(
        self,
        graph_id: str,
        trigger_message_id: Optional[str] = None,
        execution_config: Optional[Dict[str, Any]] = None
    ) -> Execution:
        """
        Create a new execution record for chat streaming.
        
        Args:
            graph_id: ID of the graph being executed
            trigger_message_id: ID of the message that triggered this execution
            execution_config: Configuration data for the execution
            
        Returns:
            Created Execution record
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            execution_id = str(uuid4())
            
            execution = Execution(
                id=execution_id,
                graph_id=graph_id,
                trigger_message_id=trigger_message_id,
                status=ExecutionStatus.PENDING.value,
                execution_config=execution_config or {},
                progress_percentage=0
            )
            
            self.db.add(execution)
            self.db.flush()  # Get the ID without committing
            
            logger.info(f"Created execution record {execution_id} for graph {graph_id}")
            return execution
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to create execution record: {e}")
            self.db.rollback()
            raise
    
    def start_execution(self, execution_id: str) -> None:
        """
        Mark execution as started and update timestamps.
        
        Args:
            execution_id: ID of the execution to start
            
        Raises:
            ValueError: If execution not found
            SQLAlchemyError: If database operation fails
        """
        try:
            execution = self.db.query(Execution).filter(Execution.id == execution_id).first()
            if not execution:
                raise ValueError(f"Execution {execution_id} not found")
            
            # Use status service for proper transition validation
            self.status_service.update_execution_status(
                execution_id=UUID(execution_id),
                new_status=ExecutionStatus.RUNNING,
                progress=0,
                current_step="Starting execution"
            )
            
            logger.info(f"Started execution {execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to start execution {execution_id}: {e}")
            raise
    
    def update_execution_progress(
        self,
        execution_id: str,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        intermediate_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update execution progress during streaming.
        
        Args:
            execution_id: ID of the execution to update
            progress: Progress percentage (0-100)
            current_step: Description of current execution step
            intermediate_data: Any intermediate data to store
            
        Raises:
            ValueError: If execution not found or invalid progress
            SQLAlchemyError: If database operation fails
        """
        try:
            execution = self.db.query(Execution).filter(Execution.id == execution_id).first()
            if not execution:
                raise ValueError(f"Execution {execution_id} not found")
            
            if progress is not None:
                if not 0 <= progress <= 100:
                    raise ValueError("Progress must be between 0 and 100")
                execution.update_progress(progress, current_step)
            
            if intermediate_data:
                # Store intermediate data in execution config
                config = execution.get_execution_config()
                config['intermediate_data'] = intermediate_data
                execution.set_execution_config(config)
            
            # Add log entry if step provided
            if current_step:
                execution.add_log_entry(f"Progress: {progress}% - {current_step}")
            
            self.db.flush()
            logger.debug(f"Updated execution {execution_id} progress: {progress}%")
            
        except Exception as e:
            logger.error(f"Failed to update execution progress {execution_id}: {e}")
            raise
    
    def complete_execution(
        self,
        execution_id: str,
        result_data: Dict[str, Any],
        final_output: Optional[str] = None
    ) -> None:
        """
        Mark execution as completed with results.
        
        Args:
            execution_id: ID of the execution to complete
            result_data: Final result data from the execution
            final_output: Final output text/content
            
        Raises:
            ValueError: If execution not found
            SQLAlchemyError: If database operation fails
        """
        try:
            # Use status service for proper completion
            self.status_service.update_execution_status(
                execution_id=UUID(execution_id),
                new_status=ExecutionStatus.COMPLETED,
                progress=100,
                current_step="Execution completed",
                result_data=result_data
            )
            
            # Add final log entry
            execution = self.db.query(Execution).filter(Execution.id == execution_id).first()
            if execution and final_output:
                execution.add_log_entry(f"Execution completed successfully")
            
            logger.info(f"Completed execution {execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to complete execution {execution_id}: {e}")
            raise
    
    def fail_execution(
        self,
        execution_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        traceback_info: Optional[str] = None
    ) -> None:
        """
        Mark execution as failed with error information.
        
        Args:
            execution_id: ID of the execution that failed
            error_message: Human-readable error message
            error_details: Detailed error information
            traceback_info: Stack trace information
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Prepare error details
            full_error_details = error_details or {}
            if traceback_info:
                full_error_details['traceback'] = traceback_info
            full_error_details['failed_at'] = datetime.utcnow().isoformat()
            
            # Use status service for proper failure handling
            self.status_service.update_execution_status(
                execution_id=UUID(execution_id),
                new_status=ExecutionStatus.FAILED,
                error_message=error_message,
                error_details=full_error_details
            )
            
            # Add error log entry
            execution = self.db.query(Execution).filter(Execution.id == execution_id).first()
            if execution:
                execution.add_log_entry(f"Execution failed: {error_message}")
            
            logger.error(f"Failed execution {execution_id}: {error_message}")
            
        except Exception as e:
            logger.error(f"Failed to mark execution {execution_id} as failed: {e}")
            # Don't raise here to avoid masking original error
    
    def link_message_to_execution(
        self,
        message_id: str,
        execution_id: str,
        user_id: str
    ) -> None:
        """
        Link a message to an execution record.
        
        Args:
            message_id: ID of the message to link
            execution_id: ID of the execution to link to
            user_id: ID of the user (for validation)
            
        Raises:
            ValueError: If message or execution not found
            SQLAlchemyError: If database operation fails
        """
        try:
            message = self.db.query(Message).filter(Message.id == message_id).first()
            if not message:
                raise ValueError(f"Message {message_id} not found")
            
            execution = self.db.query(Execution).filter(Execution.id == execution_id).first()
            if not execution:
                raise ValueError(f"Execution {execution_id} not found")
            
            # Link message to execution
            message.link_execution(execution_id)
            self.db.flush()
            
            logger.info(f"Linked message {message_id} to execution {execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to link message {message_id} to execution {execution_id}: {e}")
            raise
    
    def synchronize_message_status(
        self,
        message_id: str,
        execution_status: ExecutionStatus
    ) -> None:
        """
        Synchronize message status with execution status.
        
        Args:
            message_id: ID of the message to update
            execution_status: Current execution status
            
        Raises:
            ValueError: If message not found
            SQLAlchemyError: If database operation fails
        """
        try:
            message = self.db.query(Message).filter(Message.id == message_id).first()
            if not message:
                raise ValueError(f"Message {message_id} not found")
            
            # Map execution status to message status
            status_mapping = {
                ExecutionStatus.PENDING: MessageStatus.PENDING,
                ExecutionStatus.RUNNING: MessageStatus.PROCESSING,
                ExecutionStatus.COMPLETED: MessageStatus.COMPLETED,
                ExecutionStatus.FAILED: MessageStatus.FAILED,
                ExecutionStatus.CANCELLED: MessageStatus.FAILED,
                ExecutionStatus.TIMEOUT: MessageStatus.FAILED
            }
            
            message_status = status_mapping.get(execution_status, MessageStatus.PENDING)
            
            # Update message status using appropriate method
            if message_status == MessageStatus.PROCESSING:
                message.mark_processing()
            elif message_status == MessageStatus.COMPLETED:
                message.mark_completed()
            elif message_status == MessageStatus.FAILED:
                message.mark_failed()
            
            self.db.flush()
            logger.debug(f"Synchronized message {message_id} status to {message_status.value}")
            
        except Exception as e:
            logger.error(f"Failed to synchronize message {message_id} status: {e}")
            raise
    
    def cleanup_failed_execution(self, execution_id: str) -> None:
        """
        Clean up resources after a failed execution.
        
        Args:
            execution_id: ID of the failed execution
        """
        try:
            execution = self.db.query(Execution).filter(Execution.id == execution_id).first()
            if not execution:
                return
            
            # Add cleanup log entry
            execution.add_log_entry("Cleaning up failed execution resources")
            
            # Additional cleanup logic could go here
            # (e.g., cleanup temporary files, cancel background tasks, etc.)
            
            self.db.flush()
            logger.info(f"Cleaned up failed execution {execution_id}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup execution {execution_id}: {e}")
    
    def get_execution_by_id(self, execution_id: str) -> Optional[Execution]:
        """Get execution by ID."""
        return self.db.query(Execution).filter(Execution.id == execution_id).first()
    
    def get_execution_status(self, execution_id: str) -> Optional[ExecutionStatus]:
        """Get current execution status."""
        execution = self.get_execution_by_id(execution_id)
        if execution:
            return ExecutionStatus(execution.status)
        return None 