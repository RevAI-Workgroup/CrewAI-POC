"""
Tool Executor Service
Handles execution of tools with proper validation and error handling
"""

import time
import traceback
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from models.tool import Tool
from services.tools import create_tool_instance, TOOL_REGISTRY
from services.tools.base_tool import BaseTool, ToolResult
from utils.tool_validation import (
    validate_tool_parameters, 
    validate_tool_schema,
    ToolValidationError
)
from exceptions.http_exceptions import NotFoundError, BadRequestError

class ToolExecutor:
    """Service for executing tools with validation and error handling"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def execute_builtin_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute a built-in tool by name
        
        Args:
            tool_name: Name of the built-in tool
            parameters: Parameters to pass to the tool
            
        Returns:
            ToolResult with execution results
        """
        try:
            # Check if tool exists in registry
            if tool_name not in TOOL_REGISTRY:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Built-in tool '{tool_name}' not found",
                    execution_time=0.0
                )
            
            # Create tool instance
            tool_instance = create_tool_instance(tool_name)
            
            # Validate parameters against tool schema
            schema = tool_instance.get_schema()
            is_valid, errors = validate_tool_parameters(parameters, schema)
            
            if not is_valid:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Parameter validation failed: {'; '.join(errors)}",
                    execution_time=0.0
                )
            
            # Execute the tool
            result = tool_instance.execute(parameters)
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool execution failed: {str(e)}",
                execution_time=0.0
            )
    
    def execute_custom_tool(self, tool_id: int, parameters: Dict[str, Any], user_id: Optional[str] = None) -> ToolResult:
        """
        Execute a custom tool from the database
        
        Args:
            tool_id: ID of the tool to execute
            parameters: Parameters to pass to the tool
            user_id: Optional user ID for access control
            
        Returns:
            ToolResult with execution results
        """
        start_time = time.time()
        
        try:
            # Get tool from database
            query = self.db.query(Tool).filter(Tool.id == tool_id)
            
            if user_id:
                # Filter by user access (own tools or public tools)
                from sqlalchemy import or_
                query = query.filter(
                    or_(
                        Tool.user_id == user_id,
                        Tool.is_public == "true"
                    )
                )
            
            tool = query.first()
            if not tool:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Tool with ID {tool_id} not found or access denied",
                    execution_time=time.time() - start_time
                )
            
            # Access the actual values from the model instance
            tool_schema = getattr(tool, 'schema')
            tool_implementation = getattr(tool, 'implementation')
            tool_name = getattr(tool, 'name')
            
            # Validate parameters against tool schema
            is_valid, errors = validate_tool_parameters(parameters, tool_schema)
            
            if not is_valid:
                return ToolResult(
                    success=False,
                    result=None,
                    error=f"Parameter validation failed: {'; '.join(errors)}",
                    execution_time=time.time() - start_time
                )
            
            # Execute the custom tool implementation
            result = self._execute_custom_implementation(
                tool_implementation, 
                parameters,
                tool_name
            )
            
            result.execution_time = time.time() - start_time
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Custom tool execution failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _execute_custom_implementation(self, implementation: str, parameters: Dict[str, Any], tool_name: str) -> ToolResult:
        """
        Execute custom tool implementation code
        
        Args:
            implementation: Python code to execute
            parameters: Parameters to pass to the tool
            tool_name: Name of the tool for error reporting
            
        Returns:
            ToolResult with execution results
        """
        try:
            # Create a restricted execution environment
            exec_globals = {
                '__builtins__': {
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'isinstance': isinstance,
                    'hasattr': hasattr,
                    'getattr': getattr,
                    'setattr': setattr,
                    'min': min,
                    'max': max,
                    'sum': sum,
                    'abs': abs,
                    'round': round,
                    'print': print,  # Allow print for debugging
                },
                'parameters': parameters,
                'time': time,
                'datetime': __import__('datetime'),
                'json': __import__('json'),
                'math': __import__('math'),
                're': __import__('re'),
            }
            
            exec_locals = {}
            
            # Execute the implementation
            exec(implementation, exec_globals, exec_locals)
            
            # Look for the execute function
            if 'execute' not in exec_locals:
                return ToolResult(
                    success=False,
                    result=None,
                    error="Tool implementation must define an 'execute' function",
                    execution_time=0.0
                )
            
            execute_func = exec_locals['execute']
            
            # Call the execute function
            result = execute_func(parameters)
            
            # Ensure result is a ToolResult
            if not isinstance(result, ToolResult):
                # If it's not a ToolResult, wrap it
                if isinstance(result, dict) and 'success' in result:
                    result = ToolResult(**result)
                else:
                    result = ToolResult(
                        success=True,
                        result=result,
                        error=None,
                        execution_time=0.0
                    )
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Custom tool execution error: {str(e)}\n{traceback.format_exc()}",
                execution_time=0.0
            )
    
    def validate_tool_before_execution(self, tool_id: int, parameters: Dict[str, Any], user_id: Optional[str] = None) -> tuple[bool, str]:
        """
        Validate a tool and its parameters before execution
        
        Args:
            tool_id: ID of the tool to validate
            parameters: Parameters to validate
            user_id: Optional user ID for access control
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Get tool from database
            query = self.db.query(Tool).filter(Tool.id == tool_id)
            
            if user_id:
                from sqlalchemy import or_
                query = query.filter(
                    or_(
                        Tool.user_id == user_id,
                        Tool.is_public == "true"
                    )
                )
            
            tool = query.first()
            if not tool:
                return False, f"Tool with ID {tool_id} not found or access denied"
            
            # Access the actual values from the model instance
            tool_schema = getattr(tool, 'schema')
            
            # Validate schema
            schema_valid, schema_errors = validate_tool_schema(tool_schema)
            if not schema_valid:
                return False, f"Tool schema invalid: {'; '.join(schema_errors)}"
            
            # Validate parameters
            params_valid, param_errors = validate_tool_parameters(parameters, tool_schema)
            if not params_valid:
                return False, f"Parameter validation failed: {'; '.join(param_errors)}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}" 