"""
Base model class for all database models in CrewAI Backend
"""

from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declared_attr
from db_config import Base

class BaseModel(Base):
    """
    Abstract base class for all database models
    Provides common fields and methods for all models
    """
    __abstract__ = True
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Soft delete support
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Automatically generate table name from class name
        Convert CamelCase to snake_case and add 's' for plural
        """
        import re
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        # Add 's' for plural if not already ending with 's'
        if not name.endswith('s'):
            name += 's'
        return name
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary
        Excludes private attributes and relationships
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Convert datetime to ISO string for JSON serialization
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result
    
    def update(self, **kwargs) -> None:
        """
        Update model attributes from keyword arguments
        Automatically updates the updated_at timestamp
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self) -> None:
        """
        Soft delete the model by setting is_deleted to True
        """
        self.is_deleted = True
        self.updated_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        """
        String representation of the model
        """
        return f"<{self.__class__.__name__}(id={self.id})>" 