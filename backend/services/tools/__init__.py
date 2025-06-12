"""
Tools module for CrewAI Backend
Contains all tool implementations and utilities
"""

from .base_tool import BaseTool, ToolResult
from .hello_world_tool import HelloWorldTool

# Tool registry - maps tool names to their classes
TOOL_REGISTRY = {
    "hello_world": HelloWorldTool,
}

def get_available_tools():
    """Get list of all available tool names"""
    return list(TOOL_REGISTRY.keys())

def create_tool_instance(tool_name: str) -> BaseTool:
    """
    Create an instance of a tool by name
    
    Args:
        tool_name: Name of the tool to create
        
    Returns:
        Instance of the requested tool
        
    Raises:
        ValueError: If tool name is not found in registry
    """
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(TOOL_REGISTRY.keys())}")
    
    tool_class = TOOL_REGISTRY[tool_name]
    return tool_class()

__all__ = [
    "BaseTool",
    "ToolResult", 
    "HelloWorldTool",
    "TOOL_REGISTRY",
    "get_available_tools",
    "create_tool_instance"
] 