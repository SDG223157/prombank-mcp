"""Category management API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...database import get_db
from ...services.category_service import CategoryService
from ...schemas import (
    CategoryCreate, CategoryUpdate, CategoryResponse, CategoryWithCountResponse,
    MessageResponse
)
from ...models.prompt import PromptCategory, Prompt

router = APIRouter()


def get_category_service(db: Session = Depends(get_db)) -> CategoryService:
    """Get category service instance."""
    return CategoryService(db)


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    service: CategoryService = Depends(get_category_service)
):
    """Create a new category."""
    try:
        category = service.create_category(
            name=category_data.name,
            description=category_data.description,
            color=category_data.color,
        )
        return category
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[CategoryWithCountResponse])
async def get_categories(
    active_only: bool = True,
    service: CategoryService = Depends(get_category_service),
    db: Session = Depends(get_db)
):
    """Get all categories with prompt counts."""
    categories = service.get_categories(active_only=active_only)
    
    # Add prompt counts
    result = []
    for category in categories:
        category_response = CategoryWithCountResponse.from_orm(category)
        
        # Count prompts in this category
        prompt_count = (
            db.query(func.count(Prompt.id))
            .filter(Prompt.category_id == category.id)
            .scalar()
        )
        category_response.prompt_count = prompt_count or 0
        
        result.append(category_response)
    
    return result


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service)
):
    """Get a specific category by ID."""
    category = service.get_category(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    service: CategoryService = Depends(get_category_service)
):
    """Update a category."""
    category = service.update_category(
        category_id=category_id,
        name=category_data.name,
        description=category_data.description,
        color=category_data.color,
        is_active=category_data.is_active,
    )
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


@router.delete("/{category_id}", response_model=MessageResponse)
async def delete_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service)
):
    """Delete a category."""
    success = service.delete_category(category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return MessageResponse(message="Category deleted successfully")