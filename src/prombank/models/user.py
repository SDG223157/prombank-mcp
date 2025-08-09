"""User authentication models."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from sqlalchemy import Boolean, DateTime, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class UserRole(str, PyEnum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    # Basic information
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Authentication
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255))  # For future password auth
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.USER.value)
    
    # OAuth details
    provider: Mapped[Optional[str]] = mapped_column(String(50), default="google")
    provider_data: Mapped[Optional[str]] = mapped_column(Text)  # JSON string for additional OAuth data
    
    # Timestamps
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships  
    # api_tokens: Mapped[list["APIToken"]] = relationship("APIToken", back_populates="user", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self) -> str:
        return f"<User(email='{self.email}', role='{self.role}')>"


class UserSession(Base):
    """User session model for tracking active sessions."""
    
    __tablename__ = "user_sessions"
    
    user_id: Mapped[int] = mapped_column(String(255), nullable=False, index=True)
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    
    # Session details
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))  # IPv6 compatible
    
    # Expiration
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    def __repr__(self) -> str:
        return f"<UserSession(user_id={self.user_id}, expires_at='{self.expires_at}')>"