"""
FastAPI dependencies for authentication and authorization
Note: Full database integration will be completed in Task 1-5 (User Registration and Login)
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models.user import User
from utils.auth import verify_token, AuthenticationError

# HTTP Bearer security scheme
security = HTTPBearer()

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

# Full database-dependent authentication functions will be implemented in Task 1-5:
# - get_current_user: Get user from database using JWT token
# - get_current_active_user: Ensure user is active
# - get_current_admin_user: Ensure user has admin role
# - get_optional_current_user: Optional authentication 