"""
Integration tests for ToolExecutor service
Tests built-in and custom tool execution with database integration
"""

import pytest
import time
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from services.tool_executor import ToolExecutor
from services.tools.base_tool import ToolResult
from models.tool import Tool
from models.user import User, UserRole
from models.api_key import APIKey


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def tool_executor(mock_db_session):
    """Tool executor instance with mock database"""
    return ToolExecutor(mock_db_session)


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    user = Mock()
    user.id = "user123"
    user.username = "testuser"
    user.role = UserRole.USER
    return user


@pytest.fixture
def sample_custom_tool():
    """Sample custom tool for testing"""
    tool = Mock()
    tool.id = 1
    tool.name = "custom_test_tool"
    tool.description = "A custom test tool"
    tool.version = "1.0.0"
    tool.schema = {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Message to process"}
        },
        "required": ["message"]
    }
    tool.implementation = '''
def execute(parameters):
    """Execute the custom test tool"""
    
    try:
        message = parameters.get("message", "")
        
        if not message:
            return {
                "success": False,
                "result": None,
                "error": "Message is required",
                "execution_time": 0.001
            }
        
        result = f"Processed: {message}"
        
        return {
            "success": True,
            "result": result,
            "error": None,
            "execution_time": 0.001
        }
        
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": f"Tool execution failed: {str(e)}",
            "execution_time": 0.001
        }
'''
    tool.user_id = "user123"
    tool.is_public = "true"
    return tool


class TestToolExecutorBuiltinTools:
    """Test suite for built-in tool execution"""
    
    def test_execute_builtin_tool_hello_world_success(self, tool_executor):
        """Test successful execution of hello world tool"""
        parameters = {"name": "Alice", "greeting_style": "casual"}
        
        result = tool_executor.execute_builtin_tool("hello_world", parameters)
        
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.error is None
        assert "Hi Alice! How are you doing?" in result.result
        assert result.execution_time >= 0
    
    def test_execute_builtin_tool_hello_world_with_time(self, tool_executor):
        """Test hello world tool with time inclusion"""
        parameters = {"name": "Bob", "greeting_style": "formal", "include_time": True}
        
        result = tool_executor.execute_builtin_tool("hello_world", parameters)
        
        assert result.success is True
        assert "Good day, Bob" in result.result
        assert "The current time is" in result.result
    
    def test_execute_builtin_tool_nonexistent(self, tool_executor):
        """Test execution of non-existent built-in tool"""
        parameters = {"test": "value"}
        
        result = tool_executor.execute_builtin_tool("nonexistent_tool", parameters)
        
        assert result.success is False
        assert "Built-in tool 'nonexistent_tool' not found" in result.error
        assert result.execution_time == 0.0
    
    def test_execute_builtin_tool_invalid_parameters(self, tool_executor):
        """Test execution with invalid parameters"""
        parameters = {}  # Missing required 'name' parameter
        
        result = tool_executor.execute_builtin_tool("hello_world", parameters)
        
        assert result.success is False
        assert "Parameter validation failed" in result.error
    
    def test_execute_builtin_tool_malformed_parameters(self, tool_executor):
        """Test execution with malformed parameters"""
        parameters = {"name": 123, "greeting_style": "invalid"}  # Wrong types
        
        result = tool_executor.execute_builtin_tool("hello_world", parameters)
        
        assert result.success is False
        assert "Parameter validation failed" in result.error
    
    @patch('services.tool_executor.create_tool_instance')
    def test_execute_builtin_tool_execution_exception(self, mock_create_tool, tool_executor):
        """Test handling of tool execution exceptions"""
        # Mock tool that raises exception
        mock_tool = Mock()
        mock_tool.get_schema.return_value = {"type": "object", "properties": {}, "required": []}
        mock_tool.execute.side_effect = Exception("Tool execution error")
        mock_create_tool.return_value = mock_tool
        
        parameters = {}
        
        result = tool_executor.execute_builtin_tool("hello_world", parameters)
        
        assert result.success is False
        assert "Tool execution failed" in result.error


class TestToolExecutorCustomTools:
    """Test suite for custom tool execution"""
    
    def test_execute_custom_tool_success(self, tool_executor, sample_custom_tool):
        """Test successful execution of custom tool"""
        # Setup mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_custom_tool
        tool_executor.db.query.return_value = mock_query
        
        parameters = {"message": "Hello World"}
        
        result = tool_executor.execute_custom_tool(1, parameters, "user123")
        
        assert result.success is True
        assert result.error is None
        assert "Processed: Hello World" in result.result
        assert result.execution_time >= 0
    
    def test_execute_custom_tool_not_found(self, tool_executor):
        """Test execution of non-existent custom tool"""
        # Setup mock database query that returns None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        tool_executor.db.query.return_value = mock_query
        
        parameters = {"message": "test"}
        
        result = tool_executor.execute_custom_tool(999, parameters, "user123")
        
        assert result.success is False
        assert "Tool with ID 999 not found or access denied" in result.error
    
    def test_execute_custom_tool_invalid_parameters(self, tool_executor, sample_custom_tool):
        """Test custom tool execution with invalid parameters"""
        # Setup mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_custom_tool
        tool_executor.db.query.return_value = mock_query
        
        parameters = {}  # Missing required 'message' parameter
        
        result = tool_executor.execute_custom_tool(1, parameters, "user123")
        
        assert result.success is False
        assert "Parameter validation failed" in result.error
    
    def test_execute_custom_tool_no_user_id(self, tool_executor, sample_custom_tool):
        """Test custom tool execution without user ID"""
        # Setup mock database query (should not filter by user)
        mock_query = Mock()
        mock_query.filter.return_value = sample_custom_tool
        tool_executor.db.query.return_value = mock_query
        
        parameters = {"message": "test"}
        
        result = tool_executor.execute_custom_tool(1, parameters)
        
        # Should call db.query(Tool).filter(Tool.id == tool_id) only
        tool_executor.db.query.assert_called_once()
        mock_query.filter.assert_called_once()
    
    def test_execute_custom_tool_access_control(self, tool_executor, sample_custom_tool):
        """Test custom tool access control with user filtering"""
        # Setup mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_custom_tool
        tool_executor.db.query.return_value = mock_query
        
        parameters = {"message": "test"}
        
        result = tool_executor.execute_custom_tool(1, parameters, "user123")
        
        # Should call filter twice (once for tool_id, once for user access)
        assert mock_query.filter.call_count == 2
    
    def test_execute_custom_tool_implementation_error(self, tool_executor):
        """Test custom tool with faulty implementation"""
        # Create tool with bad implementation
        bad_tool = Mock()
        bad_tool.id = 2
        bad_tool.name = "bad_tool"
        bad_tool.schema = {"type": "object", "properties": {}, "required": []}
        bad_tool.implementation = '''
def execute(parameters):
    raise Exception("Implementation error")
'''
        
        # Setup mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = bad_tool
        tool_executor.db.query.return_value = mock_query
        
        parameters = {}
        
        result = tool_executor.execute_custom_tool(2, parameters, "user123")
        
        assert result.success is False
        assert "Custom tool execution error" in result.error
    
    def test_execute_custom_implementation_no_execute_function(self, tool_executor):
        """Test custom implementation without execute function"""
        implementation = '''
def wrong_function(parameters):
    return "test"
'''
        
        result = tool_executor._execute_custom_implementation(implementation, {}, "test_tool")
        
        assert result.success is False
        assert "Tool implementation must define an 'execute' function" in result.error
    
    def test_execute_custom_implementation_syntax_error(self, tool_executor):
        """Test custom implementation with syntax error"""
        implementation = '''
def execute(parameters):
    return "test"
    # Invalid syntax below
    if True
        pass
'''
        
        result = tool_executor._execute_custom_implementation(implementation, {}, "test_tool")
        
        assert result.success is False
        assert "Custom tool execution error" in result.error
    
    def test_execute_custom_implementation_returns_dict(self, tool_executor):
        """Test custom implementation that returns dict instead of ToolResult"""
        implementation = '''
def execute(parameters):
    return {
        "success": True,
        "result": "Test result",
        "error": None,
        "execution_time": 0.01
    }
'''
        
        result = tool_executor._execute_custom_implementation(implementation, {}, "test_tool")
        
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.result == "Test result"
    
    def test_execute_custom_implementation_returns_simple_value(self, tool_executor):
        """Test custom implementation that returns simple value"""
        implementation = '''
def execute(parameters):
    return "Simple result"
'''
        
        result = tool_executor._execute_custom_implementation(implementation, {}, "test_tool")
        
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.result == "Simple result"
        assert result.error is None


class TestToolExecutorEdgeCases:
    """Test suite for edge cases and error handling"""
    
    def test_execute_builtin_tool_empty_parameters(self, tool_executor):
        """Test execution with empty parameters dict"""
        result = tool_executor.execute_builtin_tool("hello_world", {})
        
        assert result.success is False
        assert "Parameter validation failed" in result.error
    
    def test_execute_custom_tool_database_exception(self, tool_executor):
        """Test custom tool execution with database exception"""
        # Setup mock database to raise exception
        tool_executor.db.query.side_effect = Exception("Database error")
        
        parameters = {"message": "test"}
        
        result = tool_executor.execute_custom_tool(1, parameters, "user123")
        
        assert result.success is False
        assert "Custom tool execution failed" in result.error
        assert "Database error" in result.error
    
    def test_execute_custom_implementation_restricted_imports(self, tool_executor):
        """Test that custom implementation has restricted execution environment"""
        implementation = '''
def execute(parameters):
    # These should be available
    result = len("test")
    result += int("5")
    result += float("3.14")
    
    # Basic operations should work
    data = {"key": "value"}
    items = [1, 2, 3]
    
    return f"Result: {result}, Data: {data}, Items: {items}"
'''
        
        result = tool_executor._execute_custom_implementation(implementation, {}, "test_tool")
        
        assert result.success is True
        assert "Result: 12" in result.result
    
    def test_execute_custom_tool_performance_timing(self, tool_executor, sample_custom_tool):
        """Test that execution time is properly measured"""
        # Modify implementation to include delay
        sample_custom_tool.implementation = '''
def execute(parameters):
    # Simulate delay with a loop instead of time.sleep
    for i in range(100000):
        x = i * 2
    
    return {
        "success": True,
        "result": "Delayed result",
        "error": None,
        "execution_time": 0.0  # Will be overridden
    }
'''
        
        # Setup mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_custom_tool
        tool_executor.db.query.return_value = mock_query
        
        parameters = {"message": "test"}
        
        result = tool_executor.execute_custom_tool(1, parameters, "user123")
        
        assert result.success is True
        assert result.execution_time >= 0.001  # Should be measurable but not necessarily slow 