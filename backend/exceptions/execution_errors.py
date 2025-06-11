"""
Execution Error Hierarchy and Classification

Defines specific error types for CrewAI execution with proper categorization
and error codes for consistent error handling and recovery strategies.
"""

from enum import Enum
from typing import Dict, Any, Optional


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    NETWORK = "network"
    VALIDATION = "validation"
    RESOURCE = "resource"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL = "internal"
    TIMEOUT = "timeout"
    CONFIGURATION = "configuration"
    PERMISSION = "permission"


class ExecutionErrorCode(str, Enum):
    """Specific error codes for execution failures."""
    # Network errors
    NETWORK_CONNECTION_FAILED = "E1001"
    NETWORK_TIMEOUT = "E1002"
    NETWORK_UNREACHABLE = "E1003"
    
    # Validation errors
    INVALID_GRAPH_STRUCTURE = "E2001"
    INVALID_INPUT_DATA = "E2002"
    MISSING_REQUIRED_FIELD = "E2003"
    INVALID_NODE_CONFIGURATION = "E2004"
    
    # Resource errors
    INSUFFICIENT_MEMORY = "E3001"
    INSUFFICIENT_DISK_SPACE = "E3002"
    CPU_LIMIT_EXCEEDED = "E3003"
    QUEUE_FULL = "E3004"
    
    # External service errors
    API_KEY_INVALID = "E4001"
    API_RATE_LIMITED = "E4002"
    EXTERNAL_SERVICE_UNAVAILABLE = "E4003"
    CREWAI_EXECUTION_FAILED = "E4004"
    
    # Internal errors
    DATABASE_CONNECTION_FAILED = "E5001"
    INTERNAL_SERVER_ERROR = "E5002"
    TASK_PROCESSING_FAILED = "E5003"
    
    # Timeout errors
    EXECUTION_TIMEOUT = "E6001"
    QUEUE_TIMEOUT = "E6002"
    
    # Configuration errors
    MISSING_CONFIGURATION = "E7001"
    INVALID_CONFIGURATION = "E7002"
    
    # Permission errors
    INSUFFICIENT_PERMISSIONS = "E8001"
    UNAUTHORIZED_ACCESS = "E8002"


class BaseExecutionError(Exception):
    """Base class for all execution errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ExecutionErrorCode,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        retry_recommended: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.recoverable = recoverable
        self.retry_recommended = retry_recommended
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        return {
            "message": self.message,
            "error_code": self.error_code.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "details": self.details,
            "recoverable": self.recoverable,
            "retry_recommended": self.retry_recommended
        }


class NetworkError(BaseExecutionError):
    """Network-related execution errors."""
    
    def __init__(self, message: str, error_code: ExecutionErrorCode, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            recoverable=True,
            retry_recommended=True
        )


class ValidationError(BaseExecutionError):
    """Validation-related execution errors."""
    
    def __init__(self, message: str, error_code: ExecutionErrorCode, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            details=details,
            recoverable=False,
            retry_recommended=False
        )


class ResourceError(BaseExecutionError):
    """Resource-related execution errors."""
    
    def __init__(self, message: str, error_code: ExecutionErrorCode, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.HIGH,
            details=details,
            recoverable=True,
            retry_recommended=True
        )


class ExternalServiceError(BaseExecutionError):
    """External service-related execution errors."""
    
    def __init__(self, message: str, error_code: ExecutionErrorCode, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            recoverable=True,
            retry_recommended=True
        )


class InternalError(BaseExecutionError):
    """Internal system execution errors."""
    
    def __init__(self, message: str, error_code: ExecutionErrorCode, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.CRITICAL,
            details=details,
            recoverable=True,
            retry_recommended=False
        )


class TimeoutError(BaseExecutionError):
    """Timeout-related execution errors."""
    
    def __init__(self, message: str, error_code: ExecutionErrorCode, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            details=details,
            recoverable=True,
            retry_recommended=True
        )


class ConfigurationError(BaseExecutionError):
    """Configuration-related execution errors."""
    
    def __init__(self, message: str, error_code: ExecutionErrorCode, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            details=details,
            recoverable=False,
            retry_recommended=False
        )


class PermissionError(BaseExecutionError):
    """Permission-related execution errors."""
    
    def __init__(self, message: str, error_code: ExecutionErrorCode, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.PERMISSION,
            severity=ErrorSeverity.HIGH,
            details=details,
            recoverable=False,
            retry_recommended=False
        )


# Specific error instances for common cases
class NetworkConnectionError(NetworkError):
    """Network connection failed."""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            "Network connection failed",
            ExecutionErrorCode.NETWORK_CONNECTION_FAILED,
            details
        )


class InvalidGraphError(ValidationError):
    """Invalid graph structure."""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            "Invalid graph structure",
            ExecutionErrorCode.INVALID_GRAPH_STRUCTURE,
            details
        )


class APIKeyInvalidError(ExternalServiceError):
    """Invalid API key for external service."""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            "Invalid or expired API key",
            ExecutionErrorCode.API_KEY_INVALID,
            details
        )


class CrewAIExecutionError(ExternalServiceError):
    """CrewAI execution failed."""
    
    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            "CrewAI execution failed",
            ExecutionErrorCode.CREWAI_EXECUTION_FAILED,
            details
        )


class ExecutionTimeoutError(TimeoutError):
    """Execution timed out."""
    
    def __init__(self, timeout_seconds: int, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["timeout_seconds"] = timeout_seconds
        super().__init__(
            f"Execution timed out after {timeout_seconds} seconds",
            ExecutionErrorCode.EXECUTION_TIMEOUT,
            details
        )


class InsufficientResourcesError(ResourceError):
    """Insufficient system resources."""
    
    def __init__(self, resource_type: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details["resource_type"] = resource_type
        super().__init__(
            f"Insufficient {resource_type} resources",
            ExecutionErrorCode.INSUFFICIENT_MEMORY,  # Default to memory, can be overridden
            details
        )


# Error factory for creating errors from error codes
def create_error_from_code(
    error_code: ExecutionErrorCode,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> BaseExecutionError:
    """Factory function to create appropriate error instance from error code."""
    
    # Map error codes to error classes
    error_mapping = {
        ExecutionErrorCode.NETWORK_CONNECTION_FAILED: NetworkConnectionError,
        ExecutionErrorCode.INVALID_GRAPH_STRUCTURE: InvalidGraphError,
        ExecutionErrorCode.API_KEY_INVALID: APIKeyInvalidError,
        ExecutionErrorCode.CREWAI_EXECUTION_FAILED: CrewAIExecutionError,
        ExecutionErrorCode.EXECUTION_TIMEOUT: ExecutionTimeoutError,
    }
    
    if error_code in error_mapping:
        return error_mapping[error_code](details)
    
    # Default to base error with appropriate category
    if error_code.value.startswith("E1"):
        category = ErrorCategory.NETWORK
        error_class = NetworkError
    elif error_code.value.startswith("E2"):
        category = ErrorCategory.VALIDATION
        error_class = ValidationError
    elif error_code.value.startswith("E3"):
        category = ErrorCategory.RESOURCE
        error_class = ResourceError
    elif error_code.value.startswith("E4"):
        category = ErrorCategory.EXTERNAL_SERVICE
        error_class = ExternalServiceError
    elif error_code.value.startswith("E5"):
        category = ErrorCategory.INTERNAL
        error_class = InternalError
    elif error_code.value.startswith("E6"):
        category = ErrorCategory.TIMEOUT
        error_class = TimeoutError
    elif error_code.value.startswith("E7"):
        category = ErrorCategory.CONFIGURATION
        error_class = ConfigurationError
    elif error_code.value.startswith("E8"):
        category = ErrorCategory.PERMISSION
        error_class = PermissionError
    else:
        error_class = BaseExecutionError
        category = ErrorCategory.INTERNAL
    
    if error_class == BaseExecutionError:
        return BaseExecutionError(
            message or f"Execution error: {error_code.value}",
            error_code,
            category,
            details=details
        )
    else:
        return error_class(
            message or f"Execution error: {error_code.value}",
            error_code,
            details
        ) 