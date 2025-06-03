"""
User model for authentication and authorization
"""

from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class UserRole(str, Enum):
    """User role enumeration for access control"""
    ADMIN = "admin"
    USER = "user"

class User(BaseModel):
    """
    User model for pseudo/passphrase authentication and profile management
    """
    
    # Override id field to use String instead of Integer
    id = Column(String(36), primary_key=True, index=True, nullable=False)
    
    # Authentication fields
    pseudo = Column(String(100), nullable=False)  # Non-unique display name
    passphrase = Column(String(255), unique=True, index=True, nullable=False)  # Unique auth token
    
    # Role and permissions
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    
    # Last login tracking
    last_login = Column(DateTime, nullable=True)
    
    # Relationships (to be defined in future tasks)
    api_keys = relationship("APIKey", back_populates="user")
    graphs = relationship("Graph", back_populates="user")
    metrics = relationship("Metric", back_populates="user")
    
    def get_display_name(self) -> str:
        """Get user's display name"""
        pseudo = getattr(self, 'pseudo', '') or ""
        return pseudo if pseudo else "Unknown User"
    
    def check_is_admin(self) -> bool:
        """Check if user has admin role"""
        user_role = getattr(self, 'role', None)
        return user_role == UserRole.ADMIN
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        return f"<User(id={getattr(self, 'id', None)}, pseudo='{getattr(self, 'pseudo', '')}', role='{getattr(self, 'role', '')}')>" 