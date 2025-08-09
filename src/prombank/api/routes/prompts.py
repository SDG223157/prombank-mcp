"""Prompt management API routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response, PlainTextResponse
from sqlalchemy.orm import Session

from ...database import get_db
from ...services.prompt_service import PromptService
from ...schemas import (
    PromptCreate, PromptUpdate, PromptResponse, PromptListResponse,
    PromptSearchParams, PromptUseResponse, PromptVersionResponse,
    PaginationParams, PaginatedResponse, MessageResponse
)
from ...models.prompt import PromptType, PromptStatus

router = APIRouter()


def get_prompt_service(db: Session = Depends(get_db)) -> PromptService:
    """Get prompt service instance."""
    return PromptService(db)


@router.post("/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    prompt_data: PromptCreate,
    service: PromptService = Depends(get_prompt_service)
):
    """Create a new prompt."""
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


@router.get("/", response_model=PaginatedResponse[PromptListResponse])
async def get_prompts(
    pagination: PaginationParams = Depends(),
    search_params: PromptSearchParams = Depends(),
    service: PromptService = Depends(get_prompt_service)
):
    """Get prompts with filtering and pagination."""
    prompts, total = service.get_prompts(
        skip=pagination.skip,
        limit=pagination.limit,
        search=search_params.search,
        category_id=search_params.category_id,
        tags=search_params.tags,
        prompt_type=search_params.prompt_type,
        status=search_params.status,
        is_public=search_params.is_public,
        is_favorite=search_params.is_favorite,
        sort_by=search_params.sort_by,
        sort_order=search_params.sort_order,
    )
    
    # Convert to list response format
    prompt_list = []
    for prompt in prompts:
        prompt_item = PromptListResponse.from_orm(prompt)
        prompt_item.category_name = prompt.category.name if prompt.category else None
        prompt_item.tag_names = [tag.name for tag in prompt.tags]
        prompt_list.append(prompt_item)
    
    return PaginatedResponse(
        items=prompt_list,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
        has_next=pagination.skip + pagination.limit < total,
        has_prev=pagination.skip > 0,
    )


@router.get("/search", response_model=List[PromptListResponse])
async def search_prompts(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    service: PromptService = Depends(get_prompt_service)
):
    """Search prompts by content."""
    prompts = service.search_prompts(q, limit)
    
    result = []
    for prompt in prompts:
        prompt_item = PromptListResponse.from_orm(prompt)
        prompt_item.category_name = prompt.category.name if prompt.category else None
        prompt_item.tag_names = [tag.name for tag in prompt.tags]
        result.append(prompt_item)
    
    return result


@router.get("/popular", response_model=List[PromptListResponse])
async def get_popular_prompts(
    limit: int = Query(10, ge=1, le=50),
    service: PromptService = Depends(get_prompt_service)
):
    """Get most popular prompts."""
    prompts = service.get_popular_prompts(limit)
    
    result = []
    for prompt in prompts:
        prompt_item = PromptListResponse.from_orm(prompt)
        prompt_item.category_name = prompt.category.name if prompt.category else None
        prompt_item.tag_names = [tag.name for tag in prompt.tags]
        result.append(prompt_item)
    
    return result


@router.get("/recent", response_model=List[PromptListResponse])
async def get_recent_prompts(
    limit: int = Query(10, ge=1, le=50),
    service: PromptService = Depends(get_prompt_service)
):
    """Get recently created prompts."""
    prompts = service.get_recent_prompts(limit)
    
    result = []
    for prompt in prompts:
        prompt_item = PromptListResponse.from_orm(prompt)
        prompt_item.category_name = prompt.category.name if prompt.category else None
        prompt_item.tag_names = [tag.name for tag in prompt.tags]
        result.append(prompt_item)
    
    return result


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: int,
    service: PromptService = Depends(get_prompt_service)
):
    """Get a specific prompt by ID."""
    prompt = service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )
    return prompt


@router.get("/{prompt_id}/raw")
async def get_prompt_raw(
    prompt_id: int,
    include_metadata: bool = Query(False, description="Include title/description as Markdown"),
    download: bool = Query(False, description="Force download instead of inline view"),
    service: PromptService = Depends(get_prompt_service)
):
    """Return the prompt content as plain text (or Markdown if including metadata).

    This is useful for a Notepad/TextEdit-style view or direct download.
    """
    prompt = service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )

    if include_metadata:
        body = []
        if prompt.title:
            body.append(f"# {prompt.title}")
        if prompt.description:
            body.append("")
            body.append(prompt.description)
        body.append("")
        body.append(prompt.content or "")
        text = "\n".join(body)
        headers = {}
        if download:
            headers["Content-Disposition"] = f"attachment; filename=prompt_{prompt_id}.md"
        return Response(content=text, media_type="text/markdown", headers=headers)
    else:
        headers = {}
        if download:
            headers["Content-Disposition"] = f"attachment; filename=prompt_{prompt_id}.txt"
        return PlainTextResponse(content=prompt.content or "", headers=headers)


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: int,
    prompt_data: PromptUpdate,
    service: PromptService = Depends(get_prompt_service)
):
    """Update a prompt."""
    prompt = service.update_prompt(
        prompt_id=prompt_id,
        title=prompt_data.title,
        content=prompt_data.content,
        description=prompt_data.description,
        category_id=prompt_data.category_id,
        tags=prompt_data.tags,
        status=prompt_data.status,
        is_public=prompt_data.is_public,
        is_favorite=prompt_data.is_favorite,
        template_variables=prompt_data.template_variables,
        create_version=prompt_data.create_version,
        version_comment=prompt_data.version_comment,
    )
    
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )
    
    return prompt


@router.delete("/{prompt_id}", response_model=MessageResponse)
async def delete_prompt(
    prompt_id: int,
    service: PromptService = Depends(get_prompt_service)
):
    """Delete a prompt."""
    success = service.delete_prompt(prompt_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )
    
    return MessageResponse(message="Prompt deleted successfully")


@router.post("/{prompt_id}/archive", response_model=PromptResponse)
async def archive_prompt(
    prompt_id: int,
    service: PromptService = Depends(get_prompt_service)
):
    """Archive a prompt."""
    prompt = service.archive_prompt(prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )
    
    return prompt


@router.post("/{prompt_id}/use", response_model=PromptUseResponse)
async def use_prompt(
    prompt_id: int,
    service: PromptService = Depends(get_prompt_service)
):
    """Record prompt usage."""
    prompt = service.use_prompt(prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )
    
    return PromptUseResponse(
        message="Prompt usage recorded",
        usage_count=prompt.usage_count,
        last_used_at=prompt.last_used_at
    )


@router.get("/{prompt_id}/versions", response_model=List[PromptVersionResponse])
async def get_prompt_versions(
    prompt_id: int,
    service: PromptService = Depends(get_prompt_service)
):
    """Get all versions of a prompt."""
    # First check if prompt exists
    prompt = service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found"
        )
    
    versions = service.get_prompt_versions(prompt_id)
    return versions