"""Protected prompt routes that require authentication."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...services.prompt_service import PromptService
from ...schemas import (
    PromptCreate, PromptUpdate, PromptResponse,
    PaginationParams, PaginatedResponse, MessageResponse
)
from ...auth import get_current_user, get_current_user_optional
from ...models.user import User
from ...models.prompt import PromptStatus

router = APIRouter()


def get_prompt_service(db: Session = Depends(get_db)) -> PromptService:
    """Get prompt service instance."""
    return PromptService(db)


@router.post("/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt_data: PromptCreate,
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service)
):
    """Create a new prompt (requires authentication)."""
    try:
        prompt = service.create_prompt(
            title=prompt_data.title,
            content=prompt_data.content,
            description=prompt_data.description,
            prompt_type=prompt_data.prompt_type,
            category_id=prompt_data.category_id,
            tags=prompt_data.tags,
            is_public=prompt_data.is_public,
            is_template=prompt_data.is_template,
            template_variables=prompt_data.template_variables,
        )
        return prompt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/my-prompts", response_model=PaginatedResponse[PromptResponse])
async def get_my_prompts(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service)
):
    """Get current user's prompts."""
    
    # This would require adding user_id to the Prompt model
    # For now, return all prompts (you'd filter by user_id in a real implementation)
    prompts, total = service.get_prompts(
        skip=pagination.skip,
        limit=pagination.limit,
        status=PromptStatus.ACTIVE,
    )
    
    return PaginatedResponse(
        items=prompts,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
        has_next=pagination.skip + pagination.limit < total,
        has_prev=pagination.skip > 0,
    )


@router.get("/favorites", response_model=List[PromptResponse])
async def get_favorite_prompts(
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service)
):
    """Get user's favorite prompts."""
    
    prompts, _ = service.get_prompts(
        is_favorite=True,
        limit=100  # Reasonable limit for favorites
    )
    
    return prompts


@router.put("/{prompt_id}/favorite", response_model=MessageResponse)
async def toggle_favorite_prompt(
    prompt_id: int,
    current_user: User = Depends(get_current_user),
    service: PromptService = Depends(get_prompt_service)
):
    """Toggle favorite status of a prompt."""
    
    prompt = service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )
    
    # Toggle favorite status
    updated_prompt = service.update_prompt(
        prompt_id=prompt_id,
        is_favorite=not prompt.is_favorite
    )
    
    action = "added to" if updated_prompt.is_favorite else "removed from"
    return MessageResponse(
        message=f"Prompt {action} favorites"
    )