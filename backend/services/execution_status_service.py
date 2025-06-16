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

# Import SSE service for real-time updates
try:
    from services.sse_service import sse_service
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False
    sse_service = None

# Import execution protection service
try:
    from services.execution_protection_service import get_execution_protection_service
    PROTECTION_AVAILABLE = True
except ImportError:
    PROTECTION_AVAILABLE = False

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
            
            # Handle execution protection integration
            if PROTECTION_AVAILABLE:
                self._handle_protection_integration(execution, current_status, new_status)
            
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
            
            # Broadcast status change via SSE if available
            self._broadcast_status_change(execution, new_status)
            
            logger.info(f"Updated execution {execution_id} status to {new_status.value}")
            return execution
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update execution status: {e}")
            raise
    
    def _handle_protection_integration(self, execution: Execution, old_status: ExecutionStatus, new_status: ExecutionStatus):
        """Handle execution protection service integration during status changes."""
        try:
            protection_service = get_execution_protection_service(self.db)
            
            # When execution finishes, release the lock
            if old_status in [ExecutionStatus.RUNNING, ExecutionStatus.PENDING] and \
               new_status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT]:
                
                success = protection_service.release_execution_lock(str(execution.graph_id), str(execution.id))
                if success:
                    logger.info(f"Released execution lock for graph {execution.graph_id} after execution {execution.id} finished")
                else:
                    logger.warning(f"Failed to release execution lock for graph {execution.graph_id} after execution {execution.id} finished")
            
            # When execution starts, ensure lock is acquired
            elif old_status == ExecutionStatus.PENDING and new_status == ExecutionStatus.RUNNING:
                success = protection_service.acquire_execution_lock(str(execution.graph_id), str(execution.id))
                if not success:
                    # This is a critical failure - should not happen if protection is working correctly
                    logger.error(f"Failed to acquire execution lock when starting execution {execution.id} for graph {execution.graph_id}")
                    raise RuntimeError("Failed to acquire execution lock during status transition")
                
        except Exception as e:
            logger.error(f"Error in protection service integration: {e}")
            # Don't fail the entire status update for protection issues, but log the error
    
    def _execute_callbacks(self, status: ExecutionStatus, execution: Execution):
        """Execute registered callbacks for status change."""
        if status in self._status_callbacks:
            for callback in self._status_callbacks[status]:
                try:
                    callback(execution)
                except Exception as e:
                    logger.error(f"Status callback failed: {e}")
    
    def _broadcast_status_change(self, execution: Execution, new_status: ExecutionStatus):
        """Broadcast status change via SSE if available."""
        if not SSE_AVAILABLE or not sse_service:
            return
        
        try:
            import asyncio
            
            # Get user_id from execution config (we need to extract it from the execution context)
            # For now, we'll try to get it from execution_config if available
            user_id = None
            execution_config = getattr(execution, 'execution_config', None)
            if execution_config and isinstance(execution_config, dict):
                user_id = execution_config.get('user_id')
            
            if not user_id:
                logger.warning(f"Cannot broadcast status change for execution {execution.id}: no user_id found")
                return
            
            asyncio.create_task(sse_service.broadcast_execution_event(
                "execution_status",
                str(user_id),
                {
                    "execution_id": str(execution.id),
                    "status": new_status,
                    "progress_percentage": execution.progress_percentage,
                    "current_step": execution.current_step,
                    "error_message": execution.error_message,
                    "result_data": execution.result_data if hasattr(execution, 'result_data') else None,
                    "user_id": str(user_id),
                    "graph_id": str(execution.graph_id) if hasattr(execution, 'graph_id') else None,
                    "thread_id": None  # Thread ID not available in current model
                }
            ))
        except Exception as e:
            logger.warning(f"Failed to broadcast status change via SSE: {e}")
    
    def get_execution_status(self, execution_id: UUID) -> Dict[str, Any]:
        """Get detailed execution status information."""
        execution = self.db.query(Execution).filter(Execution.id == str(execution_id)).first()
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        # Use getattr to safely access column values
        started_at = getattr(execution, 'started_at', None)
        completed_at = getattr(execution, 'completed_at', None)
        
        return {
            "id": execution.id,
            "status": execution.status,
            "progress_percentage": execution.progress_percentage,
            "current_step": execution.current_step,
            "started_at": started_at.isoformat() if started_at else None,
            "completed_at": completed_at.isoformat() if completed_at else None,
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
        query = self.db.query(Execution).filter(Execution.status == status.value)  # type: ignore[misc]
        
        if since:
            query = query.filter(Execution.created_at >= since)  # type: ignore[misc]
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_stuck_executions(self, timeout_minutes: int = 60) -> List[Execution]:
        """Find executions that have been running too long."""
        timeout_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        return self.db.query(Execution).filter(
            and_(
                Execution.status == ExecutionStatus.RUNNING.value,  # type: ignore[misc]
                Execution.started_at < timeout_threshold  # type: ignore[misc]
            )
        ).all()
    
    def timeout_stuck_executions(self, timeout_minutes: int = 60) -> List[str]:
        """Mark stuck executions as timed out."""
        stuck_executions = self.get_stuck_executions(timeout_minutes)
        timed_out = []
        
        for execution in stuck_executions:
            try:
                # Use getattr to safely access the id column value
                execution_id_str = getattr(execution, 'id', None)
                if execution_id_str:
                    self.update_execution_status(
                        UUID(execution_id_str),
                        ExecutionStatus.TIMEOUT,
                        error_message=f"Execution timed out after {timeout_minutes} minutes"
                    )
                    timed_out.append(execution_id_str)
            except Exception as e:
                execution_id_str = getattr(execution, 'id', 'unknown')
                logger.error(f"Failed to timeout execution {execution_id_str}: {e}")
        
        return timed_out
    
    def get_execution_statistics(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Get execution statistics."""
        query = self.db.query(Execution)
        
        if since:
            query = query.filter(Execution.created_at >= since)  # type: ignore[misc]
        
        executions = query.all()
        
        stats = {
            "total": len(executions),
            "by_status": {},
            "avg_duration": 0,
            "success_rate": 0
        }
        
        # Count by status - use getattr to safely access column values
        for status in ExecutionStatus:
            stats["by_status"][status.value] = sum(
                1 for e in executions 
                if getattr(e, 'status', None) == status.value
            )
        
        # Calculate averages - use getattr for safe column access
        completed = [
            e for e in executions 
            if (getattr(e, 'status', None) == ExecutionStatus.COMPLETED.value and 
                getattr(e, 'duration_seconds', None) is not None)
        ]
        if completed:
            duration_values = [getattr(e, 'duration_seconds', 0) for e in completed]
            stats["avg_duration"] = sum(duration_values) / len(duration_values)
        
        # Success rate - use getattr for safe column access
        finished = [
            e for e in executions 
            if getattr(e, 'status', None) in [ExecutionStatus.COMPLETED.value, ExecutionStatus.FAILED.value]
        ]
        if finished:
            successful = [
                e for e in finished 
                if getattr(e, 'status', None) == ExecutionStatus.COMPLETED.value
            ]
            stats["success_rate"] = len(successful) / len(finished)
        
        return stats
    
    def cancel_user_executions(self, user_id: UUID, reason: str = "User requested cancellation") -> List[str]:
        """Cancel all running executions for a user."""
        # Note: This would need a user_id field in Execution model
        # For now, we'll return empty list as the model doesn't have user_id field
        logger.warning("cancel_user_executions not implemented - Execution model needs user_id field")
        return []
    
    def cleanup_old_executions(self, days: int = 30) -> int:
        """Mark old completed/failed executions for cleanup."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_executions = self.db.query(Execution).filter(
            and_(
                Execution.completed_at < cutoff_date,  # type: ignore[misc]
                or_(
                    Execution.status == ExecutionStatus.COMPLETED.value,  # type: ignore[misc]
                    Execution.status == ExecutionStatus.FAILED.value,  # type: ignore[misc]
                    Execution.status == ExecutionStatus.CANCELLED.value  # type: ignore[misc]
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