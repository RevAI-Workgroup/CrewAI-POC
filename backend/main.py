"""
CrewAI Backend API
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from routers.auth import router as auth_router

# Create FastAPI app
app = FastAPI(
    title=os.getenv("APP_NAME", "CrewAI Backend"),
    description="Backend API for CrewAI Graph Builder",
    version="1.0.0"
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

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "CrewAI Backend API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "crewai-backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run("main:app", host=host, port=port, reload=debug) 