"""
Hello World Tool - First concrete tool implementation
Demonstrates the tool framework with a simple greeting function
"""

import time
from typing import Dict, Any
from .base_tool import BaseTool, ToolResult

class HelloWorldTool(BaseTool):
    """
    Simple Hello World tool that creates personalized greetings
    Demonstrates basic tool functionality and serves as a template
    """
    
    def __init__(self):
        super().__init__(
            name="hello_world",
            description="A simple tool that creates personalized greetings",
            version="1.0.0"
        )
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Define the JSON schema for this tool's input parameters
        """
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the person to greet",
                    "minLength": 1,
                    "maxLength": 100
                },
                "greeting_style": {
                    "type": "string",
                    "description": "Style of greeting to use",
                    "enum": ["formal", "casual", "enthusiastic"],
                    "default": "casual"
                },
                "include_time": {
                    "type": "boolean",
                    "description": "Whether to include the current time in the greeting",
                    "default": False
                }
            },
            "required": ["name"],
            "additionalProperties": False
        }
    
    def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute the Hello World tool with the given parameters
        
        Args:
            parameters: Input parameters containing name and optional style
            
        Returns:
            ToolResult with personalized greeting
        """
        start_time = time.time()
        
        try:
            # Validate parameters
            if not self.validate_parameters(parameters):
                return ToolResult(
                    success=False,
                    result=None,
                    error="Invalid parameters provided",
                    execution_time=time.time() - start_time
                )
            
            # Extract parameters
            name = parameters["name"].strip()
            greeting_style = parameters.get("greeting_style", "casual")
            include_time = parameters.get("include_time", False)
            
            # Generate greeting based on style
            if greeting_style == "formal":
                greeting = f"Good day, {name}. I hope you are well."
            elif greeting_style == "enthusiastic":
                greeting = f"Hello there, {name}! Great to see you!"
            else:  # casual
                greeting = f"Hi {name}! How are you doing?"
            
            # Add time if requested
            if include_time:
                from datetime import datetime
                current_time = datetime.now().strftime("%H:%M:%S")
                greeting += f" The current time is {current_time}."
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                result=greeting,
                error=None,
                execution_time=execution_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool execution failed: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Custom validation for HelloWorldTool parameters
        """
        # Call base validation first
        if not super().validate_parameters(parameters):
            return False
        
        # Custom validation
        name = parameters.get("name", "")
        if not isinstance(name, str) or not name.strip():
            return False
        
        greeting_style = parameters.get("greeting_style", "casual")
        if greeting_style not in ["formal", "casual", "enthusiastic"]:
            return False
        
        include_time = parameters.get("include_time", False)
        if not isinstance(include_time, bool):
            return False
        
        return True 