"""Prompt-related Pydantic schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator

from ..models.prompt import PromptType, PromptStatus
from .common import BaseTimestampModel
from .category import CategoryResponse
from .tag import TagResponse


class PromptBase(BaseModel):
    """Base prompt schema."""
    title: str = Field(..., min_length=1, max_length=200, description="Prompt title")
    description: Optional[str] = Field(None, max_length=1000, description="Prompt description")
    content: str = Field(..., min_length=1, description="Prompt content")
    prompt_type: PromptType = Field(PromptType.USER, description="Type of prompt")
    category_id: Optional[int] = Field(None, description="Category ID")
    tags: Optional[List[str]] = Field(None, description="List of tag names")
    is_public: bool = Field(False, description="Whether prompt is public")
    is_favorite: bool = Field(False, description="Whether prompt is favorited")
    is_template: bool = Field(False, description="Whether prompt is a template")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="Template variable definitions")


class PromptCreate(PromptBase):
    """Schema for creating a prompt."""
    pass


class PromptUpdate(BaseModel):
    """Schema for updating a prompt."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = Field(None, min_length=1)
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    status: Optional[PromptStatus] = None
    is_public: Optional[bool] = None
    is_favorite: Optional[bool] = None
    template_variables: Optional[Dict[str, Any]] = None
    create_version: bool = Field(False, description="Create new version on update")
    version_comment: Optional[str] = Field(None, description="Comment for version")


class PromptVersionResponse(BaseTimestampModel):
    """Schema for prompt version response."""
    version: str
    content: str
    title: str
    description: Optional[str]
    change_log: Optional[str]
    is_major_change: bool
    prompt_id: int


class PromptResponse(BaseTimestampModel):
    """Schema for prompt response."""
    title: str
    description: Optional[str]
    content: str
    prompt_type: PromptType
    status: PromptStatus
    version: str
    category_id: Optional[int]
    usage_count: int
    last_used_at: Optional[datetime]
    is_public: bool
    is_favorite: bool
    is_template: bool
    template_variables: Optional[Dict[str, Any]]
    source_url: Optional[str]
    source_type: Optional[str]
    
    # Relationships
    category: Optional[CategoryResponse]
    tags: List[TagResponse]
    
    @validator('template_variables', pre=True)
    def parse_template_variables(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class PromptListResponse(BaseTimestampModel):
    """Schema for prompt list response (lighter version)."""
    title: str
    description: Optional[str]
    prompt_type: PromptType
    status: PromptStatus
    version: str
    usage_count: int
    last_used_at: Optional[datetime]
    is_public: bool
    is_favorite: bool
    is_template: bool
    
    # Relationships (names only for performance)
    category_name: Optional[str] = None
    tag_names: List[str] = []
    
    class Config:
        from_attributes = True


class PromptSearchParams(BaseModel):
    """Schema for prompt search parameters."""
    search: Optional[str] = Field(None, description="Search query")
    category_id: Optional[int] = Field(None, description="Filter by category")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    prompt_type: Optional[PromptType] = Field(None, description="Filter by type")
    status: Optional[PromptStatus] = Field(None, description="Filter by status")
    is_public: Optional[bool] = Field(None, description="Filter by public status")
    is_favorite: Optional[bool] = Field(None, description="Filter by favorite status")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v.lower()


class PromptUseResponse(BaseModel):
    """Schema for prompt usage response."""
    message: str
    usage_count: int
    last_used_at: datetime