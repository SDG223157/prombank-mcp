"""Authentication service."""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from authlib.integrations.requests_client import OAuth2Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..config import settings
from ..models.user import User, UserSession, UserRole
from ..schemas.auth import GoogleUserInfo, TokenData


class AuthService:
    """Service for handling authentication."""
    
    def __init__(self, db: Session):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_user_from_google(self, google_user: GoogleUserInfo) -> User:
        """Create a new user from Google OAuth data."""
        
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            (User.email == google_user.email) | 
            (User.google_id == google_user.id)
        ).first()
        
        if existing_user:
            # Update existing user with Google data if needed
            if not existing_user.google_id:
                existing_user.google_id = google_user.id
            if not existing_user.avatar_url and google_user.picture:
                existing_user.avatar_url = google_user.picture
            if not existing_user.full_name and google_user.name:
                existing_user.full_name = google_user.name
            
            existing_user.is_verified = google_user.verified_email
            existing_user.email_verified_at = datetime.utcnow() if google_user.verified_email else None
            existing_user.last_login_at = datetime.utcnow()
            existing_user.provider_data = json.dumps({
                "given_name": google_user.given_name,
                "family_name": google_user.family_name,
                "picture": google_user.picture,
            })
            
            self.db.commit()
            self.db.refresh(existing_user)
            return existing_user
        
        # Create new user
        user = User(
            email=google_user.email,
            full_name=google_user.name,
            avatar_url=google_user.picture,
            google_id=google_user.id,
            provider="google",
            is_verified=google_user.verified_email,
            email_verified_at=datetime.utcnow() if google_user.verified_email else None,
            last_login_at=datetime.utcnow(),
            provider_data=json.dumps({
                "given_name": google_user.given_name,
                "family_name": google_user.family_name,
                "picture": google_user.picture,
            })
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def create_access_token(self, user: User, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token."""
        
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        
        to_encode = {
            "sub": str(user.id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify JWT token and return token data."""
        
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            token_type: str = payload.get("type", "access")
            
            if user_id is None:
                return None
            
            return TokenData(
                user_id=int(user_id),
                email=email,
                scopes=[]
            )
        
        except JWTError:
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user_session(
        self, 
        user: User, 
        access_token: str, 
        refresh_token: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> UserSession:
        """Create a user session."""
        
        expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        
        session = UserSession(
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def revoke_user_session(self, session_token: str) -> bool:
        """Revoke a user session."""
        
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()
            return True
        
        return False
    
    def revoke_all_user_sessions(self, user_id: int) -> int:
        """Revoke all sessions for a user."""
        
        count = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).update({UserSession.is_active: False})
        
        self.db.commit()
        return count
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        
        count = self.db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).delete()
        
        self.db.commit()
        return count
    
    def get_google_oauth_url(self, state: Optional[str] = None) -> str:
        """Get Google OAuth authorization URL."""
        
        oauth = OAuth2Session(
            client_id=settings.google_client_id,
            redirect_uri=settings.google_redirect_uri,
            scope="openid email profile"
        )
        
        authorization_url, state = oauth.create_authorization_url(
            "https://accounts.google.com/o/oauth2/auth",
            state=state,
            access_type="offline",
            prompt="consent"
        )
        
        return authorization_url
    
    def exchange_google_code(self, code: str) -> Optional[GoogleUserInfo]:
        """Exchange Google OAuth code for user information."""
        
        try:
            oauth = OAuth2Session(
                client_id=settings.google_client_id,
                redirect_uri=settings.google_redirect_uri
            )
            
            # Exchange code for token
            token = oauth.fetch_token(
                "https://oauth2.googleapis.com/token",
                code=code,
                client_secret=settings.google_client_secret
            )
            
            # Get user info
            response = oauth.get("https://www.googleapis.com/oauth2/v1/userinfo")
            user_data = response.json()
            
            return GoogleUserInfo(
                id=user_data["id"],
                email=user_data["email"],
                name=user_data.get("name"),
                picture=user_data.get("picture"),
                given_name=user_data.get("given_name"),
                family_name=user_data.get("family_name"),
                verified_email=user_data.get("verified_email", False)
            )
        
        except Exception as e:
            print(f"Error exchanging Google code: {e}")
            return None