"""Category-related Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, Field

from .common import BaseTimestampModel


class CategoryBase(BaseModel):
    """Base category schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: Optional[str] = Field(None, max_length=500, description="Category description")
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    is_active: Optional[bool] = None


class CategoryResponse(BaseTimestampModel):
    """Schema for category response."""
    name: str
    description: Optional[str]
    color: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True


class CategoryWithCountResponse(CategoryResponse):
    """Schema for category response with prompt count."""
    prompt_count: int = 0