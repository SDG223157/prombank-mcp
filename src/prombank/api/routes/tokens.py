"""API Token management routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...auth import get_current_user
from ...models.user import User
from ...services.token_service import TokenService
from ...schemas.token import TokenCreate, TokenResponse

router = APIRouter()


def get_token_service(db: Session = Depends(get_db)) -> TokenService:
    """Get token service instance."""
    return TokenService(db)


@router.post("/", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def create_token(
    token_data: TokenCreate,
    current_user: User = Depends(get_current_user),
    service: TokenService = Depends(get_token_service)
):
    """Create a new API token."""
    try:
        token = service.create_token(
            user_id=current_user.id,
            name=token_data.name,
            description=token_data.description
        )
        return token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[TokenResponse])
async def get_user_tokens(
    current_user: User = Depends(get_current_user),
    service: TokenService = Depends(get_token_service)
):
    """Get all tokens for the current user."""
    return service.get_user_tokens(current_user.id)


@router.delete("/{token_id}")
async def delete_token(
    token_id: int,
    current_user: User = Depends(get_current_user),
    service: TokenService = Depends(get_token_service)
):
    """Delete a token."""
    success = service.delete_token(token_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    return {"message": "Token deleted successfully"}