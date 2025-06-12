"""
Base Tool Interface for CrewAI Backend
Defines the common interface that all tools must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ToolResult:
    """Result object returned by tool execution"""
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0

class BaseTool(ABC):
    """
    Abstract base class for all tools in the CrewAI system
    All custom tools must inherit from this class
    """
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Return the JSON schema for this tool's input parameters
        Must be implemented by all tools
        """
        pass
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool with the given parameters
        Must be implemented by all tools
        
        Args:
            parameters: Dictionary of input parameters matching the tool's schema
            
        Returns:
            ToolResult object with execution results
        """
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate input parameters against the tool's schema
        Can be overridden by tools for custom validation logic
        
        Args:
            parameters: Dictionary of input parameters
            
        Returns:
            True if parameters are valid, False otherwise
        """
        # Basic validation - tools can override for custom validation
        schema = self.get_schema()
        required_fields = schema.get("required", [])
        
        # Check required fields
        for field in required_fields:
            if field not in parameters:
                return False
        
        return True
    
    def get_tool_info(self) -> Dict[str, Any]:
        """
        Get basic information about this tool
        
        Returns:
            Dictionary with tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "schema": self.get_schema()
        } 