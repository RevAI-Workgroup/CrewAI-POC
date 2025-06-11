"""
Execution Status Management Service

Centralized service for managing execution status transitions, progress tracking,
and execution lifecycle management.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from uuid import UUID
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models.execution import Execution, ExecutionStatus, ExecutionPriority
from db_config import SessionLocal

logger = logging.getLogger(__name__)


class StatusTransitionError(Exception):
    """Raised when an invalid status transition is attempted."""
    pass


class ExecutionStatusService:
    """Service for centralized execution status management."""
    
    # Valid status transitions
    VALID_TRANSITIONS = {
        ExecutionStatus.PENDING: [ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED],
        ExecutionStatus.RUNNING: [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT],
        ExecutionStatus.COMPLETED: [],  # Terminal state
        ExecutionStatus.FAILED: [ExecutionStatus.PENDING],  # Can retry
        ExecutionStatus.CANCELLED: [],  # Terminal state
        ExecutionStatus.TIMEOUT: [ExecutionStatus.PENDING],  # Can retry
    }
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()
        self._status_callbacks: Dict[ExecutionStatus, List[Callable]] = {}
    
    def register_status_callback(self, status: ExecutionStatus, callback: Callable):
        """Register a callback to be called when execution reaches specific status."""
        if status not in self._status_callbacks:
            self._status_callbacks[status] = []
        self._status_callbacks[status].append(callback)
    
    def validate_transition(self, from_status: ExecutionStatus, to_status: ExecutionStatus) -> bool:
        """Validate if status transition is allowed."""
        if from_status not in self.VALID_TRANSITIONS:
            return False
        return to_status in self.VALID_TRANSITIONS[from_status]
    
    def update_execution_status(
        self,
        execution_id: UUID,
        new_status: ExecutionStatus,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        result_data: Optional[Dict[str, Any]] = None
    ) -> Execution:
        """Update execution status with validation and callbacks."""
        try:
            execution = self.db.query(Execution).filter(Execution.id == str(execution_id)).first()
            if not execution:
                raise ValueError(f"Execution {execution_id} not found")
            
            current_status = ExecutionStatus(execution.status)
            
            # Validate transition
            if not self.validate_transition(current_status, new_status):
                raise StatusTransitionError(
                    f"Invalid status transition from {current_status.value} to {new_status.value}"
                )
            
            # Update status
            execution.set_status(new_status)
            
            # Update progress if provided
            if progress is not None:
                execution.update_progress(progress, current_step)
            
            # Handle specific status updates
            if new_status == ExecutionStatus.COMPLETED and result_data:
                execution.complete_execution(result_data)
            elif new_status == ExecutionStatus.FAILED:
                execution.fail_execution(error_message or "Execution failed", error_details)
            elif new_status == ExecutionStatus.CANCELLED:
                execution.cancel_execution(error_message)
            
            self.db.commit()
            
            # Execute callbacks
            self._execute_callbacks(new_status, execution)
            
            logger.info(f"Updated execution {execution_id} status to {new_status.value}")
            return execution
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update execution status: {e}")
            raise
    
    def _execute_callbacks(self, status: ExecutionStatus, execution: Execution):
        """Execute registered callbacks for status change."""
        if status in self._status_callbacks:
            for callback in self._status_callbacks[status]:
                try:
                    callback(execution)
                except Exception as e:
                    logger.error(f"Status callback failed: {e}")
    
    def get_execution_status(self, execution_id: UUID) -> Dict[str, Any]:
        """Get detailed execution status information."""
        execution = self.db.query(Execution).filter(Execution.id == str(execution_id)).first()
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        return {
            "id": execution.id,
            "status": execution.status,
            "progress_percentage": execution.progress_percentage,
            "current_step": execution.current_step,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "duration_seconds": execution.duration_seconds,
            "error_message": execution.error_message,
            "is_cancelled": execution.is_cancelled,
            "priority": execution.priority
        }
    
    def bulk_update_status(
        self,
        execution_ids: List[UUID],
        new_status: ExecutionStatus,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update status for multiple executions."""
        results = {"updated": [], "failed": [], "skipped": []}
        
        for execution_id in execution_ids:
            try:
                execution = self.update_execution_status(
                    execution_id,
                    new_status,
                    error_message=reason
                )
                results["updated"].append(str(execution_id))
            except StatusTransitionError as e:
                logger.warning(f"Skipped execution {execution_id}: {e}")
                results["skipped"].append(str(execution_id))
            except Exception as e:
                logger.error(f"Failed to update execution {execution_id}: {e}")
                results["failed"].append(str(execution_id))
        
        return results
    
    def get_executions_by_status(
        self,
        status: ExecutionStatus,
        limit: Optional[int] = None,
        since: Optional[datetime] = None
    ) -> List[Execution]:
        """Get executions filtered by status."""
        query = self.db.query(Execution).filter(Execution.status == status.value)
        
        if since:
            query = query.filter(Execution.created_at >= since)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_stuck_executions(self, timeout_minutes: int = 60) -> List[Execution]:
        """Find executions that have been running too long."""
        timeout_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        return self.db.query(Execution).filter(
            and_(
                Execution.status == ExecutionStatus.RUNNING.value,
                Execution.started_at < timeout_threshold
            )
        ).all()
    
    def timeout_stuck_executions(self, timeout_minutes: int = 60) -> List[str]:
        """Mark stuck executions as timed out."""
        stuck_executions = self.get_stuck_executions(timeout_minutes)
        timed_out = []
        
        for execution in stuck_executions:
            try:
                self.update_execution_status(
                    UUID(execution.id),
                    ExecutionStatus.TIMEOUT,
                    error_message=f"Execution timed out after {timeout_minutes} minutes"
                )
                timed_out.append(execution.id)
            except Exception as e:
                logger.error(f"Failed to timeout execution {execution.id}: {e}")
        
        return timed_out
    
    def get_execution_statistics(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Get execution statistics."""
        query = self.db.query(Execution)
        
        if since:
            query = query.filter(Execution.created_at >= since)
        
        executions = query.all()
        
        stats = {
            "total": len(executions),
            "by_status": {},
            "avg_duration": 0,
            "success_rate": 0
        }
        
        # Count by status
        for status in ExecutionStatus:
            stats["by_status"][status.value] = sum(1 for e in executions if e.status == status.value)
        
        # Calculate averages
        completed = [e for e in executions if e.status == ExecutionStatus.COMPLETED.value and e.duration_seconds]
        if completed:
            stats["avg_duration"] = sum(e.duration_seconds for e in completed) / len(completed)
        
        # Success rate
        finished = [e for e in executions if e.status in [ExecutionStatus.COMPLETED.value, ExecutionStatus.FAILED.value]]
        if finished:
            successful = [e for e in finished if e.status == ExecutionStatus.COMPLETED.value]
            stats["success_rate"] = len(successful) / len(finished)
        
        return stats
    
    def cancel_user_executions(self, user_id: UUID, reason: str = "User requested cancellation") -> List[str]:
        """Cancel all running executions for a user."""
        # Note: This would need a user_id field in Execution model
        # For now, we'll return empty list as the model doesn't have user_id
        logger.warning("cancel_user_executions not implemented - Execution model needs user_id field")
        return []
    
    def cleanup_old_executions(self, days: int = 30) -> int:
        """Mark old completed/failed executions for cleanup."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_executions = self.db.query(Execution).filter(
            and_(
                Execution.completed_at < cutoff_date,
                or_(
                    Execution.status == ExecutionStatus.COMPLETED.value,
                    Execution.status == ExecutionStatus.FAILED.value,
                    Execution.status == ExecutionStatus.CANCELLED.value
                )
            )
        ).all()
        
        count = len(old_executions)
        logger.info(f"Found {count} old executions for cleanup")
        
        # For now, just log - actual cleanup would depend on business requirements
        return count
    
    def close(self):
        """Close database session."""
        if self.db:
            self.db.close() 