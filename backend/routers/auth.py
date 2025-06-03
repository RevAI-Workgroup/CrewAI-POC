"""
Authentication router with user registration and login using pseudo/passphrase system
"""

import uuid
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db_config import get_db
from models.user import User, UserRole
from schemas.auth import (
    UserCreate, UserCreateResponse, UserResponse, UserLogin, TokenResponse, 
    TokenRefresh, UserUpdate
)
from utils.auth import (
    generate_passphrase, create_access_token, 
    create_refresh_token, verify_token, ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user with pseudo and generate unique passphrase
    """
    # Generate unique passphrase
    max_attempts = 50
    for attempt in range(max_attempts):
        passphrase = generate_passphrase()
        
        # Check if passphrase is unique
        existing_user = db.query(User).filter(User.passphrase == passphrase).first()
        if not existing_user:
            break
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate unique passphrase"
        )
    
    # Create new user
    try:
        db_user = User(
            id=str(uuid.uuid4()),
            pseudo=user_data.pseudo,
            passphrase=passphrase,
            role=UserRole.USER
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Generate JWT tokens for auto-login
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(db_user.id), "pseudo": db_user.pseudo},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(db_user.id), "pseudo": db_user.pseudo}
        )
        
        # Update last login since we're auto-logging them in
        db_user.update_last_login()
        db.commit()
        
        # Create response with passphrase and JWT tokens
        user_response = UserResponse.model_validate(db_user)
        return UserCreateResponse(
            **user_response.model_dump(),
            passphrase=passphrase,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user - passphrase collision"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user using passphrase only and return JWT tokens
    """
    # Find user by passphrase
    user = db.query(User).filter(User.passphrase == login_data.passphrase).first()
    
    # Check if user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid passphrase",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "pseudo": user.pseudo},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "pseudo": user.pseudo}
    )
    
    # Update last login
    user.update_last_login()
    db.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    payload = verify_token(token_data.refresh_token, "refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    # Check user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "pseudo": user.pseudo},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "pseudo": user.pseudo}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )

# Note: Profile management endpoints will use dependencies 
# These will be implemented in future tasks 