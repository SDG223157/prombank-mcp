"""Authentication utilities and dependencies."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .database import get_db
from .services.auth_service import AuthService
from .services.token_service import TokenService
from .models.user import User
from .schemas.auth import TokenData

security = HTTPBearer()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get authentication service."""
    return AuthService(db)


def get_token_service(db: Session = Depends(get_db)) -> TokenService:
    """Get token service."""
    return TokenService(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service)
) -> User:
    """Get current authenticated user (supports both JWT and API tokens)."""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    
    # Check if it's an API token (starts with 'pb_')
    if token.startswith('pb_'):
        token_data = token_service.verify_token(token)
        if token_data and token_data.get('user'):
            user = token_data['user']
            if user and user.is_active:
                return user
        raise credentials_exception
    
    # Otherwise, treat as JWT token
    jwt_token_data = auth_service.verify_token(token)
    
    if jwt_token_data is None or jwt_token_data.user_id is None:
        raise credentials_exception
    
    user = auth_service.get_user_by_id(jwt_token_data.user_id)
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current admin user."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# Optional authentication for public endpoints
def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    
    if credentials is None:
        return None
    
    try:
        token_data = auth_service.verify_token(credentials.credentials)
        
        if token_data is None or token_data.user_id is None:
            return None
        
        user = auth_service.get_user_by_id(token_data.user_id)
        
        if user is None or not user.is_active:
            return None
        
        return user
    
    except Exception:
        return None