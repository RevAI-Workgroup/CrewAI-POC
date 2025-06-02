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
    User model for authentication and profile management
    """
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Profile fields
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    
    # Role and permissions
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    
    # Password reset
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # Last login tracking
    last_login = Column(DateTime, nullable=True)
    
    # Relationships (to be defined in future tasks)
    api_keys = relationship("APIKey", back_populates="user")
    graphs = relationship("Graph", back_populates="user")
    metrics = relationship("Metric", back_populates="user")
    
    def get_full_name(self) -> str:
        """Get user's full name"""
        first = getattr(self, 'first_name', None) or ""
        last = getattr(self, 'last_name', None) or ""
        
        if first and last:
            return f"{first} {last}"
        elif first:
            return first
        elif last:
            return last
        else:
            email = getattr(self, 'email', '') or ""
            return email.split('@')[0] if '@' in email else ""
    
    def check_is_admin(self) -> bool:
        """Check if user has admin role"""
        user_role = getattr(self, 'role', None)
        return user_role == UserRole.ADMIN
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def set_reset_token(self, token: str, expires_at: datetime):
        """Set password reset token"""
        self.reset_token = token
        self.reset_token_expires = expires_at
        self.updated_at = datetime.utcnow()
    
    def clear_reset_token(self):
        """Clear password reset token"""
        self.reset_token = None
        self.reset_token_expires = None
        self.updated_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        return f"<User(id={getattr(self, 'id', None)}, email='{getattr(self, 'email', '')}', role='{getattr(self, 'role', '')}')>" 