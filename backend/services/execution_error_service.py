"""
Execution Error Handling Service

Centralized service for error handling, retry logic, and recovery strategies
for CrewAI execution failures.
"""

import logging
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Type
from uuid import UUID

from sqlalchemy.orm import Session

from exceptions.execution_errors import (
    BaseExecutionError, ErrorCategory, ErrorSeverity,
    NetworkError, ValidationError, ResourceError, ExternalServiceError,
    InternalError, TimeoutError, ConfigurationError, PermissionError,
    ExecutionErrorCode, create_error_from_code
)
from models.execution import Execution, ExecutionStatus
from services.execution_status_service import ExecutionStatusService
from db_config import SessionLocal

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry logic."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # Add random jitter ±25%
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


class CircuitBreaker:
    """Circuit breaker for external service failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = BaseExecutionError
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise ExternalServiceError(
                    "Circuit breaker is OPEN",
                    ExecutionErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
                    {"circuit_breaker_state": self.state}
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class ExecutionErrorService:
    """Service for centralized execution error handling."""
    
    # Default retry configurations by error category
    DEFAULT_RETRY_CONFIGS = {
        ErrorCategory.NETWORK: RetryConfig(max_retries=3, base_delay=2.0),
        ErrorCategory.EXTERNAL_SERVICE: RetryConfig(max_retries=5, base_delay=1.0),
        ErrorCategory.RESOURCE: RetryConfig(max_retries=3, base_delay=5.0),
        ErrorCategory.TIMEOUT: RetryConfig(max_retries=2, base_delay=10.0),
        ErrorCategory.INTERNAL: RetryConfig(max_retries=1, base_delay=5.0),
        ErrorCategory.VALIDATION: RetryConfig(max_retries=0),  # Don't retry validation errors
        ErrorCategory.CONFIGURATION: RetryConfig(max_retries=0),  # Don't retry config errors
        ErrorCategory.PERMISSION: RetryConfig(max_retries=0),  # Don't retry permission errors
    }
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()
        self.status_service = ExecutionStatusService(self.db)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_callbacks: Dict[ErrorCategory, List[Callable]] = {}
        self.retry_configs: Dict[ErrorCategory, RetryConfig] = self.DEFAULT_RETRY_CONFIGS.copy()
    
    def register_error_callback(self, category: ErrorCategory, callback: Callable):
        """Register callback for specific error category."""
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]
    
    def classify_error(self, exception: Exception) -> BaseExecutionError:
        """Classify and convert generic exceptions to execution errors."""
        if isinstance(exception, BaseExecutionError):
            return exception
        
        # Map common Python exceptions to execution errors
        error_msg = str(exception)
        
        if isinstance(exception, ConnectionError):
            return NetworkError(
                f"Network connection error: {error_msg}",
                ExecutionErrorCode.NETWORK_CONNECTION_FAILED,
                {"original_exception": type(exception).__name__}
            )
        elif isinstance(exception, TimeoutError):
            return TimeoutError(
                f"Operation timed out: {error_msg}",
                ExecutionErrorCode.EXECUTION_TIMEOUT,
                {"original_exception": type(exception).__name__}
            )
        elif isinstance(exception, ValueError):
            return ValidationError(
                f"Validation error: {error_msg}",
                ExecutionErrorCode.INVALID_INPUT_DATA,
                {"original_exception": type(exception).__name__}
            )
        elif isinstance(exception, MemoryError):
            return ResourceError(
                f"Memory error: {error_msg}",
                ExecutionErrorCode.INSUFFICIENT_MEMORY,
                {"original_exception": type(exception).__name__}
            )
        elif isinstance(exception, PermissionError):
            return PermissionError(
                f"Permission error: {error_msg}",
                ExecutionErrorCode.INSUFFICIENT_PERMISSIONS,
                {"original_exception": type(exception).__name__}
            )
        else:
            return InternalError(
                f"Internal error: {error_msg}",
                ExecutionErrorCode.INTERNAL_SERVER_ERROR,
                {"original_exception": type(exception).__name__}
            )
    
    def handle_execution_error(
        self,
        execution_id: UUID,
        error: Exception,
        attempt: int = 1
    ) -> Dict[str, Any]:
        """Handle execution error with retry logic and recovery."""
        
        # Classify the error
        exec_error = self.classify_error(error)
        
        # Execute error callbacks
        self._execute_error_callbacks(exec_error)
        
        # Log the error
        logger.error(
            f"Execution {execution_id} failed (attempt {attempt}): {exec_error.message}",
            extra={
                "execution_id": str(execution_id),
                "error_code": exec_error.error_code.value,
                "category": exec_error.category.value,
                "severity": exec_error.severity.value,
                "attempt": attempt
            }
        )
        
        # Update execution status
        try:
            self.status_service.update_execution_status(
                execution_id,
                ExecutionStatus.FAILED,
                error_message=exec_error.message,
                error_details=exec_error.to_dict()
            )
        except Exception as e:
            logger.error(f"Failed to update execution status: {e}")
        
        # Determine if retry is recommended
        retry_config = self.retry_configs.get(exec_error.category)
        should_retry = (
            exec_error.retry_recommended and
            retry_config and
            attempt <= retry_config.max_retries
        )
        
        result = {
            "error": exec_error.to_dict(),
            "execution_id": str(execution_id),
            "attempt": attempt,
            "should_retry": should_retry,
            "retry_delay": 0
        }
        
        if should_retry:
            delay = retry_config.get_delay(attempt - 1)
            result["retry_delay"] = delay
            result["next_attempt"] = attempt + 1
            
            logger.info(
                f"Scheduling retry for execution {execution_id} in {delay:.2f} seconds "
                f"(attempt {attempt + 1}/{retry_config.max_retries + 1})"
            )
        else:
            logger.info(f"No retry scheduled for execution {execution_id}")
        
        return result
    
    def _execute_error_callbacks(self, error: BaseExecutionError):
        """Execute registered callbacks for error category."""
        if error.category in self.error_callbacks:
            for callback in self.error_callbacks[error.category]:
                try:
                    callback(error)
                except Exception as e:
                    logger.error(f"Error callback failed: {e}")
    
    def recover_execution(
        self,
        execution_id: UUID,
        recovery_strategy: str = "restart"
    ) -> Dict[str, Any]:
        """Attempt to recover failed execution."""
        
        execution = self.db.query(Execution).filter(Execution.id == str(execution_id)).first()
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        if execution.status != ExecutionStatus.FAILED.value:
            raise ValueError(f"Execution {execution_id} is not in failed state")
        
        logger.info(f"Attempting recovery for execution {execution_id} using strategy: {recovery_strategy}")
        
        if recovery_strategy == "restart":
            # Reset execution to pending for retry
            try:
                self.status_service.update_execution_status(
                    execution_id,
                    ExecutionStatus.PENDING,
                    error_message="Execution reset for recovery"
                )
                return {
                    "status": "recovered",
                    "strategy": recovery_strategy,
                    "execution_id": str(execution_id)
                }
            except Exception as e:
                logger.error(f"Recovery failed for execution {execution_id}: {e}")
                return {
                    "status": "recovery_failed",
                    "error": str(e),
                    "execution_id": str(execution_id)
                }
        
        return {
            "status": "recovery_not_supported",
            "strategy": recovery_strategy,
            "execution_id": str(execution_id)
        }
    
    def get_error_statistics(self, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        query = self.db.query(Execution).filter(Execution.status == ExecutionStatus.FAILED.value)
        
        if since:
            query = query.filter(Execution.created_at >= since)
        
        failed_executions = query.all()
        
        stats = {
            "total_failures": len(failed_executions),
            "by_category": {},
            "by_severity": {},
            "by_error_code": {},
            "recovery_candidates": 0
        }
        
        for execution in failed_executions:
            if execution.error_details:
                category = execution.error_details.get("category", "unknown")
                severity = execution.error_details.get("severity", "unknown")
                error_code = execution.error_details.get("error_code", "unknown")
                recoverable = execution.error_details.get("recoverable", False)
                
                # Count by category
                stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
                
                # Count by severity
                stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
                
                # Count by error code
                stats["by_error_code"][error_code] = stats["by_error_code"].get(error_code, 0) + 1
                
                # Count recovery candidates
                if recoverable:
                    stats["recovery_candidates"] += 1
        
        return stats
    
    def cleanup_circuit_breakers(self):
        """Reset circuit breakers that have been open for too long."""
        current_time = time.time()
        
        for service_name, breaker in self.circuit_breakers.items():
            if (breaker.state == "OPEN" and 
                breaker.last_failure_time and 
                current_time - breaker.last_failure_time > breaker.recovery_timeout * 2):
                
                logger.info(f"Resetting circuit breaker for service: {service_name}")
                breaker.state = "CLOSED"
                breaker.failure_count = 0
                breaker.last_failure_time = None
    
    def configure_retry_policy(self, category: ErrorCategory, config: RetryConfig):
        """Configure retry policy for specific error category."""
        self.retry_configs[category] = config
        logger.info(f"Updated retry policy for {category.value}: max_retries={config.max_retries}")
    
    def get_failed_executions_for_recovery(
        self,
        limit: int = 50,
        min_age_minutes: int = 5
    ) -> List[Execution]:
        """Get failed executions that are candidates for recovery."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=min_age_minutes)
        
        return self.db.query(Execution).filter(
            Execution.status == ExecutionStatus.FAILED.value,
            Execution.completed_at < cutoff_time
        ).limit(limit).all()
    
    def close(self):
        """Close database session."""
        if self.db:
            self.db.close() 