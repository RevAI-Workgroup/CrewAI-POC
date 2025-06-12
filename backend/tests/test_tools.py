"""
Unit tests for tool implementations
Tests HelloWorldTool and base tool functionality
"""

import pytest
import time
from services.tools.hello_world_tool import HelloWorldTool
from services.tools.base_tool import BaseTool, ToolResult
from services.tools import get_available_tools, create_tool_instance, TOOL_REGISTRY

class TestHelloWorldTool:
    """Test suite for HelloWorldTool"""
    
    def setup_method(self):
        """Setup test environment"""
        self.tool = HelloWorldTool()
    
    def test_tool_initialization(self):
        """Test tool initializes correctly"""
        assert self.tool.name == "hello_world"
        assert self.tool.description == "A simple tool that creates personalized greetings"
        assert self.tool.version == "1.0.0"
    
    def test_get_schema(self):
        """Test tool schema generation"""
        schema = self.tool.get_schema()
        
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "greeting_style" in schema["properties"]
        assert "include_time" in schema["properties"]
        assert schema["required"] == ["name"]
        
        # Check name property
        name_prop = schema["properties"]["name"]
        assert name_prop["type"] == "string"
        assert name_prop["minLength"] == 1
        assert name_prop["maxLength"] == 100
        
        # Check greeting_style property
        style_prop = schema["properties"]["greeting_style"]
        assert style_prop["type"] == "string"
        assert set(style_prop["enum"]) == {"formal", "casual", "enthusiastic"}
        
        # Check include_time property
        time_prop = schema["properties"]["include_time"]
        assert time_prop["type"] == "boolean"
    
    def test_execute_valid_parameters_casual(self):
        """Test execution with valid casual greeting parameters"""
        parameters = {"name": "Alice"}
        result = self.tool.execute(parameters)
        
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.error is None
        assert "Hi Alice! How are you doing?" in result.result
        assert result.execution_time >= 0
    
    def test_execute_valid_parameters_formal(self):
        """Test execution with valid formal greeting parameters"""
        parameters = {"name": "Bob", "greeting_style": "formal"}
        result = self.tool.execute(parameters)
        
        assert result.success is True
        assert "Good day, Bob. I hope you are well." in result.result
    
    def test_execute_valid_parameters_enthusiastic(self):
        """Test execution with valid enthusiastic greeting parameters"""
        parameters = {"name": "Charlie", "greeting_style": "enthusiastic"}
        result = self.tool.execute(parameters)
        
        assert result.success is True
        assert "Hello there, Charlie! Great to see you!" in result.result
    
    def test_execute_with_time(self):
        """Test execution with time inclusion"""
        parameters = {"name": "Diana", "include_time": True}
        result = self.tool.execute(parameters)
        
        assert result.success is True
        assert "Diana" in result.result
        assert "The current time is" in result.result
    
    def test_execute_invalid_empty_name(self):
        """Test execution with empty name"""
        parameters = {"name": ""}
        result = self.tool.execute(parameters)
        
        assert result.success is False
        assert result.error == "Invalid parameters provided"
    
    def test_execute_invalid_missing_name(self):
        """Test execution with missing name parameter"""
        parameters = {}
        result = self.tool.execute(parameters)
        
        assert result.success is False
        assert result.error == "Invalid parameters provided"
    
    def test_execute_invalid_greeting_style(self):
        """Test execution with invalid greeting style"""
        parameters = {"name": "Eve", "greeting_style": "invalid"}
        result = self.tool.execute(parameters)
        
        assert result.success is False
        assert result.error == "Invalid parameters provided"
    
    def test_execute_invalid_include_time_type(self):
        """Test execution with invalid include_time type"""
        parameters = {"name": "Frank", "include_time": "yes"}
        result = self.tool.execute(parameters)
        
        assert result.success is False
        assert result.error == "Invalid parameters provided"
    
    def test_parameter_validation_valid(self):
        """Test parameter validation with valid inputs"""
        valid_params = [
            {"name": "Alice"},
            {"name": "Bob", "greeting_style": "formal"},
            {"name": "Charlie", "greeting_style": "casual", "include_time": True},
            {"name": "Diana", "greeting_style": "enthusiastic", "include_time": False}
        ]
        
        for params in valid_params:
            assert self.tool.validate_parameters(params) is True
    
    def test_parameter_validation_invalid(self):
        """Test parameter validation with invalid inputs"""
        invalid_params = [
            {},  # Missing name
            {"name": ""},  # Empty name
            {"name": "   "},  # Whitespace name
            {"name": "Alice", "greeting_style": "invalid"},  # Invalid style
            {"name": "Bob", "include_time": "yes"},  # Invalid type
            {"name": 123},  # Wrong type for name
        ]
        
        for params in invalid_params:
            assert self.tool.validate_parameters(params) is False
    
    def test_get_tool_info(self):
        """Test tool info retrieval"""
        info = self.tool.get_tool_info()
        
        assert info["name"] == "hello_world"
        assert info["description"] == "A simple tool that creates personalized greetings"
        assert info["version"] == "1.0.0"
        assert "schema" in info
        assert isinstance(info["schema"], dict)


class TestToolRegistry:
    """Test suite for tool registry functionality"""
    
    def test_get_available_tools(self):
        """Test getting list of available tools"""
        tools = get_available_tools()
        assert "hello_world" in tools
        assert isinstance(tools, list)
    
    def test_create_tool_instance_valid(self):
        """Test creating valid tool instance"""
        tool = create_tool_instance("hello_world")
        assert isinstance(tool, HelloWorldTool)
        assert tool.name == "hello_world"
    
    def test_create_tool_instance_invalid(self):
        """Test creating invalid tool instance"""
        with pytest.raises(ValueError) as exc_info:
            create_tool_instance("nonexistent_tool")
        
        assert "Tool 'nonexistent_tool' not found" in str(exc_info.value)
        assert "hello_world" in str(exc_info.value)
    
    def test_tool_registry_structure(self):
        """Test tool registry structure"""
        assert isinstance(TOOL_REGISTRY, dict)
        assert "hello_world" in TOOL_REGISTRY
        assert TOOL_REGISTRY["hello_world"] == HelloWorldTool


class TestToolResult:
    """Test suite for ToolResult class"""
    
    def test_tool_result_creation_success(self):
        """Test creating successful ToolResult"""
        result = ToolResult(
            success=True,
            result="Test result",
            error=None,
            execution_time=0.1
        )
        
        assert result.success is True
        assert result.result == "Test result"
        assert result.error is None
        assert result.execution_time == 0.1
    
    def test_tool_result_creation_failure(self):
        """Test creating failed ToolResult"""
        result = ToolResult(
            success=False,
            result=None,
            error="Test error",
            execution_time=0.05
        )
        
        assert result.success is False
        assert result.result is None
        assert result.error == "Test error"
        assert result.execution_time == 0.05
    
    def test_tool_result_defaults(self):
        """Test ToolResult default values"""
        result = ToolResult(success=True, result="test")
        
        assert result.error is None
        assert result.execution_time == 0.0


class MockTool(BaseTool):
    """Mock tool for testing base functionality"""
    
    def __init__(self):
        super().__init__("mock_tool", "A mock tool for testing", "1.0.0")
    
    def get_schema(self):
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            },
            "required": ["input"]
        }
    
    def execute(self, parameters):
        return ToolResult(
            success=True,
            result=f"Mock result for {parameters.get('input', 'unknown')}",
            execution_time=0.01
        )


class TestBaseTool:
    """Test suite for BaseTool abstract class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.tool = MockTool()
    
    def test_base_tool_initialization(self):
        """Test base tool initialization"""
        assert self.tool.name == "mock_tool"
        assert self.tool.description == "A mock tool for testing"
        assert self.tool.version == "1.0.0"
    
    def test_get_tool_info(self):
        """Test base tool info method"""
        info = self.tool.get_tool_info()
        
        assert info["name"] == "mock_tool"
        assert info["description"] == "A mock tool for testing"
        assert info["version"] == "1.0.0"
        assert "schema" in info
    
    def test_validate_parameters_required_fields(self):
        """Test base parameter validation"""
        # Valid parameters
        assert self.tool.validate_parameters({"input": "test"}) is True
        
        # Missing required field
        assert self.tool.validate_parameters({}) is False
        
        # Extra fields should pass base validation
        assert self.tool.validate_parameters({"input": "test", "extra": "field"}) is True 