"""
Authentication-related Pydantic schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from enum import Enum

class UserRole(str, Enum):
    """User role enumeration matching the model"""
    ADMIN = "admin"
    USER = "user"

class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")

class UserUpdate(BaseModel):
    """Schema for user updates"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[UserRole] = None

class UserResponse(UserBase):
    """Schema for user response (public fields)"""
    id: int
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

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

class PasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters")

class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters") 