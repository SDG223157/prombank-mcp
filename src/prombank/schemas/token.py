"""Token schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TokenCreate(BaseModel):
    """Schema for creating a new token."""
    name: str = Field(..., min_length=1, max_length=255, description="Token name")
    description: Optional[str] = Field(None, max_length=1000, description="Token description")


class TokenResponse(BaseModel):
    """Schema for token response."""
    id: int
    name: str
    description: Optional[str]
    token: Optional[str] = None  # Only included when creating a new token
    created_at: datetime
    last_used_at: Optional[datetime]
    
    class Config:
        from_attributes = True