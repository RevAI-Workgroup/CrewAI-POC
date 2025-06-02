#!/usr/bin/env python3
"""
Test script to verify FastAPI application startup with automatic migrations
"""

import asyncio
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def test_app_startup():
    """Test the FastAPI application startup with lifespan events"""
    try:
        print("🧪 Testing FastAPI application startup...")
        
        from main import lifespan, app
        
        print("✅ Successfully imported main app and lifespan")
        
        # Test the lifespan context manager
        print("🚀 Testing lifespan startup...")
        
        async with lifespan(app):
            print("✅ Lifespan startup completed successfully!")
            print("🎉 Application is ready to serve requests!")
            
        print("✅ Lifespan shutdown completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Application startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 CrewAI Backend - Application Startup Test")
    print("=" * 60)
    
    success = await test_app_startup()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Application startup test passed!")
        print("✅ Automatic migrations are working correctly!")
    else:
        print("💥 Application startup test failed!")
        print("❌ Check the error messages above for details")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        sys.exit(1) 