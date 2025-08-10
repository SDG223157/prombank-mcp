"""Token service for API token management."""

import secrets
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.token import APIToken
from ..models.user import User


class TokenService:
    """Service for managing API tokens."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_token(self, user_id: int, name: str, description: Optional[str] = None) -> dict:
        """Create a new API token for a user."""
        # Generate a secure token (match working implementation format)
        import secrets
        prefix = secrets.token_hex(4)
        random_part = secrets.token_hex(20)
        token_value = f"{prefix}_{random_part}"
        
        # Create token record
        api_token = APIToken(
            user_id=user_id,
            name=name,
            description=description,
            token_hash=self._hash_token(token_value),
            created_at=datetime.utcnow(),
            last_used_at=None
        )
        
        self.db.add(api_token)
        self.db.commit()
        self.db.refresh(api_token)
        
        # Return response matching working implementation structure
        return {
            "message": "API token created successfully",
            "token": {
                "id": api_token.id,
                "name": api_token.name,
                "description": api_token.description,
                "accessLink": token_value,  # This is the key field the frontend expects
                "preview": f"{token_value[:12]}...",
                "created_at": api_token.created_at,
                "last_used_at": api_token.last_used_at
            },
            "warning": "Save this token securely - it cannot be viewed again!"
        }
    
    def get_user_tokens(self, user_id: int) -> List[dict]:
        """Get all tokens for a user (without token values)."""
        tokens = self.db.query(APIToken).filter(
            APIToken.user_id == user_id,
            APIToken.is_active == True
        ).order_by(APIToken.created_at.desc()).all()
        
        return [
            {
                "id": token.id,
                "name": token.name,
                "description": token.description,
                "created_at": token.created_at,
                "last_used_at": token.last_used_at
            }
            for token in tokens
        ]
    
    def delete_token(self, token_id: int, user_id: int) -> bool:
        """Delete a token (soft delete)."""
        token = self.db.query(APIToken).filter(
            APIToken.id == token_id,
            APIToken.user_id == user_id,
            APIToken.is_active == True
        ).first()
        
        if not token:
            return False
        
        token.is_active = False
        self.db.commit()
        return True
    
    def verify_token(self, token_value: str) -> Optional[dict]:
        """Verify a token and return the associated token record with user info."""
        token_hash = self._hash_token(token_value)
        
        token = self.db.query(APIToken).filter(
            APIToken.token_hash == token_hash,
            APIToken.is_active == True
        ).first()
        
        if token:
            # Update last used timestamp
            token.last_used_at = datetime.utcnow()
            self.db.commit()
            
            # Get associated user
            user = self.db.query(User).filter(User.id == token.user_id).first()
            
            return {
                "token": token,
                "user": user
            }
        
        return None
    
    def _hash_token(self, token_value: str) -> str:
        """Hash a token value for storage."""
        import hashlib
        return hashlib.sha256(token_value.encode()).hexdigest()