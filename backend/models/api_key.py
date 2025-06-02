"""
API Key model for secure storage of user API keys
"""

from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from .base import BaseModel
from services.encryption import encryption_service

class APIKeyType(str, Enum):
    """Supported API key types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    OTHER = "other"

class APIKey(BaseModel):
    """
    Model for storing encrypted API keys for external services
    """
    
    # Explicit table name to match migration schema
    __tablename__ = "api_keys"  # type: ignore
    
    # Override id field to use String instead of Integer (matches migration schema)
    id = Column(String(36), primary_key=True, index=True, nullable=False)
    
    # Foreign key to user
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # API key metadata
    name = Column(String(100), nullable=False)  # User-friendly name for the key
    key_type = Column(String(20), nullable=False)  # Type of API key (openai, anthropic, etc.)
    
    # Encrypted API key value
    encrypted_value = Column(String(500), nullable=False)  # Encrypted API key
    
    # Status and management
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uq_user_api_key_name'),
    )
    
    def set_api_key_value(self, value: str) -> None:
        """Encrypt and store the API key value"""
        if not value or not value.strip():
            raise ValueError("API key value cannot be empty")
        
        self.encrypted_value = encryption_service.encrypt(value.strip())
    
    def get_api_key_value(self) -> str:
        """Decrypt and return the API key value"""
        encrypted_val = getattr(self, 'encrypted_value', None)
        if not encrypted_val:
            raise ValueError("No encrypted value stored")
        
        return encryption_service.decrypt(encrypted_val)
    
    def validate_key_type(self) -> bool:
        """Validate that the key_type is supported"""
        try:
            APIKeyType(self.key_type)
            return True
        except ValueError:
            return False
    
    def get_masked_value(self) -> str:
        """Return a masked version of the API key for display"""
        try:
            value = self.get_api_key_value()
            if len(value) <= 8:
                return "*" * len(value)
            return f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"
        except:
            return "****"
    
    def soft_delete(self) -> None:
        """Soft delete the API key for security"""
        self.is_active = False
        # Keep encrypted value for audit trail but mark as inactive
    
    def is_owned_by(self, user_id: str) -> bool:
        """Check if this API key belongs to the given user"""
        return str(self.user_id) == str(user_id)
    
    @classmethod
    def validate_api_key_format(cls, key_type: str, api_key: str) -> bool:
        """Basic validation of API key format based on type"""
        if not api_key or not api_key.strip():
            return False
        
        api_key = api_key.strip()
        
        # Basic format validation based on known patterns
        if key_type == APIKeyType.OPENAI:
            return api_key.startswith("sk-") and len(api_key) >= 20
        elif key_type == APIKeyType.ANTHROPIC:
            return api_key.startswith("sk-ant-") and len(api_key) >= 20
        elif key_type == APIKeyType.GOOGLE:
            return len(api_key) >= 20  # Google API keys vary in format
        elif key_type == APIKeyType.AZURE_OPENAI:
            return len(api_key) >= 32  # Azure keys are typically 32 chars
        elif key_type == APIKeyType.COHERE:
            return len(api_key) >= 20
        elif key_type == APIKeyType.HUGGINGFACE:
            return api_key.startswith("hf_") and len(api_key) >= 20
        else:
            return len(api_key) >= 8  # Minimum length for other types
    
    def __repr__(self) -> str:
        return f"<APIKey(id={getattr(self, 'id', None)}, user_id='{self.user_id}', name='{self.name}', type='{self.key_type}', active={self.is_active})>" 