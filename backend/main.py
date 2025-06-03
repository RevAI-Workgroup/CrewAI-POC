"""
CrewAI Backend API
Main FastAPI application entry point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import startup module for database initialization
from startup import startup_database_check

# Import routers
from routers.auth import router as auth_router
from routers.graphs import router as graphs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup: Run database migrations
    print("🚀 Starting CrewAI Backend...")
    
    # Run database startup checks and migrations
    db_success = startup_database_check()
    
    if not db_success:
        print("💥 Database startup failed! Exiting...")
        sys.exit(1)
    
    print("✅ CrewAI Backend startup completed successfully!")
    
    yield  # Application runs here
    
    # Shutdown: Cleanup if needed
    print("🔄 Shutting down CrewAI Backend...")
    print("👋 CrewAI Backend shutdown completed!")


# Create FastAPI app with lifespan manager
app = FastAPI(
    title=os.getenv("APP_NAME", "CrewAI Backend"),
    description="Backend API for CrewAI Graph Builder",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(graphs_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "CrewAI Backend API is running"}

@app.get("/doc", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url or "/openapi.json",
        title=app.title,
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Import here to avoid circular imports
        from db_config import test_connection
        
        db_status = "healthy" if test_connection() else "unhealthy"
        
        return {
            "status": "healthy",
            "service": "crewai-backend",
            "version": "1.0.0",
            "database": db_status
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "crewai-backend", 
            "version": "1.0.0",
            "database": "error",
            "error": str(e)
        }

@app.get("/db-status")
async def database_status():
    """Detailed database status endpoint"""
    try:
        from db_config import test_connection, get_database_url
        from startup import get_current_database_revision, get_latest_migration_revision
        
        db_connected = test_connection()
        current_rev = get_current_database_revision() if db_connected else None
        latest_rev = get_latest_migration_revision()
        
        # Mask database URL for security
        db_url = get_database_url()
        if "://" in db_url and "@" in db_url:
            scheme_rest = db_url.split("://", 1)
            if len(scheme_rest) == 2:
                scheme, rest = scheme_rest
                if "@" in rest:
                    credentials, host_db = rest.split("@", 1)
                    if ":" in credentials:
                        user, password = credentials.split(":", 1)
                        masked_password = "*" * min(len(password), 8)
                        masked_url = f"{scheme}://{user}:{masked_password}@{host_db}"
                    else:
                        masked_url = db_url
                else:
                    masked_url = db_url
            else:
                masked_url = db_url
        else:
            masked_url = db_url
            
        return {
            "database_connected": db_connected,
            "database_url": masked_url,
            "current_migration": current_rev,
            "latest_migration": latest_rev,
            "migrations_up_to_date": current_rev == latest_rev if current_rev and latest_rev else False
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database status check failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run("main:app", host=host, port=port, reload=debug) 