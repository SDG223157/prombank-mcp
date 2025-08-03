"""Common Pydantic schemas."""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(20, ge=1, le=100, description="Number of items to return")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""
    items: List[T]
    total: int = Field(description="Total number of items")
    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Number of items per page")
    has_next: bool = Field(description="Whether there are more items")
    has_prev: bool = Field(description="Whether there are previous items")


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str
    error_code: Optional[str] = None


class BaseTimestampModel(BaseModel):
    """Base model with timestamps."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True