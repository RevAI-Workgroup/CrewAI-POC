"""
Models package for CrewAI Backend
"""

from .base import BaseModel
from .user import User, UserRole

__all__ = ["BaseModel", "User", "UserRole"] 