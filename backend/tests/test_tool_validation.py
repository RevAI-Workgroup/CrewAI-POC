"""
Tests for tool validation utilities
Tests parameter validation, schema validation, and implementation validation
"""

import pytest
import json
from utils.tool_validation import (
    validate_tool_parameters,
    validate_tool_schema,
    validate_tool_implementation,
    ToolValidationError
)


class TestParameterValidation:
    """Test suite for tool parameter validation"""
    
    def test_validate_simple_schema_valid_params(self):
        """Test validation with simple schema and valid parameters"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            },
            "required": ["name"]
        }
        
        parameters = {"name": "Alice", "age": 25}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_simple_schema_missing_required(self):
        """Test validation with missing required parameter"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name", "age"]
        }
        
        parameters = {"name": "Bob"}  # Missing age
        is_valid, errors = validate_tool_parameters(parameters, schema)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("age" in error for error in errors)
    
    def test_validate_simple_schema_wrong_type(self):
        """Test validation with wrong parameter type"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
        
        parameters = {"name": "Charlie", "age": "not a number"}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_enum_valid_value(self):
        """Test validation with enum constraint and valid value"""
        schema = {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "pending"]
                }
            },
            "required": ["status"]
        }
        
        parameters = {"status": "active"}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_enum_invalid_value(self):
        """Test validation with enum constraint and invalid value"""
        schema = {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "pending"]
                }
            },
            "required": ["status"]
        }
        
        parameters = {"status": "invalid"}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_string_constraints(self):
        """Test validation with string length constraints"""
        schema = {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 20
                }
            },
            "required": ["username"]
        }
        
        # Valid username
        parameters = {"username": "alice123"}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is True
        
        # Too short
        parameters = {"username": "ab"}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is False
        
        # Too long
        parameters = {"username": "a" * 25}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is False
    
    def test_validate_number_constraints(self):
        """Test validation with number constraints"""
        schema = {
            "type": "object",
            "properties": {
                "score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 100
                }
            },
            "required": ["score"]
        }
        
        # Valid score
        parameters = {"score": 85.5}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is True
        
        # Below minimum
        parameters = {"score": -5}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is False
        
        # Above maximum
        parameters = {"score": 105}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is False
    
    def test_validate_additional_properties_false(self):
        """Test validation with additionalProperties: false"""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "additionalProperties": False,
            "required": ["name"]
        }
        
        # Valid - only allowed properties
        parameters = {"name": "Alice"}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is True
        
        # Invalid - additional property
        parameters = {"name": "Bob", "extra": "not allowed"}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is False
    
    def test_validate_nested_object(self):
        """Test validation with nested object schema"""
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"}
                    },
                    "required": ["name"]
                }
            },
            "required": ["user"]
        }
        
        # Valid nested object
        parameters = {"user": {"name": "Alice", "email": "alice@example.com"}}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is True
        
        # Invalid - missing required nested property
        parameters = {"user": {"email": "bob@example.com"}}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is False
    
    def test_validate_array_schema(self):
        """Test validation with array schema"""
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 5
                }
            },
            "required": ["tags"]
        }
        
        # Valid array
        parameters = {"tags": ["python", "api", "tool"]}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is True
        
        # Empty array (violates minItems)
        parameters = {"tags": []}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is False
        
        # Too many items
        parameters = {"tags": ["a", "b", "c", "d", "e", "f"]}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is False
        
        # Wrong item type
        parameters = {"tags": ["valid", 123, "invalid"]}
        is_valid, errors = validate_tool_parameters(parameters, schema)
        assert is_valid is False
    
    def test_validate_invalid_json_schema(self):
        """Test validation with malformed JSON schema"""
        invalid_schema = {"type": "invalid_type"}
        parameters = {"test": "value"}
        
        is_valid, errors = validate_tool_parameters(parameters, invalid_schema)
        
        assert is_valid is False
        assert len(errors) > 0


class TestSchemaValidation:
    """Test suite for tool schema validation"""
    
    def test_validate_valid_schema(self):
        """Test validation of valid tool schema"""
        valid_schema = {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input parameter"
                },
                "count": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 1
                }
            },
            "required": ["input"],
            "additionalProperties": False
        }
        
        is_valid, errors = validate_tool_schema(valid_schema)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_schema_missing_type(self):
        """Test validation of schema missing type property"""
        invalid_schema = {
            "properties": {
                "input": {"type": "string"}
            }
        }
        
        is_valid, errors = validate_tool_schema(invalid_schema)
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_schema_invalid_property_type(self):
        """Test validation of schema with invalid property type"""
        invalid_schema = {
            "type": "object",
            "properties": {
                "input": {"type": "invalid_type"}
            }
        }
        
        is_valid, errors = validate_tool_schema(invalid_schema)
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_schema_malformed_json(self):
        """Test validation of malformed schema"""
        invalid_schema = {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "enum": ["a", "b", "c"],
                    "minLength": 10  # Conflict: enum values are shorter than minLength
                }
            }
        }
        
        is_valid, errors = validate_tool_schema(invalid_schema)
        
        # This should still be valid as it's syntactically correct JSON Schema
        # even if logically inconsistent
        assert is_valid is True
    
    def test_validate_empty_schema(self):
        """Test validation of empty schema"""
        empty_schema = {}
        
        is_valid, errors = validate_tool_schema(empty_schema)
        
        assert is_valid is False
        assert len(errors) > 0


class TestImplementationValidation:
    """Test suite for tool implementation validation"""
    
    def test_validate_valid_implementation(self):
        """Test validation of valid tool implementation"""
        valid_implementation = '''
def execute(parameters):
    """Execute the tool"""
    name = parameters.get("name", "World")
    return f"Hello, {name}!"
'''
        
        is_valid, errors = validate_tool_implementation(valid_implementation)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_implementation_missing_execute_function(self):
        """Test validation of implementation missing execute function"""
        invalid_implementation = '''
def process(parameters):
    return "This is not execute function"
'''
        
        is_valid, errors = validate_tool_implementation(invalid_implementation)
        
        assert is_valid is False
        assert any("execute(" in error for error in errors)
    
    def test_validate_implementation_simple_return(self):
        """Test validation of implementation with simple return"""
        implementation_with_return = '''
def execute(parameters):
    name = parameters.get("name", "World")
    return f"Hello, {name}!"
'''
        
        is_valid, errors = validate_tool_implementation(implementation_with_return)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_implementation_syntax_error(self):
        """Test validation of implementation with syntax error"""
        invalid_implementation = '''
def execute(parameters):
    name = parameters.get("name", "World")
    if True
        return f"Hello, {name}!"  # Missing colon after if
'''
        
        is_valid, errors = validate_tool_implementation(invalid_implementation)
        
        assert is_valid is False
        assert any("Syntax error" in error for error in errors)
    
    def test_validate_implementation_dangerous_patterns(self):
        """Test validation catches dangerous patterns"""
        dangerous_implementations = [
            'import os\ndef execute(parameters):\n    return os.system("rm -rf /")',
            'import subprocess\ndef execute(parameters):\n    return subprocess.call(["ls"])',
            'def execute(parameters):\n    return eval(parameters["code"])',
            'def execute(parameters):\n    return exec(parameters["code"])',
            'def execute(parameters):\n    with open("/etc/passwd") as f:\n        return f.read()',
        ]
        
        for implementation in dangerous_implementations:
            is_valid, errors = validate_tool_implementation(implementation)
            assert is_valid is False
            assert len(errors) > 0
    
    def test_validate_implementation_empty_string(self):
        """Test validation of empty implementation"""
        empty_implementation = ""
        
        is_valid, errors = validate_tool_implementation(empty_implementation)
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_implementation_whitespace_only(self):
        """Test validation of whitespace-only implementation"""
        whitespace_implementation = "   \n\t\n   "
        
        is_valid, errors = validate_tool_implementation(whitespace_implementation)
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_implementation_valid_with_imports(self):
        """Test validation allows safe imports"""
        valid_implementation = '''
def execute(parameters):
    import json
    import math
    import datetime
    import re
    
    data = {"message": "Hello World"}
    return json.dumps(data)
'''
        
        is_valid, errors = validate_tool_implementation(valid_implementation)
        
        assert is_valid is True
        assert len(errors) == 0


class TestToolValidationError:
    """Test suite for ToolValidationError exception"""
    
    def test_tool_validation_error_creation(self):
        """Test creating ToolValidationError"""
        error = ToolValidationError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == {}
    
    def test_tool_validation_error_with_details(self):
        """Test creating ToolValidationError with details"""
        details = {"field": "name", "value": "invalid"}
        error = ToolValidationError("Validation failed", details)
        
        assert error.message == "Validation failed"
        assert error.details == details
    
    def test_tool_validation_error_inheritance(self):
        """Test that ToolValidationError inherits from Exception"""
        error = ToolValidationError("Test error")
        
        assert isinstance(error, Exception)
        assert isinstance(error, ToolValidationError)


class TestEdgeCasesAndIntegration:
    """Test suite for edge cases and integration scenarios"""
    
    def test_validate_none_parameters(self):
        """Test validation with None parameters"""
        schema = {"type": "object", "properties": {}}
        
        is_valid, errors = validate_tool_parameters(None, schema)  # type: ignore
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_none_schema(self):
        """Test validation with None schema"""
        parameters = {"test": "value"}
        
        is_valid, errors = validate_tool_parameters(parameters, None)  # type: ignore
        
        assert is_valid is False
        assert len(errors) > 0
    
    def test_validate_large_parameter_set(self):
        """Test validation with large parameter set"""
        schema = {
            "type": "object",
            "properties": {f"param_{i}": {"type": "string"} for i in range(100)},
            "required": [f"param_{i}" for i in range(50)]
        }
        
        parameters = {f"param_{i}": f"value_{i}" for i in range(100)}
        
        is_valid, errors = validate_tool_parameters(parameters, schema)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_deeply_nested_schema(self):
        """Test validation with deeply nested schema"""
        schema = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {
                        "level2": {
                            "type": "object",
                            "properties": {
                                "level3": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "string"}
                                    },
                                    "required": ["value"]
                                }
                            },
                            "required": ["level3"]
                        }
                    },
                    "required": ["level2"]
                }
            },
            "required": ["level1"]
        }
        
        parameters = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep value"
                    }
                }
            }
        }
        
        is_valid, errors = validate_tool_parameters(parameters, schema)
        
        assert is_valid is True
        assert len(errors) == 0 