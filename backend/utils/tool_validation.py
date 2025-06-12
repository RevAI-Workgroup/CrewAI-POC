"""
Tool Validation Utilities
Provides validation functions for tool schemas and parameters
"""

import json
import jsonschema
from typing import Dict, Any, List, Tuple, Optional
from jsonschema import ValidationError

class ToolValidationError(Exception):
    """Custom exception for tool validation errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

def validate_tool_schema(schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that a tool schema is properly formatted JSON Schema
    
    Args:
        schema: The schema dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        # Check if it's a valid JSON Schema by using the meta-schema
        jsonschema.Draft7Validator.check_schema(schema)
        
        # Additional checks for tool-specific requirements
        if not isinstance(schema, dict):
            errors.append("Schema must be a dictionary")
            return False, errors
        
        if "type" not in schema:
            errors.append("Schema must have a 'type' field")
        elif schema["type"] != "object":
            errors.append("Tool schema type must be 'object'")
        
        if "properties" not in schema:
            errors.append("Schema must have a 'properties' field")
        elif not isinstance(schema["properties"], dict):
            errors.append("Schema properties must be a dictionary")
        
        # Validate that required fields exist in properties
        if "required" in schema:
            if not isinstance(schema["required"], list):
                errors.append("Schema required field must be a list")
            else:
                properties = schema.get("properties", {})
                for required_field in schema["required"]:
                    if required_field not in properties:
                        errors.append(f"Required field '{required_field}' not found in properties")
        
        return len(errors) == 0, errors
        
    except jsonschema.SchemaError as e:
        errors.append(f"Invalid JSON Schema: {str(e)}")
        return False, errors
    except Exception as e:
        errors.append(f"Schema validation error: {str(e)}")
        return False, errors

def validate_tool_parameters(parameters: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate tool parameters against a schema
    
    Args:
        parameters: The parameters to validate
        schema: The schema to validate against
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        # First validate the schema itself
        schema_valid, schema_errors = validate_tool_schema(schema)
        if not schema_valid:
            errors.extend([f"Schema error: {err}" for err in schema_errors])
            return False, errors
        
        # Validate parameters against schema
        validator = jsonschema.Draft7Validator(schema)
        validation_errors = list(validator.iter_errors(parameters))
        
        for error in validation_errors:
            # Create more user-friendly error messages
            path = " -> ".join(str(p) for p in error.path) if error.path else "root"
            errors.append(f"Parameter '{path}': {error.message}")
        
        return len(errors) == 0, errors
        
    except Exception as e:
        errors.append(f"Parameter validation error: {str(e)}")
        return False, errors

def validate_tool_implementation(implementation: str) -> Tuple[bool, List[str]]:
    """
    Validate tool implementation code
    
    Args:
        implementation: Python code as string
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        # Basic syntax validation
        compile(implementation, '<tool_implementation>', 'exec')
        
        # Check for required imports/patterns (basic checks)
        required_patterns = [
            'def execute(',
            'return'
        ]
        
        for pattern in required_patterns:
            if pattern not in implementation:
                errors.append(f"Implementation missing required pattern: {pattern}")
        
        # Security checks - prevent dangerous operations
        dangerous_patterns = [
            'import os',
            'import subprocess',
            'import sys',
            '__import__',
            'eval(',
            'exec(',
            'open(',
            'file(',
        ]
        
        for pattern in dangerous_patterns:
            if pattern in implementation:
                errors.append(f"Implementation contains potentially dangerous pattern: {pattern}")
        
        return len(errors) == 0, errors
        
    except SyntaxError as e:
        errors.append(f"Syntax error in implementation: {str(e)}")
        return False, errors
    except Exception as e:
        errors.append(f"Implementation validation error: {str(e)}")
        return False, errors

def sanitize_tool_name(name: str) -> str:
    """
    Sanitize tool name to ensure it's safe for use
    
    Args:
        name: Raw tool name
        
    Returns:
        Sanitized tool name
    """
    # Remove non-alphanumeric characters except underscore and hyphen
    import re
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', name)
    
    # Ensure it starts with a letter or underscore
    if sanitized and not sanitized[0].isalpha() and sanitized[0] != '_':
        sanitized = '_' + sanitized
    
    # Limit length
    return sanitized[:50] if sanitized else 'unnamed_tool'

def extract_schema_info(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract useful information from a tool schema
    
    Args:
        schema: Tool schema dictionary
        
    Returns:
        Dictionary with extracted information
    """
    info = {
        "required_parameters": schema.get("required", []),
        "optional_parameters": [],
        "parameter_types": {},
        "parameter_descriptions": {}
    }
    
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    
    for param_name, param_schema in properties.items():
        param_type = param_schema.get("type", "unknown")
        param_desc = param_schema.get("description", "")
        
        info["parameter_types"][param_name] = param_type
        info["parameter_descriptions"][param_name] = param_desc
        
        if param_name not in required:
            info["optional_parameters"].append(param_name)
    
    return info 