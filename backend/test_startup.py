#!/usr/bin/env python3
"""
Test script for startup database migration functionality
"""

import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from startup import startup_database_check, ensure_database_schema, check_if_migrations_needed
from db_config import test_connection


def test_database_connection():
    """Test basic database connection"""
    print("🔍 Testing database connection...")
    
    if test_connection():
        print("✅ Database connection: OK")
        return True
    else:
        print("❌ Database connection: FAILED")
        return False


def test_migration_check():
    """Test migration status checking"""
    print("🔍 Testing migration status check...")
    
    try:
        needs_migration, current_rev, target_rev = check_if_migrations_needed()
        print(f"📋 Migration needed: {needs_migration}")
        print(f"📋 Current revision: {current_rev}")
        print(f"📋 Target revision: {target_rev}")
        return True
    except Exception as e:
        print(f"❌ Migration check failed: {e}")
        return False


def test_schema_validation():
    """Test database schema validation"""
    print("🔍 Testing database schema validation...")
    
    try:
        success = ensure_database_schema()
        if success:
            print("✅ Schema validation: OK")
        else:
            print("❌ Schema validation: FAILED")
        return success
    except Exception as e:
        print(f"❌ Schema validation error: {e}")
        return False


def test_full_startup():
    """Test full startup process"""
    print("🔍 Testing full startup process...")
    
    try:
        success = startup_database_check()
        if success:
            print("✅ Full startup: OK")
        else:
            print("❌ Full startup: FAILED")
        return success
    except Exception as e:
        print(f"❌ Full startup error: {e}")
        return False


def main():
    """Run all startup tests"""
    print("=" * 60)
    print("🧪 CrewAI Backend - Startup Functionality Test")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Migration Check", test_migration_check),
        ("Schema Validation", test_schema_validation),
        ("Full Startup Process", test_full_startup),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📝 Running: {test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🏆 Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Startup functionality is working correctly.")
        return True
    else:
        print("💥 Some tests failed. Please check the configuration and database setup.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 