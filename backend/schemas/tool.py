"""
Tool schemas for request/response validation
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

class ToolBase(BaseModel):
    """Base tool schema with common fields"""
    name: str = Field(..., max_length=100, description="Tool name")
    description: Optional[str] = Field(None, description="Tool description")
    schema: Dict[str, Any] = Field(..., description="JSON schema for input/output validation")
    implementation: str = Field(..., description="Python code implementation")
    version: str = Field(default="1.0.0", max_length=20, description="Tool version")
    category: Optional[str] = Field(None, max_length=50, description="Tool category")
    tags: Optional[List[str]] = Field(None, description="Tool tags for categorization")
    is_public: bool = Field(default=False, description="Whether tool is publicly accessible")

class ToolCreate(ToolBase):
    """Schema for creating a new tool"""
    pass

class ToolUpdate(BaseModel):
    """Schema for updating an existing tool"""
    name: Optional[str] = Field(None, max_length=100, description="Tool name")
    description: Optional[str] = Field(None, description="Tool description")
    schema: Optional[Dict[str, Any]] = Field(None, description="JSON schema for input/output validation")
    implementation: Optional[str] = Field(None, description="Python code implementation")
    version: Optional[str] = Field(None, max_length=20, description="Tool version")
    category: Optional[str] = Field(None, max_length=50, description="Tool category")
    tags: Optional[List[str]] = Field(None, description="Tool tags for categorization")
    is_public: Optional[bool] = Field(None, description="Whether tool is publicly accessible")

class ToolResponse(ToolBase):
    """Schema for tool response"""
    id: int = Field(..., description="Tool ID")
    user_id: str = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True

class ToolListResponse(BaseModel):
    """Schema for listing tools"""
    tools: List[ToolResponse] = Field(..., description="List of tools")
    total: int = Field(..., description="Total number of tools")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")

class ToolExecuteRequest(BaseModel):
    """Schema for executing a tool"""
    tool_id: int = Field(..., description="Tool ID to execute")
    parameters: Dict[str, Any] = Field(..., description="Tool execution parameters")

class ToolExecuteResponse(BaseModel):
    """Schema for tool execution response"""
    success: bool = Field(..., description="Execution success status")
    result: Any = Field(..., description="Execution result")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: float = Field(..., description="Execution time in seconds") 