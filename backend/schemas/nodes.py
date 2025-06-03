"""
Node schemas for CrewAI visual graph builder.
Defines Pydantic models for validation and serialization of all node types.
"""

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


class NodeType(str, Enum):
    """Enumeration of all supported node types."""
    AGENT = "agent"
    TASK = "task"
    TOOL = "tool"
    FLOW = "flow"
    CREW = "crew"


class ProcessType(str, Enum):
    """CrewAI process execution types."""
    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"


class OutputFormat(str, Enum):
    """Task output formats."""
    RAW = "raw"
    JSON = "json"
    PYDANTIC = "pydantic"
    FILE = "file"


# Base Node Schema
class BaseNodeSchema(BaseModel):
    """Base schema for all node types."""
    id: str = Field(..., description="Unique node identifier")
    type: NodeType = Field(..., description="Node type")
    name: str = Field(..., description="Human-readable node name")
    description: Optional[str] = Field(None, description="Node description")
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Agent Node Schema
class AgentNodeSchema(BaseNodeSchema):
    """Schema for CrewAI Agent nodes."""
    type: Literal[NodeType.AGENT] = NodeType.AGENT
    role: str = Field(..., description="Agent's function and expertise")
    goal: str = Field(..., description="Agent's individual objective")
    backstory: str = Field(..., description="Agent's context and personality")
    
    # Optional properties
    llm: Optional[str] = Field(None, description="Language model identifier")
    tools: List[str] = Field(default_factory=list, description="List of tool IDs")
    memory: bool = Field(True, description="Enable interaction memory")
    verbose: bool = Field(False, description="Enable detailed logging")
    allow_delegation: bool = Field(False, description="Allow task delegation")
    max_iter: int = Field(20, gt=0, description="Maximum iterations")
    max_rpm: Optional[int] = Field(None, gt=0, description="Rate limit (requests/minute)")
    max_execution_time: Optional[int] = Field(None, gt=0, description="Max execution time (seconds)")
    
    @validator('role', 'goal', 'backstory')
    def validate_required_strings(cls, v):
        if not v or not v.strip():
            raise ValueError('Required string fields cannot be empty')
        return v.strip()


# Task Node Schema  
class TaskNodeSchema(BaseNodeSchema):
    """Schema for CrewAI Task nodes."""
    type: Literal[NodeType.TASK] = NodeType.TASK
    description: str = Field(..., description="Clear task statement")
    expected_output: str = Field(..., description="Completion criteria description")
    
    # Optional properties
    agent_id: Optional[str] = Field(None, description="Assigned agent ID")
    tools: List[str] = Field(default_factory=list, description="Task-specific tool IDs")
    context_task_ids: List[str] = Field(default_factory=list, description="Context dependency task IDs")
    async_execution: bool = Field(False, description="Execute asynchronously")
    human_input: bool = Field(False, description="Require human review")
    output_format: OutputFormat = Field(OutputFormat.RAW, description="Output format type")
    output_file: Optional[str] = Field(None, description="Output file path")
    callback: Optional[str] = Field(None, description="Callback function name")
    
    @validator('description', 'expected_output')
    def validate_required_strings(cls, v):
        if not v or not v.strip():
            raise ValueError('Required string fields cannot be empty')
        return v.strip()


# Tool Node Schema
class ToolNodeSchema(BaseNodeSchema):
    """Schema for CrewAI Tool nodes."""
    type: Literal[NodeType.TOOL] = NodeType.TOOL
    tool_type: str = Field(..., description="Tool implementation type")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    is_custom: bool = Field(False, description="Whether this is a custom tool")
    
    # Common tool properties
    function_name: Optional[str] = Field(None, description="Function name for custom tools")
    api_endpoint: Optional[str] = Field(None, description="API endpoint for external tools")
    
    @validator('tool_type')
    def validate_tool_type(cls, v):
        if not v or not v.strip():
            raise ValueError('Tool type cannot be empty')
        return v.strip()


# Flow Node Schema
class FlowNodeSchema(BaseNodeSchema):
    """Schema for CrewAI Flow control nodes."""
    type: Literal[NodeType.FLOW] = NodeType.FLOW
    flow_type: ProcessType = Field(..., description="Flow execution type")
    entry_point: bool = Field(False, description="Whether this is the flow entry point")
    exit_point: bool = Field(False, description="Whether this is the flow exit point")
    
    # Flow control properties
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Flow conditions")
    routing_rules: List[Dict[str, Any]] = Field(default_factory=list, description="Routing rules")


# Crew Node Schema
class CrewNodeSchema(BaseNodeSchema):
    """Schema for CrewAI Crew nodes."""
    type: Literal[NodeType.CREW] = NodeType.CREW
    
    # Crew composition
    agent_ids: List[str] = Field(default_factory=list, description="List of agent IDs in this crew")
    task_ids: List[str] = Field(default_factory=list, description="List of task IDs for this crew")
    
    # Crew configuration
    process: ProcessType = Field(ProcessType.SEQUENTIAL, description="Crew execution process")
    verbose: bool = Field(False, description="Enable verbose logging for crew execution")
    memory: bool = Field(False, description="Enable crew memory")
    cache: bool = Field(True, description="Enable crew caching")
    
    # Crew limits and control
    max_rpm: Optional[int] = Field(None, gt=0, description="Rate limit for crew (requests/minute)")
    max_execution_time: Optional[int] = Field(None, gt=0, description="Max execution time for crew (seconds)")
    
    # Crew outputs and callbacks
    output_log_file: Optional[str] = Field(None, description="Path to crew execution log file")
    full_output: bool = Field(False, description="Return full output from all tasks")
    step_callback: Optional[str] = Field(None, description="Callback function for step completion")
    
    @validator('agent_ids')
    def validate_agent_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Crew must have at least one agent')
        return v
    
    @validator('task_ids')  
    def validate_task_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Crew must have at least one task')
        return v


# Edge/Connection Schema
class EdgeSchema(BaseModel):
    """Schema for connections between nodes."""
    id: str = Field(..., description="Unique edge identifier")
    source_id: str = Field(..., description="Source node ID")
    target_id: str = Field(..., description="Target node ID")
    edge_type: str = Field("default", description="Edge type")
    label: Optional[str] = Field(None, description="Edge label")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge properties")


# Graph Schema
class GraphSchema(BaseModel):
    """Schema for complete CrewAI graph."""
    id: str = Field(..., description="Graph identifier")
    name: str = Field(..., description="Graph name")
    description: Optional[str] = Field(None, description="Graph description")
    
    # Graph components
    nodes: List[Union[AgentNodeSchema, TaskNodeSchema, ToolNodeSchema, FlowNodeSchema, CrewNodeSchema]] = Field(
        default_factory=list, description="Graph nodes"
    )
    edges: List[EdgeSchema] = Field(default_factory=list, description="Graph edges")
    
    # Graph properties
    process_type: ProcessType = Field(ProcessType.SEQUENTIAL, description="Default process type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Graph metadata")
    
    class Config:
        use_enum_values = True


# Validation Response Schema
class NodeValidationSchema(BaseModel):
    """Schema for node validation responses."""
    is_valid: bool = Field(..., description="Whether the node is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    node_id: str = Field(..., description="Node ID being validated")


class GraphValidationSchema(BaseModel):
    """Schema for graph validation responses."""
    is_valid: bool = Field(..., description="Whether the graph is valid")
    errors: List[str] = Field(default_factory=list, description="Graph-level errors")
    warnings: List[str] = Field(default_factory=list, description="Graph-level warnings")
    node_validations: List[NodeValidationSchema] = Field(
        default_factory=list, description="Individual node validations"
    )


# Export schemas for easy importing
__all__ = [
    "NodeType",
    "ProcessType", 
    "OutputFormat",
    "BaseNodeSchema",
    "AgentNodeSchema",
    "TaskNodeSchema",
    "ToolNodeSchema", 
    "FlowNodeSchema",
    "CrewNodeSchema",
    "EdgeSchema",
    "GraphSchema",
    "NodeValidationSchema",
    "GraphValidationSchema"
] 