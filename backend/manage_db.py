#!/usr/bin/env python3
"""
Database Management Script for CrewAI Backend
Provides commands for database migrations, seeding, and management
"""

import sys
import os
import argparse
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from alembic.config import Config
from alembic import command
from db_config import engine, test_connection, get_database_url
from utils.seeder import seed_database, clear_database
from sqlalchemy import text


def setup_alembic_config():
    """Setup Alembic configuration"""
    alembic_cfg = Config("alembic.ini")
    return alembic_cfg


def migrate_upgrade(revision="head"):
    """Run database migrations to upgrade to specified revision"""
    try:
        print(f"🔄 Upgrading database to revision: {revision}")
        alembic_cfg = setup_alembic_config()
        command.upgrade(alembic_cfg, revision)
        print("✅ Database migration completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False


def migrate_downgrade(revision):
    """Run database migrations to downgrade to specified revision"""
    try:
        print(f"🔄 Downgrading database to revision: {revision}")
        alembic_cfg = setup_alembic_config()
        command.downgrade(alembic_cfg, revision)
        print("✅ Database downgrade completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Downgrade failed: {str(e)}")
        return False


def generate_migration(message):
    """Generate a new migration file"""
    try:
        print(f"📝 Generating new migration: {message}")
        alembic_cfg = setup_alembic_config()
        command.revision(alembic_cfg, message=message, autogenerate=True)
        print("✅ Migration file generated successfully!")
        return True
    except Exception as e:
        print(f"❌ Migration generation failed: {str(e)}")
        return False


def show_migration_history():
    """Show migration history"""
    try:
        print("📋 Migration history:")
        alembic_cfg = setup_alembic_config()
        command.history(alembic_cfg, verbose=True)
        return True
    except Exception as e:
        print(f"❌ Failed to show history: {str(e)}")
        return False


def show_current_revision():
    """Show current database revision"""
    try:
        print("🔍 Current database revision:")
        alembic_cfg = setup_alembic_config()
        command.current(alembic_cfg, verbose=True)
        return True
    except Exception as e:
        print(f"❌ Failed to show current revision: {str(e)}")
        return False


def reset_database():
    """Reset database (clear all data and re-run migrations)"""
    try:
        print("🔄 Resetting database...")
        
        # Clear all data
        clear_database()
        
        # Downgrade to base
        alembic_cfg = setup_alembic_config()
        command.downgrade(alembic_cfg, "base")
        
        # Upgrade to head
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Database reset completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Database reset failed: {str(e)}")
        return False


def init_database():
    """Initialize database with migrations and seed data"""
    try:
        print("🚀 Initializing database...")
        
        # Test connection
        if not test_connection():
            print("❌ Database connection failed!")
            return False
        
        print("✅ Database connection successful!")
        
        # Run migrations
        if not migrate_upgrade():
            return False
        
        # Seed database
        print("🌱 Seeding database with initial data...")
        seed_database(clear_existing=False)
        
        print("✅ Database initialization completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        return False


def check_database_status():
    """Check database connection and current status"""
    print("🔍 Checking database status...")
    
    # Test connection
    if test_connection():
        print("✅ Database connection: OK")
    else:
        print("❌ Database connection: FAILED")
        return False
    
    # Show database URL (masked)
    db_url = get_database_url()
    masked_url = mask_database_url(db_url)
    print(f"📍 Database URL: {masked_url}")
    
    # Show current revision
    show_current_revision()
    
    # Check if database has data
    try:
        with engine.connect() as conn:
            # Check if users table exists and has data
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"👥 Users in database: {user_count}")
            
            # Check if migrations table exists
            result = conn.execute(text("SELECT COUNT(*) FROM alembic_version"))
            print("✅ Migration tracking: OK")
            
    except Exception as e:
        print(f"⚠️  Database status check incomplete: {str(e)}")
    
    return True


def mask_database_url(url):
    """Mask sensitive information in database URL"""
    if "://" in url:
        scheme, rest = url.split("://", 1)
        if "@" in rest:
            credentials, host_db = rest.split("@", 1)
            if ":" in credentials:
                user, password = credentials.split(":", 1)
                masked_password = "*" * len(password)
                return f"{scheme}://{user}:{masked_password}@{host_db}"
        return url
    return url


def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(
        description="Database Management Script for CrewAI Backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_db.py init                    # Initialize database
  python manage_db.py migrate                 # Run migrations
  python manage_db.py migrate --revision base # Migrate to specific revision
  python manage_db.py seed                    # Seed database
  python manage_db.py seed --clear            # Clear and seed database
  python manage_db.py status                  # Check database status
  python manage_db.py history                 # Show migration history
  python manage_db.py reset                   # Reset database completely
  python manage_db.py generate "Add new model" # Generate new migration
        """
    )
    
    parser.add_argument(
        'command',
        choices=['init', 'migrate', 'downgrade', 'seed', 'clear', 'status', 'history', 'current', 'reset', 'generate'],
        help='Database management command'
    )
    
    parser.add_argument(
        '--revision',
        default='head',
        help='Target revision for migrate/downgrade commands'
    )
    
    parser.add_argument(
        '--message',
        help='Message for generate command'
    )
    
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing data before seeding'
    )
    
    args = parser.parse_args()
    
    # Set environment variable for database operations
    os.environ.setdefault('PYTHONPATH', str(backend_dir))
    
    success = True
    
    if args.command == 'init':
        success = init_database()
    
    elif args.command == 'migrate':
        success = migrate_upgrade(args.revision)
    
    elif args.command == 'downgrade':
        if args.revision == 'head':
            print("❌ Downgrade requires a specific revision (not 'head')")
            success = False
        else:
            success = migrate_downgrade(args.revision)
    
    elif args.command == 'seed':
        try:
            seed_database(clear_existing=args.clear)
            print("✅ Database seeding completed!")
        except Exception as e:
            print(f"❌ Seeding failed: {str(e)}")
            success = False
    
    elif args.command == 'clear':
        try:
            clear_database()
            print("✅ Database cleared!")
        except Exception as e:
            print(f"❌ Clear failed: {str(e)}")
            success = False
    
    elif args.command == 'status':
        success = check_database_status()
    
    elif args.command == 'history':
        success = show_migration_history()
    
    elif args.command == 'current':
        success = show_current_revision()
    
    elif args.command == 'reset':
        confirm = input("⚠️  This will permanently delete all data. Are you sure? (yes/no): ")
        if confirm.lower() == 'yes':
            success = reset_database()
        else:
            print("❌ Reset cancelled")
            success = False
    
    elif args.command == 'generate':
        if not args.message:
            print("❌ Generate command requires --message")
            success = False
        else:
            success = generate_migration(args.message)
    
    if success:
        print(f"\n🎉 Command '{args.command}' completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Command '{args.command}' failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 