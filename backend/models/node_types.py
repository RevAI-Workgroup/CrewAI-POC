"""
Database models for CrewAI node types.
Provides ORM models for storing and managing node definitions.
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import BaseModel


class NodeTypeEnum(enum.Enum):
    """Node type enumeration for database."""
    AGENT = "agent"
    TASK = "task" 
    TOOL = "tool"
    FLOW = "flow"


class ProcessTypeEnum(enum.Enum):
    """Process type enumeration for database."""
    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"


class OutputFormatEnum(enum.Enum):
    """Output format enumeration for database."""
    RAW = "raw"
    JSON = "json"
    PYDANTIC = "pydantic"
    FILE = "file"


class NodeDefinition(BaseModel):
    """Base model for all node definitions."""
    __tablename__ = "node_definitions" # type: ignore
    
    # Override id to use string instead of integer from BaseModel
    id = Column(String, primary_key=True, index=True)
    type = Column(SQLEnum(NodeTypeEnum), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Visual properties
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    
    # Metadata and configuration
    metadata = Column(JSON, default=dict)
    configuration = Column(JSON, default=dict)
    
    # User association
    created_by = Column(String, ForeignKey("users.id"))
    
    # Graph association
    graph_id = Column(String, ForeignKey("graphs.id"))
    
    # Relationships
    graph = relationship("Graph", back_populates="nodes")
    
    def __repr__(self):
        return f"<NodeDefinition(id={self.id}, type={self.type}, name={self.name})>"


class AgentNode(BaseModel):
    """Extended model for Agent-specific properties."""
    __tablename__ = "agent_nodes" # type: ignore
    
    id = Column(String, ForeignKey("node_definitions.id"), primary_key=True, index=True)
    
    # Required Agent properties
    role = Column(Text, nullable=False)
    goal = Column(Text, nullable=False)
    backstory = Column(Text, nullable=False)
    
    # Optional Agent properties
    llm = Column(String(100))
    memory = Column(Boolean, default=True)
    verbose = Column(Boolean, default=False)
    allow_delegation = Column(Boolean, default=False)
    max_iter = Column(Integer, default=20)
    max_rpm = Column(Integer)
    max_execution_time = Column(Integer)
    
    # Tool associations (stored as JSON array of tool IDs)
    tools = Column(JSON, default=list)
    
    # Relationship to base node
    node = relationship("NodeDefinition", foreign_keys=[id])
    
    def __repr__(self):
        return f"<AgentNode(id={self.id}, role={self.role})>"


class TaskNode(BaseModel):
    """Extended model for Task-specific properties."""
    __tablename__ = "task_nodes" # type: ignore
    
    id = Column(String, ForeignKey("node_definitions.id"), primary_key=True, index=True)
    
    # Required Task properties
    description = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    
    # Optional Task properties
    agent_id = Column(String, ForeignKey("node_definitions.id"))
    async_execution = Column(Boolean, default=False)
    human_input = Column(Boolean, default=False)
    output_format = Column(SQLEnum(OutputFormatEnum), default=OutputFormatEnum.RAW)
    output_file = Column(String(500))
    callback = Column(String(255))
    
    # Dependencies and tools (stored as JSON arrays)
    tools = Column(JSON, default=list)
    context_task_ids = Column(JSON, default=list)
    
    # Relationship to base node and agent
    node = relationship("NodeDefinition", foreign_keys=[id])
    agent = relationship("NodeDefinition", foreign_keys=[agent_id])
    
    def __repr__(self):
        return f"<TaskNode(id={self.id}, description={self.description[:50]}...)>"


class ToolNode(BaseModel):
    """Extended model for Tool-specific properties."""
    __tablename__ = "tool_nodes" # type: ignore
    
    id = Column(String, ForeignKey("node_definitions.id"), primary_key=True, index=True)
    
    # Required Tool properties
    tool_type = Column(String(100), nullable=False)
    is_custom = Column(Boolean, default=False)
    
    # Tool configuration
    parameters = Column(JSON, default=dict)
    function_name = Column(String(255))
    api_endpoint = Column(String(500))
    
    # Relationship to base node
    node = relationship("NodeDefinition", foreign_keys=[id])
    
    def __repr__(self):
        return f"<ToolNode(id={self.id}, tool_type={self.tool_type})>"


class FlowNode(BaseModel):
    """Extended model for Flow control nodes."""
    __tablename__ = "flow_nodes" # type: ignore
    
    id = Column(String, ForeignKey("node_definitions.id"), primary_key=True, index=True)
    
    # Flow properties
    flow_type = Column(SQLEnum(ProcessTypeEnum), nullable=False)
    entry_point = Column(Boolean, default=False)
    exit_point = Column(Boolean, default=False)
    
    # Flow control configuration
    conditions = Column(JSON, default=dict)
    routing_rules = Column(JSON, default=list)
    
    # Relationship to base node
    node = relationship("NodeDefinition", foreign_keys=[id])
    
    def __repr__(self):
        return f"<FlowNode(id={self.id}, flow_type={self.flow_type})>"


class NodeConnection(BaseModel):
    """Model for connections/edges between nodes."""
    __tablename__ = "node_connections" # type: ignore
    
    id = Column(String, primary_key=True, index=True)
    source_id = Column(String, ForeignKey("node_definitions.id"), nullable=False)
    target_id = Column(String, ForeignKey("node_definitions.id"), nullable=False)
    
    # Connection properties
    edge_type = Column(String(50), default="default")
    label = Column(String(255))
    properties = Column(JSON, default=dict)
    
    # Graph association
    graph_id = Column(String, ForeignKey("graphs.id"))
    
    # User association
    created_by = Column(String, ForeignKey("users.id"))
    
    # Relationships
    source_node = relationship("NodeDefinition", foreign_keys=[source_id])
    target_node = relationship("NodeDefinition", foreign_keys=[target_id])
    graph = relationship("Graph", back_populates="connections")
    
    def __repr__(self):
        return f"<NodeConnection(id={self.id}, {self.source_id} -> {self.target_id})>"


class NodeTemplate(BaseModel):
    """Model for reusable node templates."""
    __tablename__ = "node_templates" # type: ignore
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(SQLEnum(NodeTypeEnum), nullable=False, index=True)
    
    # Template configuration
    template_config = Column(JSON, nullable=False)
    default_properties = Column(JSON, default=dict)
    
    # Template metadata
    category = Column(String(100))
    tags = Column(JSON, default=list)
    is_public = Column(Boolean, default=False)
    is_official = Column(Boolean, default=False)
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    
    # User association
    created_by = Column(String, ForeignKey("users.id"))
    
    def __repr__(self):
        return f"<NodeTemplate(id={self.id}, name={self.name}, type={self.type})>"


# Export models
__all__ = [
    "NodeTypeEnum",
    "ProcessTypeEnum", 
    "OutputFormatEnum",
    "NodeDefinition",
    "AgentNode",
    "TaskNode",
    "ToolNode",
    "FlowNode", 
    "NodeConnection",
    "NodeTemplate"
] 