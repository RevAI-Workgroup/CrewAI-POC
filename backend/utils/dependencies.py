"""
FastAPI dependencies for authentication and authorization
"""

import sys
import os
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

# Add parent directory to Python path to ensure database module can be found
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import database function with error handling
try:
    from database import get_db
except ImportError as e:
    print(f"Warning: Could not import get_db from database module: {e}")
    # Create a fallback function for development
    def get_db():
        """Fallback database function for development"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine("sqlite:///:memory:")
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

from models.user import User
from utils.auth import verify_token, AuthenticationError

# HTTP Bearer security scheme
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    """
    token = credentials.credentials
    payload = verify_token(token, "access")
    
    if payload is None:
        raise AuthenticationError("Invalid authentication credentials")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Invalid token payload")
    
    # Simple query without complex filters
    user = db.query(User).filter(User.id == user_id).first()
    
    # Check user conditions after fetching
    if (user is None or 
        not getattr(user, 'is_active', False) or 
        getattr(user, 'is_deleted', True)):
        raise AuthenticationError("User not found or inactive")
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (additional check for is_active)
    """
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user with admin role
    """
    if not current_user.check_is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None

async def validate_token_only(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Validate JWT token without database lookup (for testing auth utilities)
    Returns payload if token is valid
    """
    token = credentials.credentials
    payload = verify_token(token, "access")
    
    if payload is None:
        raise AuthenticationError("Invalid authentication credentials")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationError("Invalid token payload")
    
    return {"user_id": user_id, "payload": payload} 