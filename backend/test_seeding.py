#!/usr/bin/env python3
"""
Test script for database seeding functionality
"""

import os
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables for testing
os.environ['DATABASE_URL'] = 'sqlite:///./test_seeding.db'
os.environ['ENCRYPTION_KEY'] = 'test-encryption-key-for-seeding'
os.environ['TESTING'] = 'false'

from db_config import engine, test_connection
from utils.seeder import DatabaseSeeder
from sqlalchemy import text
from alembic.config import Config
from alembic import command

# Import all models to ensure they're registered with SQLAlchemy
import models


def test_seeding():
    """Test the database seeding functionality"""
    print("🧪 Testing Database Seeding")
    print("=" * 50)
    
    # Test connection
    print("1. Testing database connection...")
    if not test_connection():
        print("❌ Database connection failed!")
        return False
    print("✅ Database connection successful!")
    
    # Close any existing connections
    engine.dispose()
    
    # Use migrations to create tables (not Base.metadata.create_all)
    print("\n2. Creating database tables using migrations...")
    try:
        # Delete existing database to start fresh
        db_file = Path("test_seeding.db")
        if db_file.exists():
            db_file.unlink()
            print("  ✓ Cleared existing database")
        
        # Run migrations
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("✅ Tables created using migrations!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    # Check what tables exist
    print("\n3. Checking created tables...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            print(f"✅ Tables found: {tables}")
    except Exception as e:
        print(f"❌ Failed to check tables: {e}")
        return False
    
    # Test seeding
    print("\n4. Testing database seeding...")
    try:
        with DatabaseSeeder() as seeder:
            seeder.seed_all(clear_existing=True)
        print("✅ Database seeding completed successfully!")
    except Exception as e:
        print(f"❌ Database seeding failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Check seeded data
    print("\n5. Checking seeded data...")
    try:
        with engine.connect() as conn:
            # Check users
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"✅ Users created: {user_count}")
            
            # Check API keys
            result = conn.execute(text("SELECT COUNT(*) FROM api_keys"))
            api_key_count = result.scalar()
            print(f"✅ API keys created: {api_key_count}")
            
            # Check graphs
            result = conn.execute(text("SELECT COUNT(*) FROM graphs"))
            graph_count = result.scalar()
            print(f"✅ Graphs created: {graph_count}")
            
            # Check threads
            result = conn.execute(text("SELECT COUNT(*) FROM threads"))
            thread_count = result.scalar()
            print(f"✅ Threads created: {thread_count}")
            
            # Check messages
            result = conn.execute(text("SELECT COUNT(*) FROM messages"))
            message_count = result.scalar()
            print(f"✅ Messages created: {message_count}")
            
            # Check executions
            result = conn.execute(text("SELECT COUNT(*) FROM executions"))
            execution_count = result.scalar()
            print(f"✅ Executions created: {execution_count}")
            
            # Check metrics
            result = conn.execute(text("SELECT COUNT(*) FROM metrics"))
            metric_count = result.scalar()
            print(f"✅ Metrics created: {metric_count}")
            
    except Exception as e:
        print(f"❌ Failed to check seeded data: {e}")
        return False
    
    print("\n🎉 All seeding tests passed!")
    print("=" * 50)
    return True


def cleanup():
    """Clean up test database"""
    db_file = Path("test_seeding.db")
    if db_file.exists():
        try:
            db_file.unlink()
            print("🧹 Test database cleaned up")
        except Exception as e:
            print(f"⚠️  Could not cleanup database: {e}")


if __name__ == "__main__":
    try:
        success = test_seeding()
        if not success:
            sys.exit(1)
    finally:
        cleanup() 