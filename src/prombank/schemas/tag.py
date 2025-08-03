"""Tag-related Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, Field

from .common import BaseTimestampModel


class TagBase(BaseModel):
    """Base tag schema."""
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    description: Optional[str] = Field(None, max_length=500, description="Tag description")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")


class TagCreate(TagBase):
    """Schema for creating a tag."""
    pass


class TagUpdate(BaseModel):
    """Schema for updating a tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class TagResponse(BaseTimestampModel):
    """Schema for tag response."""
    name: str
    description: Optional[str]
    color: Optional[str]
    
    class Config:
        from_attributes = True


class TagWithCountResponse(TagResponse):
    """Schema for tag response with usage count."""
    usage_count: int = 0