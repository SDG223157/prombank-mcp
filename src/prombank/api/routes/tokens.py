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


@router.get("/debug/db")
async def test_database():
    """Test database connectivity for tokens."""
    try:
        from ...database import get_db
        from ...models.token import APIToken
        db = next(get_db())
        
        # Test if we can query the APIToken table
        count = db.query(APIToken).count()
        
        return {
            "database": "connected",
            "api_tokens_table": "exists",
            "token_count": count,
            "message": "Database connectivity test passed"
        }
    except Exception as e:
        import traceback
        return {
            "database": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "Database connectivity test failed"
        }


@router.get("/debug/auth")
async def test_auth(current_user: User = Depends(get_current_user)):
    """Test authentication for tokens API."""
    return {
        "authenticated": True,
        "user_id": current_user.id,
        "user_email": current_user.email,
        "message": "Authentication test passed"
    }


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