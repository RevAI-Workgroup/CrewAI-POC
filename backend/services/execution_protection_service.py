"""
Execution Protection Service

Service to prevent concurrent crew executions for the same graph.
Ensures only one crew runs at a time per graph to avoid resource conflicts.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set, Any
from threading import RLock
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.execution import Execution, ExecutionStatus
from models.graph import Graph
from db_config import SessionLocal

logger = logging.getLogger(__name__)


class ConcurrentExecutionError(Exception):
    """Raised when attempting to start a concurrent execution for the same graph."""
    pass


class ExecutionProtectionService:
    """Service for managing execution protection and preventing concurrent runs."""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()
        self._protection_lock = RLock()  # Thread-safe lock for service operations
        self._active_executions: Dict[str, str] = {}  # graph_id -> execution_id mapping
        self._timeout_minutes = 60  # Default timeout for stuck executions
    
    def can_start_execution(self, graph_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if a new execution can be started for the given graph.
        
        Returns:
            tuple: (can_start: bool, blocking_execution_id: Optional[str])
        """
        with self._protection_lock:
            try:
                # First check in-memory tracking
                if graph_id in self._active_executions:
                    blocking_execution_id = self._active_executions[graph_id]
                    # Verify the execution is still actually running
                    if self._is_execution_actually_running(blocking_execution_id):
                        return False, blocking_execution_id
                    else:
                        # Clean up stale tracking
                        del self._active_executions[graph_id]
                
                # Check database for any running executions
                running_execution = self._get_running_execution(graph_id)
                if running_execution:
                    # Update in-memory tracking
                    execution_id_str = str(running_execution.id)
                    self._active_executions[graph_id] = execution_id_str
                    return False, execution_id_str
                
                return True, None
                
            except Exception as e:
                logger.error(f"Error checking execution protection for graph {graph_id}: {e}")
                # Default to safe behavior - don't allow if unsure
                return False, None
    
    def acquire_execution_lock(self, graph_id: str, execution_id: str) -> bool:
        """
        Acquire execution lock for a graph.
        
        Args:
            graph_id: The graph ID to lock
            execution_id: The execution ID acquiring the lock
            
        Returns:
            bool: True if lock acquired successfully, False otherwise
        """
        with self._protection_lock:
            try:
                can_start, blocking_id = self.can_start_execution(graph_id)
                
                if not can_start:
                    logger.warning(f"Cannot acquire lock for graph {graph_id}: blocked by execution {blocking_id}")
                    return False
                
                # Acquire the lock
                self._active_executions[graph_id] = execution_id
                logger.info(f"Acquired execution lock for graph {graph_id} by execution {execution_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error acquiring execution lock: {e}")
                return False
    
    def release_execution_lock(self, graph_id: str, execution_id: str) -> bool:
        """
        Release execution lock for a graph.
        
        Args:
            graph_id: The graph ID to unlock
            execution_id: The execution ID releasing the lock
            
        Returns:
            bool: True if lock released successfully, False otherwise
        """
        with self._protection_lock:
            try:
                if graph_id not in self._active_executions:
                    logger.warning(f"No active execution lock found for graph {graph_id}")
                    return True  # Already unlocked
                
                if self._active_executions[graph_id] != execution_id:
                    logger.warning(f"Execution {execution_id} cannot release lock for graph {graph_id} - owned by {self._active_executions[graph_id]}")
                    return False
                
                # Release the lock
                del self._active_executions[graph_id]
                logger.info(f"Released execution lock for graph {graph_id} by execution {execution_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error releasing execution lock: {e}")
                return False
    
    def validate_execution_start(self, graph_id: str, execution_id: str) -> None:
        """
        Validate that an execution can start and acquire lock.
        
        Raises:
            ConcurrentExecutionError: If execution cannot start due to concurrent execution
            ValueError: If validation parameters are invalid
        """
        if not graph_id or not execution_id:
            raise ValueError("Graph ID and Execution ID are required")
        
        # Verify graph exists and is valid
        graph = self.db.query(Graph).filter(Graph.id == graph_id).first()
        if not graph:
            raise ValueError(f"Graph {graph_id} not found")
        
        # Check if execution can start
        can_start, blocking_id = self.can_start_execution(graph_id)
        if not can_start:
            blocking_execution = self.db.query(Execution).filter(Execution.id == blocking_id).first()
            if blocking_execution:
                started_at = getattr(blocking_execution, 'started_at', None)
                created_at = getattr(blocking_execution, 'created_at', None)
                timestamp = started_at or created_at
                error_msg = (f"Cannot start execution for graph {graph_id}: "
                           f"Another execution ({blocking_id}) is already running since "
                           f"{timestamp}")
            else:
                error_msg = f"Cannot start execution for graph {graph_id}: Another execution is already running"
            
            raise ConcurrentExecutionError(error_msg)
        
        # Try to acquire lock
        if not self.acquire_execution_lock(graph_id, execution_id):
            raise ConcurrentExecutionError(f"Failed to acquire execution lock for graph {graph_id}")
    
    def cleanup_orphaned_locks(self) -> int:
        """
        Clean up orphaned execution locks where executions are no longer running.
        
        Returns:
            int: Number of locks cleaned up
        """
        cleaned_count = 0
        
        with self._protection_lock:
            try:
                graphs_to_cleanup = []
                
                for graph_id, execution_id in self._active_executions.items():
                    if not self._is_execution_actually_running(execution_id):
                        graphs_to_cleanup.append(graph_id)
                
                for graph_id in graphs_to_cleanup:
                    execution_id = self._active_executions[graph_id]
                    del self._active_executions[graph_id]
                    cleaned_count += 1
                    logger.info(f"Cleaned up orphaned lock for graph {graph_id} (execution {execution_id})")
                
                # Also check for database executions that should be timed out
                timeout_threshold = datetime.utcnow() - timedelta(minutes=self._timeout_minutes)
                stuck_executions = self.db.query(Execution).filter(
                    and_(
                        Execution.status.in_([ExecutionStatus.RUNNING.value, ExecutionStatus.PENDING.value]),  # type: ignore[misc]
                        Execution.started_at < timeout_threshold  # type: ignore[misc]
                    )
                ).all()
                
                for execution in stuck_executions:
                    execution.set_status(ExecutionStatus.TIMEOUT)
                    logger.warning(f"Timed out stuck execution {execution.id} for graph {execution.graph_id}")
                
                if stuck_executions:
                    self.db.commit()
                    cleaned_count += len(stuck_executions)
                
                if cleaned_count > 0:
                    logger.info(f"Cleaned up {cleaned_count} orphaned/stuck executions")
                
                return cleaned_count
                
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
                self.db.rollback()
                return 0
    
    def get_active_executions(self) -> Dict[str, str]:
        """Get currently tracked active executions."""
        with self._protection_lock:
            return self._active_executions.copy()
    
    def get_execution_info(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about current execution for a graph.
        
        Returns:
            dict: Execution information or None if no active execution
        """
        running_execution = self._get_running_execution(graph_id)
        if not running_execution:
            return None
        
        return {
            'execution_id': str(running_execution.id),
            'status': running_execution.status,
            'started_at': getattr(running_execution, 'started_at', None),
            'progress_percentage': getattr(running_execution, 'progress_percentage', 0),
            'current_step': getattr(running_execution, 'current_step', None)
        }
    
    def _get_running_execution(self, graph_id: str) -> Optional[Execution]:
        """Get currently running execution for a graph from database."""
        return self.db.query(Execution).filter(
            and_(
                Execution.graph_id == graph_id,
                Execution.status.in_([ExecutionStatus.RUNNING.value, ExecutionStatus.PENDING.value])  # type: ignore[misc]
            )
        ).order_by(Execution.created_at.desc()).first()
    
    def _is_execution_actually_running(self, execution_id: str) -> bool:
        """Check if execution is actually still running in database."""
        execution = self.db.query(Execution).filter(Execution.id == execution_id).first()
        if not execution:
            return False
        
        return execution.status in [ExecutionStatus.RUNNING.value, ExecutionStatus.PENDING.value]
    
    def set_timeout_minutes(self, timeout_minutes: int) -> None:
        """Set the timeout for stuck executions."""
        if timeout_minutes <= 0:
            raise ValueError("Timeout must be positive")
        self._timeout_minutes = timeout_minutes
        logger.info(f"Set execution timeout to {timeout_minutes} minutes")
    
    def close(self):
        """Close the service and clean up resources."""
        with self._protection_lock:
            self._active_executions.clear()
        
        if hasattr(self, 'db') and self.db:
            self.db.close()


# Global service instance
_protection_service: Optional[ExecutionProtectionService] = None


def get_execution_protection_service(db: Optional[Session] = None) -> ExecutionProtectionService:
    """Get or create the global execution protection service instance."""
    global _protection_service
    
    if _protection_service is None:
        _protection_service = ExecutionProtectionService(db)
    
    return _protection_service 