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


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify tokens API is working."""
    return {"message": "Tokens API is working!", "timestamp": "2025-08-09"}


def get_token_service(db: Session = Depends(get_db)) -> TokenService:
    """Get token service instance."""
    return TokenService(db)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_token(
    token_data: TokenCreate,
    current_user: User = Depends(get_current_user),
    service: TokenService = Depends(get_token_service)
):
    """Create a new API token."""
    try:
        print(f"🔑 Creating token for user {current_user.id}: {token_data.name}")
        token = service.create_token(
            user_id=current_user.id,
            name=token_data.name,
            description=token_data.description
        )
        print(f"✅ Token created successfully: {token['id']}")
        return token
    except Exception as e:
        print(f"❌ Error creating token: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create token: {str(e)}"
        )


@router.get("/")
async def get_user_tokens(
    current_user: User = Depends(get_current_user),
    service: TokenService = Depends(get_token_service)
):
    """Get all tokens for the current user."""
    try:
        print(f"📋 Loading tokens for user {current_user.id}")
        tokens = service.get_user_tokens(current_user.id)
        print(f"✅ Found {len(tokens)} tokens")
        # Return structure matching working implementation
        return {
            "tokens": tokens,
            "count": len(tokens)
        }
    except Exception as e:
        print(f"❌ Error loading tokens: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load tokens: {str(e)}"
        )


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