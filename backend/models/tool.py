"""
Tool model for CrewAI Backend API
Stores tool definitions, schemas, and implementations
"""

from sqlalchemy import Column, String, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from models.base import BaseModel

class Tool(BaseModel):
    """
    Tool model for storing tool definitions and implementations
    Used by CrewAI agents for extended functionality
    """
    
    # Basic tool information
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Tool schema and implementation
    schema = Column(JSON, nullable=False)  # JSON schema for input/output validation
    implementation = Column(Text, nullable=False)  # Python code implementation
    
    # Tool metadata
    version = Column(String(20), nullable=False, default="1.0.0")
    category = Column(String(50), nullable=True, index=True)
    tags = Column(JSON, nullable=True)  # Array of tags for categorization
    
    # Ownership and access control
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    is_public = Column(String, nullable=False, default="false")  # "true"/"false" to match other models
    
    # Relationships
    user = relationship("User", back_populates="tools")
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_tool_name_user', 'name', 'user_id'),
        Index('idx_tool_category', 'category'),
        Index('idx_tool_public', 'is_public'),
    )
    
    def __repr__(self) -> str:
        """String representation of Tool"""
        return f"<Tool(id={self.id}, name='{self.name}', user_id='{self.user_id}')>" 