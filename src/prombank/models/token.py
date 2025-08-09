"""API Token model."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class APIToken(Base):
    """API Token model for MCP authentication."""
    
    __tablename__ = "api_tokens"
    
    # Token details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    
    # User relationship
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="api_tokens")
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<APIToken(name='{self.name}', user_id={self.user_id})>"