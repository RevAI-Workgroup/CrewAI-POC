"""
Database configuration and connection management for CrewAI Backend
"""

import os
from typing import Generator
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
database_url_env = os.getenv("DATABASE_URL")

# For testing, we can use SQLite in-memory database, but only if no specific DATABASE_URL is provided
TESTING = os.getenv("TESTING", "false").lower() == "true"
if TESTING and database_url_env is None:
    DATABASE_URL: str = "sqlite:///:memory:"
elif database_url_env is None:
    # Default database URL if none provided
    DATABASE_URL = "postgresql://user:password@localhost:5432/crewai_db"
else:
    DATABASE_URL = database_url_env

# At this point, DATABASE_URL is guaranteed to be a string
assert DATABASE_URL is not None, "DATABASE_URL should not be None after configuration"

# Create SQLAlchemy engine
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific configuration
    engine_kwargs.update({
        "poolclass": StaticPool,
        "connect_args": {
            "check_same_thread": False
        }
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create MetaData instance for database operations
metadata = MetaData()

# Create declarative base for models
Base = declarative_base(metadata=metadata)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    Yields a database session and ensures it's closed after use
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Create all tables in the database
    """
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    Drop all tables in the database (useful for testing)
    """
    Base.metadata.drop_all(bind=engine)

def get_database_url() -> str:
    """
    Get the current database URL
    """
    return DATABASE_URL

def test_connection() -> bool:
    """
    Test database connection
    Returns True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False 