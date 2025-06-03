"""
Authentication-related Pydantic schemas for pseudo/passphrase system
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class UserRole(str, Enum):
    """User role enumeration matching the model"""
    ADMIN = "admin"
    USER = "user"

class UserBase(BaseModel):
    """Base user schema with common fields"""
    pseudo: str = Field(..., min_length=1, max_length=100, description="Display name (non-unique)")
    role: UserRole = UserRole.USER

class UserCreate(BaseModel):
    """Schema for user creation - only needs pseudo"""
    pseudo: str = Field(..., min_length=1, max_length=100, description="Display name (non-unique)")

class UserCreateResponse(UserBase):
    """Schema for user creation response - includes generated passphrase and JWT tokens"""
    id: str
    passphrase: str = Field(..., description="Generated unique passphrase for authentication")
    created_at: datetime
    updated_at: datetime
    access_token: str = Field(..., description="JWT access token for immediate login")
    refresh_token: str = Field(..., description="JWT refresh token for session management")
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    """Schema for user updates"""
    role: Optional[UserRole] = None

class UserResponse(UserBase):
    """Schema for user response (public fields)"""
    id: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    """Schema for user login - passphrase only"""
    passphrase: str = Field(..., description="Unique passphrase for authentication")

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class TokenRefresh(BaseModel):
    """Schema for token refresh"""
    refresh_token: str 