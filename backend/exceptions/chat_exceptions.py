"""
Chat-specific exceptions for error handling in chat streaming functionality.
Extends the base execution error system with chat-specific error types.
"""

import logging
from typing import Dict, Any, Optional
from .execution_errors import (
    BaseExecutionError, ErrorCategory, ErrorSeverity, ExecutionErrorCode,
    ValidationError, ExternalServiceError, InternalError, TimeoutError
)

logger = logging.getLogger(__name__)


class ChatErrorCode:
    """Chat-specific error codes extending ExecutionErrorCode."""
    # Graph Translation Errors
    GRAPH_STRUCTURE_INVALID = "C1001"
    AGENT_CONFIG_MISSING = "C1002"
    TASK_CONFIG_INVALID = "C1003"
    CREW_CONFIG_INVALID = "C1004"
    NODE_RELATIONSHIP_BROKEN = "C1005"
    MULTIPLE_CREWS_DETECTED = "C1006"
    
    # CrewAI Execution Errors
    CREWAI_AGENT_FAILED = "C2001"
    CREWAI_TASK_FAILED = "C2002"
    CREWAI_EXECUTION_TIMEOUT = "C2003"
    CREWAI_MEMORY_ERROR = "C2004"
    CREWAI_TOOL_ERROR = "C2005"
    
    # Streaming Errors
    STREAM_CONNECTION_LOST = "C3001"
    STREAM_PARTIAL_FAILURE = "C3002"
    STREAM_TIMEOUT = "C3003"
    STREAM_ENCODING_ERROR = "C3004"
    
    # Chat Context Errors
    THREAD_NOT_ACCESSIBLE = "C4001"
    MESSAGE_PROCESSING_FAILED = "C4002"
    EXECUTION_ALREADY_RUNNING = "C4003"
    DYNAMIC_TASK_CREATION_FAILED = "C4004"


class ChatError(BaseExecutionError):
    """Base class for chat-specific errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        retry_recommended: bool = False,
        user_message: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code=ExecutionErrorCode.INTERNAL_SERVER_ERROR,  # Fallback to existing enum
            category=category,
            severity=severity,
            details=details or {},
            recoverable=recoverable,
            retry_recommended=retry_recommended
        )
        self.chat_error_code = error_code
        self.user_message = user_message or self._generate_user_message()
    
    def _generate_user_message(self) -> str:
        """Generate user-friendly error message."""
        return "An error occurred while processing your chat message. Please try again."
    
    def to_dict(self) -> Dict[str, Any]:
        """Extend base dict with chat-specific fields."""
        data = super().to_dict()
        data.update({
            "chat_error_code": self.chat_error_code,
            "user_message": self.user_message
        })
        return data


class GraphTranslationError(ChatError):
    """Graph translation specific errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        graph_id: Optional[str] = None,
        node_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            details={
                "graph_id": graph_id,
                "node_id": node_id,
                **(details or {})
            },
            recoverable=False,
            retry_recommended=False
        )
    
    def _generate_user_message(self) -> str:
        if self.chat_error_code == ChatErrorCode.MULTIPLE_CREWS_DETECTED:
            return "This graph has multiple crews. Chat functionality requires exactly one crew."
        elif self.chat_error_code == ChatErrorCode.AGENT_CONFIG_MISSING:
            return "The graph configuration is incomplete. Please check agent settings."
        elif self.chat_error_code == ChatErrorCode.TASK_CONFIG_INVALID:
            return "The graph tasks are not properly configured for chat."
        else:
            return "The graph structure is not compatible with chat functionality."


class CrewExecutionError(ChatError):
    """CrewAI execution specific errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        execution_id: Optional[str] = None,
        crew_stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.MEDIUM,
            details={
                "execution_id": execution_id,
                "crew_stage": crew_stage,
                **(details or {})
            },
            recoverable=True,
            retry_recommended=True
        )
    
    def _generate_user_message(self) -> str:
        if self.chat_error_code == ChatErrorCode.CREWAI_EXECUTION_TIMEOUT:
            return "The AI crew took too long to respond. Please try with a simpler request."
        elif self.chat_error_code == ChatErrorCode.CREWAI_AGENT_FAILED:
            return "One of the AI agents encountered an error. Please try again."
        elif self.chat_error_code == ChatErrorCode.CREWAI_TOOL_ERROR:
            return "A tool used by the AI crew failed. Please check your configuration."
        else:
            return "The AI crew execution failed. Please try again or simplify your request."


class StreamingError(ChatError):
    """Streaming response specific errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        thread_id: Optional[str] = None,
        message_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            details={
                "thread_id": thread_id,
                "message_id": message_id,
                **(details or {})
            },
            recoverable=True,
            retry_recommended=True
        )
    
    def _generate_user_message(self) -> str:
        if self.chat_error_code == ChatErrorCode.STREAM_CONNECTION_LOST:
            return "Connection lost while streaming response. Please refresh and try again."
        elif self.chat_error_code == ChatErrorCode.STREAM_PARTIAL_FAILURE:
            return "Partial response received. You may have a partial answer above."
        else:
            return "Streaming response failed. Please try again."


class ChatContextError(ChatError):
    """Chat context and setup specific errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        thread_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            category=ErrorCategory.PERMISSION,
            severity=ErrorSeverity.HIGH,
            details={
                "thread_id": thread_id,
                "user_id": user_id,
                **(details or {})
            },
            recoverable=False,
            retry_recommended=False
        )
    
    def _generate_user_message(self) -> str:
        if self.chat_error_code == ChatErrorCode.THREAD_NOT_ACCESSIBLE:
            return "You don't have access to this chat thread."
        elif self.chat_error_code == ChatErrorCode.EXECUTION_ALREADY_RUNNING:
            return "A crew is already running for this graph. Please wait for it to complete."
        else:
            return "Unable to access chat. Please check your permissions."


# Convenience functions for creating specific errors
def create_graph_structure_error(graph_id: str, details: Optional[Dict] = None) -> GraphTranslationError:
    """Create a graph structure validation error."""
    return GraphTranslationError(
        message=f"Graph {graph_id} has invalid structure for chat",
        error_code=ChatErrorCode.GRAPH_STRUCTURE_INVALID,
        graph_id=graph_id,
        details=details
    )


def create_multiple_crews_error(graph_id: str, crew_count: int) -> GraphTranslationError:
    """Create error for multiple crews detected."""
    return GraphTranslationError(
        message=f"Graph {graph_id} has {crew_count} crews, but chat requires exactly 1",
        error_code=ChatErrorCode.MULTIPLE_CREWS_DETECTED,
        graph_id=graph_id,
        details={"crew_count": crew_count}
    )


def create_agent_config_error(graph_id: str, node_id: str, missing_fields: list) -> GraphTranslationError:
    """Create error for missing agent configuration."""
    return GraphTranslationError(
        message=f"Agent {node_id} in graph {graph_id} missing required fields: {missing_fields}",
        error_code=ChatErrorCode.AGENT_CONFIG_MISSING,
        graph_id=graph_id,
        node_id=node_id,
        details={"missing_fields": missing_fields}
    )


def create_crew_execution_error(execution_id: str, original_error: Exception) -> CrewExecutionError:
    """Create error for crew execution failure."""
    return CrewExecutionError(
        message=f"CrewAI execution {execution_id} failed: {str(original_error)}",
        error_code=ChatErrorCode.CREWAI_EXECUTION_TIMEOUT if "timeout" in str(original_error).lower() 
                   else ChatErrorCode.CREWAI_AGENT_FAILED,
        execution_id=execution_id,
        details={
            "original_error": str(original_error),
            "error_type": type(original_error).__name__
        }
    )


def create_streaming_error(thread_id: str, message_id: str, original_error: Exception) -> StreamingError:
    """Create error for streaming failure."""
    return StreamingError(
        message=f"Streaming failed for thread {thread_id}: {str(original_error)}",
        error_code=ChatErrorCode.STREAM_CONNECTION_LOST,
        thread_id=thread_id,
        message_id=message_id,
        details={
            "original_error": str(original_error),
            "error_type": type(original_error).__name__
        }
    )


def create_execution_already_running_error(graph_id: str) -> ChatContextError:
    """Create error for concurrent execution attempt."""
    return ChatContextError(
        message=f"Crew execution already running for graph {graph_id}",
        error_code=ChatErrorCode.EXECUTION_ALREADY_RUNNING,
        details={"graph_id": graph_id}
    )


class ErrorHandler:
    """Centralized error handling for chat operations."""
    
    @staticmethod
    def handle_graph_translation_error(e: Exception, graph_id: str, context: str = "") -> GraphTranslationError:
        """Handle and convert graph translation errors."""
        logger.error(f"Graph translation error for {graph_id} in {context}: {e}")
        
        error_msg = str(e)
        if "multiple crew" in error_msg.lower():
            # Extract crew count if available
            crew_count = 2  # Default assumption
            if "crew" in error_msg:
                try:
                    # Try to extract number from error message
                    import re
                    numbers = re.findall(r'\d+', error_msg)
                    if numbers:
                        crew_count = int(numbers[-1])
                except:
                    pass
            return create_multiple_crews_error(graph_id, crew_count)
        elif "missing" in error_msg.lower() and "agent" in error_msg.lower():
            # Extract missing fields if available
            missing_fields = ["role", "goal", "backstory"]  # Common missing fields
            return create_agent_config_error(graph_id, "unknown", missing_fields)
        else:
            return create_graph_structure_error(graph_id, {"original_error": error_msg})
    
    @staticmethod
    def handle_crew_execution_error(e: Exception, execution_id: str, context: str = "") -> CrewExecutionError:
        """Handle and convert crew execution errors."""
        logger.error(f"Crew execution error for {execution_id} in {context}: {e}")
        return create_crew_execution_error(execution_id, e)
    
    @staticmethod
    def handle_streaming_error(e: Exception, thread_id: str, message_id: str, context: str = "") -> StreamingError:
        """Handle and convert streaming errors."""
        logger.error(f"Streaming error for thread {thread_id} in {context}: {e}")
        return create_streaming_error(thread_id, message_id, e)
    
    @staticmethod
    def get_user_error_response(error: ChatError) -> Dict[str, Any]:
        """Get formatted error response for frontend."""
        return {
            "error": True,
            "message": error.user_message,
            "error_code": error.chat_error_code,
            "severity": error.severity.value,
            "recoverable": error.recoverable,
            "retry_recommended": error.retry_recommended
        } 