"""API Token management routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...auth import get_current_user
from ...models.user import User
# from ...services.token_service import TokenService  # Temporarily commented out
from ...schemas.token import TokenCreate, TokenResponse

router = APIRouter()


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify tokens API is working."""
    return {"message": "Tokens API is working!", "timestamp": "2025-08-09"}


@router.post("/test")
async def test_post_endpoint():
    """Test POST endpoint to verify POST requests work."""
    print("🔥 POST test endpoint reached!")
    return {"message": "POST request successful!", "timestamp": "2025-08-09"}


@router.post("/simple")
async def simple_token_endpoint():
    """Simplified token endpoint without dependencies."""
    print("🔥 Simple token endpoint reached!")
    return {"message": "Simple endpoint works!", "timestamp": "2025-08-09"}


@router.post("/with-auth")
async def token_with_auth(current_user: User = Depends(get_current_user)):
    """Token endpoint with only auth dependency."""
    print(f"🔥 Auth-only endpoint reached! User: {current_user.id}")
    return {"message": f"Auth works for user {current_user.id}!", "timestamp": "2025-08-09"}


@router.post("/with-body")
async def token_with_body(token_data: TokenCreate):
    """Token endpoint with only body validation."""
    print(f"🔥 Body-only endpoint reached! Name: {token_data.name}")
    return {"message": f"Body validation works for {token_data.name}!", "timestamp": "2025-08-09"}


@router.post("/with-db")
async def token_with_db(db: Session = Depends(get_db)):
    """Token endpoint with only database dependency."""
    print("🔥 Database dependency endpoint reached!")
    try:
        # Try to import and create TokenService manually
        from ...services.token_service import TokenService
        print("🔥 TokenService imported successfully!")
        service = TokenService(db)
        print("🔥 TokenService created successfully!")
        return {"message": "Database service works!", "timestamp": "2025-08-09"}
    except Exception as e:
        print(f"❌ Error with TokenService: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": f"TokenService error: {str(e)}", "timestamp": "2025-08-09"}


@router.post("/combined")
async def token_combined(
    token_data: TokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Token endpoint with all dependencies except the actual service call."""
    print(f"🔥 Combined endpoint reached! User: {current_user.id}, Token: {token_data.name}")
    return {"message": f"All dependencies work! User: {current_user.id}, Token: {token_data.name}", "timestamp": "2025-08-09"}


@router.post("/test-service")
async def test_service_creation(
    token_data: TokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test TokenService creation and method call without commits."""
    print(f"🔥 Test service endpoint reached! User: {current_user.id}, Token: {token_data.name}")
    try:
        from ...services.token_service import TokenService
        print("✅ TokenService imported")
        
        service = TokenService(db)
        print("✅ TokenService created")
        
        # Test the method call but catch any errors
        result = service.create_token(
            user_id=current_user.id,
            name=token_data.name,
            description=token_data.description
        )
        print("✅ create_token method completed")
        return {"message": "Service method works!", "result": str(result), "timestamp": "2025-08-09"}
        
    except Exception as e:
        print(f"❌ Error in service test: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": f"Service error: {str(e)}", "timestamp": "2025-08-09"}


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


# def get_token_service(db: Session = Depends(get_db)) -> TokenService:
#     """Get token service instance."""
#     return TokenService(db)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_token(
    token_data: TokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API token."""
    print(f"🔥 POST /tokens endpoint reached! User: {current_user.id if current_user else 'None'}")
    try:
        from ...services.token_service import TokenService
        print("✅ TokenService imported in main endpoint")
        
        service = TokenService(db)
        print("✅ TokenService created in main endpoint")
        
        result = service.create_token(
            user_id=current_user.id,
            name=token_data.name,
            description=token_data.description
        )
        print("✅ create_token method completed in main endpoint")
        return result
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
    db: Session = Depends(get_db)
):
    """Get all tokens for the current user."""
    try:
        from ...services.token_service import TokenService
        service = TokenService(db)
        
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
    db: Session = Depends(get_db)
):
    """Delete a token."""
    from ...services.token_service import TokenService
    service = TokenService(db)
    
    success = service.delete_token(token_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    return {"message": "Token deleted successfully"}