"""Tag management API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...database import get_db
from ...services.tag_service import TagService
from ...schemas import (
    TagCreate, TagUpdate, TagResponse, TagWithCountResponse,
    MessageResponse
)

router = APIRouter()


def get_tag_service(db: Session = Depends(get_db)) -> TagService:
    """Get tag service instance."""
    return TagService(db)


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    service: TagService = Depends(get_tag_service)
):
    """Create a new tag."""
    try:
        tag = service.create_tag(
            name=tag_data.name,
            description=tag_data.description,
            color=tag_data.color,
        )
        return tag
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[TagResponse])
async def get_tags(
    service: TagService = Depends(get_tag_service)
):
    """Get all tags."""
    tags = service.get_tags()
    return tags


@router.get("/popular", response_model=List[TagWithCountResponse])
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=100),
    service: TagService = Depends(get_tag_service)
):
    """Get most popular tags with usage counts."""
    tags_with_counts = service.get_popular_tags(limit)
    
    result = []
    for tag_data in tags_with_counts:
        tag_response = TagWithCountResponse(
            id=tag_data.id,
            name=tag_data.name,
            description=tag_data.description,
            color=tag_data.color,
            usage_count=tag_data.usage_count,
            created_at=tag_data.created_at if hasattr(tag_data, 'created_at') else None,
            updated_at=tag_data.updated_at if hasattr(tag_data, 'updated_at') else None,
        )
        result.append(tag_response)
    
    return result


@router.get("/search", response_model=List[TagResponse])
async def search_tags(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    service: TagService = Depends(get_tag_service)
):
    """Search tags by name."""
    tags = service.search_tags(q, limit)
    return tags


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int,
    service: TagService = Depends(get_tag_service)
):
    """Get a specific tag by ID."""
    tag = service.get_tag(tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    service: TagService = Depends(get_tag_service)
):
    """Update a tag."""
    tag = service.update_tag(
        tag_id=tag_id,
        name=tag_data.name,
        description=tag_data.description,
        color=tag_data.color,
    )
    
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    return tag


@router.delete("/{tag_id}", response_model=MessageResponse)
async def delete_tag(
    tag_id: int,
    service: TagService = Depends(get_tag_service)
):
    """Delete a tag."""
    success = service.delete_tag(tag_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    
    return MessageResponse(message="Tag deleted successfully")