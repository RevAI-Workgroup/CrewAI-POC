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
    LLM = "llm"


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


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    AWS_BEDROCK = "aws_bedrock"
    OLLAMA = "ollama"
    GROQ = "groq"
    HUGGINGFACE = "huggingface"
    MISTRAL = "mistral"
    NVIDIA_NIM = "nvidia_nim"
    FIREWORKS = "fireworks"
    PERPLEXITY = "perplexity"
    SAMBANOVA = "sambanova"
    CEREBRAS = "cerebras"
    OPENROUTER = "openrouter"


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


# LLM Node Schema
class LLMNodeSchema(BaseNodeSchema):
    """Schema for LLM (Language Model) nodes."""
    type: Literal[NodeType.LLM] = NodeType.LLM
    
    # Core LLM configuration
    provider: LLMProvider = Field(..., description="LLM provider (OpenAI, Anthropic, etc.)")
    model: str = Field(..., description="Model name/identifier")
    
    # Authentication and API settings
    api_key: Optional[str] = Field(None, description="API key for authentication")
    base_url: Optional[str] = Field(None, description="Custom base URL for API endpoint")
    api_version: Optional[str] = Field(None, description="API version (for Azure/other providers)")
    organization: Optional[str] = Field(None, description="Organization ID (for OpenAI)")
    
    # Model parameters
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature (0.0-2.0)")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty (-2.0 to 2.0)")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty (-2.0 to 2.0)")
    
    # Advanced configuration
    timeout: Optional[int] = Field(None, gt=0, description="Request timeout in seconds")
    max_retries: Optional[int] = Field(3, ge=0, description="Maximum number of retries")
    streaming: bool = Field(False, description="Enable streaming responses")
    response_format: Optional[Dict[str, Any]] = Field(None, description="Response format specification")
    
    # Context and limits
    context_window: Optional[int] = Field(None, gt=0, description="Model context window size")
    max_rpm: Optional[int] = Field(None, gt=0, description="Rate limit (requests per minute)")
    
    # Stop sequences and control
    stop_sequences: List[str] = Field(default_factory=list, description="Stop sequences for generation")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    
    # Provider-specific configurations
    vertex_credentials: Optional[str] = Field(None, description="Google Vertex AI credentials JSON")
    aws_region: Optional[str] = Field(None, description="AWS region for Bedrock")
    azure_deployment: Optional[str] = Field(None, description="Azure deployment name")
    
    # Model capabilities and features
    supports_streaming: bool = Field(True, description="Whether the model supports streaming")
    supports_function_calling: bool = Field(False, description="Whether the model supports function calling")
    supports_vision: bool = Field(False, description="Whether the model supports vision/image inputs")
    supports_json_mode: bool = Field(False, description="Whether the model supports JSON mode")
    
    # Cost and performance metadata
    cost_per_input_token: Optional[float] = Field(None, ge=0, description="Cost per input token (USD)")
    cost_per_output_token: Optional[float] = Field(None, ge=0, description="Cost per output token (USD)")
    estimated_latency_ms: Optional[int] = Field(None, gt=0, description="Estimated response latency (ms)")
    
    @validator('model')
    def validate_model(cls, v):
        if not v or not v.strip():
            raise ValueError('Model name cannot be empty')
        return v.strip()
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if v and len(v.strip()) < 10:
            raise ValueError('API key appears to be too short')
        return v.strip() if v else None
    
    @validator('base_url')
    def validate_base_url(cls, v):
        if v and not v.strip().startswith(('http://', 'https://')):
            raise ValueError('Base URL must start with http:// or https://')
        return v.strip() if v else None


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
    nodes: List[Union[AgentNodeSchema, TaskNodeSchema, ToolNodeSchema, FlowNodeSchema, CrewNodeSchema, LLMNodeSchema]] = Field(
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
    "LLMProvider",
    "BaseNodeSchema",
    "AgentNodeSchema",
    "TaskNodeSchema",
    "ToolNodeSchema", 
    "FlowNodeSchema",
    "CrewNodeSchema",
    "LLMNodeSchema",
    "EdgeSchema",
    "GraphSchema",
    "NodeValidationSchema",
    "GraphValidationSchema"
] 