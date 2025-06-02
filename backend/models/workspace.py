"""
Workspace model for organizing graphs and projects
"""

from sqlalchemy import Column, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import BaseModel

class Workspace(BaseModel):
    """
    Model for organizing graphs and projects into workspaces
    """
    
    # Basic workspace information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Owner and access control
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    is_public = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="workspaces")
    graphs = relationship("Graph", back_populates="workspace", cascade="all, delete-orphan")
    
    def is_owned_by(self, user_id: str) -> bool:
        """Check if this workspace belongs to the given user"""
        return str(self.owner_id) == str(user_id)
    
    def soft_delete(self) -> None:
        """Soft delete the workspace"""
        self.is_active = False
    
    def __repr__(self) -> str:
        return f"<Workspace(id={getattr(self, 'id', None)}, name='{self.name}', owner_id='{self.owner_id}')>" 