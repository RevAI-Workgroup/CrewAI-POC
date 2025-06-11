"""
Tests for execution error handling service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
import time

from services.execution_error_service import (
    ExecutionErrorService, RetryConfig, CircuitBreaker
)
from exceptions.execution_errors import (
    BaseExecutionError, NetworkError, ValidationError, ResourceError,
    ErrorCategory, ErrorSeverity, ExecutionErrorCode, 
    NetworkConnectionError, InvalidGraphError
)
from models.execution import Execution, ExecutionStatus


class TestRetryConfig:
    """Test cases for RetryConfig."""
    
    def test_init_defaults(self):
        """Test RetryConfig initialization with defaults."""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
    
    def test_get_delay_exponential(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(base_delay=2.0, exponential_base=2.0, jitter=False)
        
        assert config.get_delay(0) == 2.0  # 2.0 * 2^0
        assert config.get_delay(1) == 4.0  # 2.0 * 2^1
        assert config.get_delay(2) == 8.0  # 2.0 * 2^2
    
    def test_get_delay_max_limit(self):
        """Test delay max limit enforcement."""
        config = RetryConfig(base_delay=10.0, max_delay=20.0, exponential_base=3.0, jitter=False)
        
        delay = config.get_delay(5)  # Would be 10 * 3^5 = 2430 without limit
        assert delay == 20.0
    
    def test_get_delay_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(base_delay=10.0, jitter=True)
        
        # Run multiple times to ensure jitter creates variation
        delays = [config.get_delay(1) for _ in range(10)]
        
        # Should have some variation due to jitter
        assert len(set(delays)) > 1
        # All delays should be positive
        assert all(d > 0 for d in delays)


class TestCircuitBreaker:
    """Test cases for CircuitBreaker."""
    
    def test_init_defaults(self):
        """Test CircuitBreaker initialization."""
        breaker = CircuitBreaker()
        
        assert breaker.failure_threshold == 5
        assert breaker.recovery_timeout == 60
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0
    
    def test_call_success(self):
        """Test successful call through circuit breaker."""
        breaker = CircuitBreaker()
        
        def test_func(x):
            return x * 2
        
        result = breaker.call(test_func, 5)
        
        assert result == 10
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0
    
    def test_call_failure_below_threshold(self):
        """Test failures below threshold."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        def failing_func():
            raise BaseExecutionError("Test error", ExecutionErrorCode.NETWORK_CONNECTION_FAILED, ErrorCategory.NETWORK)
        
        # Two failures should keep circuit closed
        for _ in range(2):
            with pytest.raises(BaseExecutionError):
                breaker.call(failing_func)
        
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 2
    
    def test_call_failure_opens_circuit(self):
        """Test that failures above threshold open circuit."""
        breaker = CircuitBreaker(failure_threshold=2)
        
        def failing_func():
            raise BaseExecutionError("Test error", ExecutionErrorCode.NETWORK_CONNECTION_FAILED, ErrorCategory.NETWORK)
        
        # Trigger failures to open circuit
        for _ in range(2):  # Only need 2 failures to meet threshold of 2
            with pytest.raises(BaseExecutionError):
                breaker.call(failing_func)
        
        assert breaker.state == "OPEN"
        assert breaker.failure_count == 2  # Should be 2, not 3
    
    def test_open_circuit_blocks_calls(self):
        """Test that open circuit blocks calls."""
        breaker = CircuitBreaker(failure_threshold=1)
        
        def failing_func():
            raise BaseExecutionError("Test error", ExecutionErrorCode.NETWORK_CONNECTION_FAILED, ErrorCategory.NETWORK)
        
        # Open the circuit
        with pytest.raises(BaseExecutionError):
            breaker.call(failing_func)
        
        # Next call should be blocked
        with pytest.raises(BaseExecutionError) as exc_info:
            breaker.call(failing_func)
        
        assert "Circuit breaker is OPEN" in str(exc_info.value)
    
    def test_circuit_recovery(self):
        """Test circuit breaker recovery after timeout."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=1)  # Use int instead of float
        
        def failing_func():
            raise BaseExecutionError("Test error", ExecutionErrorCode.NETWORK_CONNECTION_FAILED, ErrorCategory.NETWORK)
        
        def success_func():
            return "success"
        
        # Open the circuit
        with pytest.raises(BaseExecutionError):
            breaker.call(failing_func)
        
        assert breaker.state == "OPEN"
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Next call should transition to HALF_OPEN and succeed
        result = breaker.call(success_func)
        
        assert result == "success"
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0


class TestExecutionErrorService:
    """Test cases for ExecutionErrorService."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_db = Mock()
        self.service = ExecutionErrorService(self.mock_db)
        self.execution_id = uuid4()
    
    def test_classify_error_base_execution_error(self):
        """Test classification of BaseExecutionError."""
        error = NetworkConnectionError({"source": "test"})
        
        classified = self.service.classify_error(error)
        
        assert classified == error
        assert isinstance(classified, BaseExecutionError)
    
    def test_classify_error_connection_error(self):
        """Test classification of ConnectionError."""
        error = ConnectionError("Network failed")
        
        classified = self.service.classify_error(error)
        
        assert isinstance(classified, NetworkError)
        assert classified.error_code == ExecutionErrorCode.NETWORK_CONNECTION_FAILED
        assert classified.category == ErrorCategory.NETWORK
    
    def test_classify_error_value_error(self):
        """Test classification of ValueError."""
        error = ValueError("Invalid input")
        
        classified = self.service.classify_error(error)
        
        assert isinstance(classified, ValidationError)
        assert classified.error_code == ExecutionErrorCode.INVALID_INPUT_DATA
        assert classified.category == ErrorCategory.VALIDATION
    
    def test_classify_error_memory_error(self):
        """Test classification of MemoryError."""
        error = MemoryError("Out of memory")
        
        classified = self.service.classify_error(error)
        
        assert isinstance(classified, ResourceError)
        assert classified.error_code == ExecutionErrorCode.INSUFFICIENT_MEMORY
        assert classified.category == ErrorCategory.RESOURCE
    
    def test_classify_error_generic_exception(self):
        """Test classification of generic Exception."""
        error = Exception("Unknown error")
        
        classified = self.service.classify_error(error)
        
        assert isinstance(classified, BaseExecutionError)
        assert classified.error_code == ExecutionErrorCode.INTERNAL_SERVER_ERROR
        assert classified.category == ErrorCategory.INTERNAL
    
    def test_handle_execution_error_no_retry(self):
        """Test error handling when retry is not recommended."""
        error = ValidationError("Invalid data", ExecutionErrorCode.INVALID_INPUT_DATA)
        
        # Setup mock execution
        mock_execution = Mock(spec=Execution)
        self.service.status_service = Mock()
        self.service.status_service.update_execution_status = Mock()
        
        # Execute
        result = self.service.handle_execution_error(self.execution_id, error, attempt=1)
        
        # Verify
        assert result["should_retry"] is False
        assert result["retry_delay"] == 0
        assert result["attempt"] == 1
        assert result["error"]["category"] == ErrorCategory.VALIDATION.value
        
        # Verify status service was called
        self.service.status_service.update_execution_status.assert_called_once()
    
    def test_handle_execution_error_with_retry(self):
        """Test error handling when retry is recommended."""
        error = NetworkConnectionError({"source": "test"})
        
        # Setup mock execution
        self.service.status_service = Mock()
        self.service.status_service.update_execution_status = Mock()
        
        # Execute
        result = self.service.handle_execution_error(self.execution_id, error, attempt=1)
        
        # Verify
        assert result["should_retry"] is True
        assert result["retry_delay"] > 0
        assert result["next_attempt"] == 2
        assert result["error"]["category"] == ErrorCategory.NETWORK.value
    
    def test_handle_execution_error_max_retries_exceeded(self):
        """Test error handling when max retries exceeded."""
        error = NetworkConnectionError({"source": "test"})
        
        # Setup mock execution
        self.service.status_service = Mock()
        self.service.status_service.update_execution_status = Mock()
        
        # Execute with attempt beyond max retries
        result = self.service.handle_execution_error(self.execution_id, error, attempt=5)
        
        # Verify
        assert result["should_retry"] is False
        assert result["retry_delay"] == 0
    
    def test_register_error_callback(self):
        """Test registering error callbacks."""
        callback = Mock()
        
        # Register callback
        self.service.register_error_callback(ErrorCategory.NETWORK, callback)
        
        # Verify callback is registered
        assert ErrorCategory.NETWORK in self.service.error_callbacks
        assert callback in self.service.error_callbacks[ErrorCategory.NETWORK]
    
    def test_execute_error_callbacks(self):
        """Test execution of error callbacks."""
        callback1 = Mock()
        callback2 = Mock()
        error = NetworkConnectionError()
        
        # Register callbacks
        self.service.register_error_callback(ErrorCategory.NETWORK, callback1)
        self.service.register_error_callback(ErrorCategory.NETWORK, callback2)
        
        # Execute callbacks
        self.service._execute_error_callbacks(error)
        
        # Verify callbacks were called
        callback1.assert_called_once_with(error)
        callback2.assert_called_once_with(error)
    
    def test_recover_execution_restart(self):
        """Test execution recovery with restart strategy."""
        # Setup mock execution
        mock_execution = Mock(spec=Execution)
        mock_execution.status = ExecutionStatus.FAILED.value
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_execution
        self.service.status_service = Mock()
        self.service.status_service.update_execution_status = Mock()
        
        # Execute
        result = self.service.recover_execution(self.execution_id, "restart")
        
        # Verify
        assert result["status"] == "recovered"
        assert result["strategy"] == "restart"
        
        # Verify status was updated to pending
        self.service.status_service.update_execution_status.assert_called_once_with(
            self.execution_id,
            ExecutionStatus.PENDING,
            error_message="Execution reset for recovery"
        )
    
    def test_recover_execution_not_failed(self):
        """Test recovery of execution that is not failed."""
        # Setup mock execution
        mock_execution = Mock(spec=Execution)
        mock_execution.status = ExecutionStatus.RUNNING.value
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_execution
        
        # Execute and verify exception
        with pytest.raises(ValueError) as exc_info:
            self.service.recover_execution(self.execution_id, "restart")
        
        assert "not in failed state" in str(exc_info.value)
    
    def test_recover_execution_not_found(self):
        """Test recovery of non-existent execution."""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute and verify exception
        with pytest.raises(ValueError) as exc_info:
            self.service.recover_execution(self.execution_id, "restart")
        
        assert "not found" in str(exc_info.value)
    
    def test_get_circuit_breaker(self):
        """Test getting circuit breaker for service."""
        # Get circuit breaker for new service
        breaker1 = self.service.get_circuit_breaker("test_service")
        
        assert isinstance(breaker1, CircuitBreaker)
        assert breaker1.state == "CLOSED"
        
        # Get same circuit breaker again
        breaker2 = self.service.get_circuit_breaker("test_service")
        
        assert breaker1 is breaker2
    
    def test_configure_retry_policy(self):
        """Test configuring retry policy."""
        new_config = RetryConfig(max_retries=5, base_delay=3.0)
        
        # Configure new policy
        self.service.configure_retry_policy(ErrorCategory.NETWORK, new_config)
        
        # Verify policy was updated
        assert self.service.retry_configs[ErrorCategory.NETWORK] == new_config
        assert self.service.retry_configs[ErrorCategory.NETWORK].max_retries == 5
    
    def test_get_error_statistics(self):
        """Test getting error statistics."""
        # Setup mock failed executions
        mock_executions = []
        for i in range(5):
            exec_mock = Mock()
            exec_mock.error_details = {
                "category": ErrorCategory.NETWORK.value if i < 3 else ErrorCategory.VALIDATION.value,
                "severity": ErrorSeverity.MEDIUM.value,
                "error_code": ExecutionErrorCode.NETWORK_CONNECTION_FAILED.value,
                "recoverable": True if i < 3 else False
            }
            mock_executions.append(exec_mock)
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_executions
        
        # Execute
        stats = self.service.get_error_statistics()
        
        # Verify
        assert stats["total_failures"] == 5
        assert stats["by_category"][ErrorCategory.NETWORK.value] == 3
        assert stats["by_category"][ErrorCategory.VALIDATION.value] == 2
        assert stats["recovery_candidates"] == 3
    
    def test_cleanup_circuit_breakers(self):
        """Test circuit breaker cleanup."""
        # Create circuit breakers in different states
        breaker1 = self.service.get_circuit_breaker("service1")
        breaker2 = self.service.get_circuit_breaker("service2")
        
        # Set breaker1 to OPEN with old failure time
        breaker1.state = "OPEN"
        breaker1.last_failure_time = time.time() - 200  # Old failure
        
        # Set breaker2 to OPEN with recent failure time
        breaker2.state = "OPEN"
        breaker2.last_failure_time = time.time() - 30  # Recent failure
        
        # Execute cleanup
        self.service.cleanup_circuit_breakers()
        
        # Verify only old breaker was reset
        assert breaker1.state == "CLOSED"
        assert breaker1.failure_count == 0
        assert breaker2.state == "OPEN"  # Should remain open
    
    def test_get_failed_executions_for_recovery(self):
        """Test getting failed executions for recovery."""
        mock_executions = [Mock(), Mock()]
        
        self.mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = mock_executions
        
        # Execute
        executions = self.service.get_failed_executions_for_recovery(limit=10, min_age_minutes=5)
        
        # Verify
        assert executions == mock_executions
        self.mock_db.query.return_value.filter.assert_called()


class TestExecutionErrorIntegration:
    """Integration tests for execution error service."""
    
    @pytest.mark.integration
    def test_error_handling_workflow(self):
        """Test complete error handling workflow."""
        # This would require actual database setup
        pytest.skip("Integration test requires database setup") 