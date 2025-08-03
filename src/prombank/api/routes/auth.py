"""Authentication API routes."""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ...database import get_db
from ...services.auth_service import AuthService
from ...schemas.auth import (
    TokenResponse, GoogleAuthRequest, RefreshTokenRequest, LogoutRequest,
    UserResponse
)
from ...auth import get_current_user, get_auth_service
from ...config import settings
from ...models.user import User

router = APIRouter()


@router.get("/google")
async def google_login(
    request: Request,
    state: Optional[str] = None,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Initiate Google OAuth login."""
    
    authorization_url = auth_service.get_google_oauth_url(state=state)
    
    return {
        "authorization_url": authorization_url,
        "message": "Redirect to this URL to authenticate with Google"
    }


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str,
    state: Optional[str] = None,
    error: Optional[str] = None,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Handle Google OAuth callback."""
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth error: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code"
        )
    
    # Exchange code for user info
    google_user = auth_service.exchange_google_code(code)
    
    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user information from Google"
        )
    
    # Create or update user
    user = auth_service.create_user_from_google(google_user)
    
    # Create tokens
    access_token = auth_service.create_access_token(user)
    refresh_token = auth_service.create_refresh_token(user)
    
    # Create session
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    
    auth_service.create_user_session(
        user=user,
        access_token=access_token,
        refresh_token=refresh_token,
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.from_orm(user)
    )


@router.post("/token", response_model=TokenResponse)
async def login_with_google_code(
    request: Request,
    google_auth: GoogleAuthRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login with Google authorization code (for API clients)."""
    
    # Exchange code for user info
    google_user = auth_service.exchange_google_code(google_auth.code)
    
    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user information from Google"
        )
    
    # Create or update user
    user = auth_service.create_user_from_google(google_user)
    
    # Create tokens
    access_token = auth_service.create_access_token(user)
    refresh_token = auth_service.create_refresh_token(user)
    
    # Create session
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    
    auth_service.create_user_session(
        user=user,
        access_token=access_token,
        refresh_token=refresh_token,
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.from_orm(user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token."""
    
    token_data = auth_service.verify_token(refresh_request.refresh_token)
    
    if not token_data or not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = auth_service.get_user_by_id(token_data.user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    new_access_token = auth_service.create_access_token(user)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=refresh_request.refresh_token,  # Keep same refresh token
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.from_orm(user)
    )


@router.post("/logout")
async def logout(
    logout_request: Optional[LogoutRequest] = None,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user and revoke tokens."""
    
    # Revoke all sessions for this user
    revoked_count = auth_service.revoke_all_user_sessions(current_user.id)
    
    return {
        "message": "Successfully logged out",
        "revoked_sessions": revoked_count
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse.from_orm(current_user)


@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's active sessions."""
    
    from ...models.user import UserSession
    
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).all()
    
    return {
        "sessions": [
            {
                "id": session.id,
                "user_agent": session.user_agent,
                "ip_address": session.ip_address,
                "created_at": session.created_at,
                "expires_at": session.expires_at
            }
            for session in sessions
        ]
    }