"""
Database utility functions for CrewAI Backend
"""

import os
from typing import Optional, Type, TypeVar, Generic, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from models.base import BaseModel
from db_config import create_tables, drop_tables, test_connection, get_database_url, engine

# Type variable for generic model operations
ModelType = TypeVar("ModelType", bound=BaseModel)

class DatabaseManager:
    """
    Database manager class for common CRUD operations
    """
    
    @staticmethod
    def initialize_database():
        """
        Initialize database tables
        """
        try:
            create_tables()
            return True
        except SQLAlchemyError:
            return False
    
    @staticmethod
    def reset_database():
        """
        Reset database by dropping and recreating tables
        """
        try:
            drop_tables()
            create_tables()
            return True
        except SQLAlchemyError:
            return False
    
    @staticmethod
    def check_health() -> bool:
        """
        Check database health
        """
        return test_connection()

class CRUDBase(Generic[ModelType]):
    """
    Base CRUD operations class
    """
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Get a record by ID
        """
        return db.query(self.model).filter(
            self.model.id == id
            # Note: is_deleted filtering disabled to match migration schema
        ).first()
    
    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get multiple records with pagination
        """
        return db.query(self.model).filter(
            # Note: is_deleted filtering disabled to match migration schema
        ).offset(skip).limit(limit).all()
    
    def create(self, db: Session, obj_in: dict) -> ModelType:
        """
        Create a new record
        """
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(self, db: Session, db_obj: ModelType, obj_in: dict) -> ModelType:
        """
        Update an existing record
        """
        db_obj.update(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Delete a record (hard delete since soft delete is disabled)
        """
        obj = self.get(db, id)
        if obj:
            # Note: Using hard delete since is_deleted field is not in migration schema
            db.delete(obj)
            db.commit()
        return obj
    
    def hard_delete(self, db: Session, id: int) -> Optional[ModelType]:
        """
        Hard delete a record (permanently remove from database)
        """
        obj = db.query(self.model).filter(self.model.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

def get_database_info() -> dict:
    """
    Get database information and status
    """
    return {
        "database_url": get_database_url(),
        "is_testing": os.getenv("TESTING", "false").lower() == "true",
        "connection_status": test_connection(),
        "engine_info": str(type(engine))
    } 