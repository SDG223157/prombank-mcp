"""Token service for API token management."""

import secrets
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.token import APIToken


class TokenService:
    """Service for managing API tokens."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_token(self, user_id: int, name: str, description: Optional[str] = None) -> dict:
        """Create a new API token for a user."""
        # Generate a secure token
        token_value = f"pb_{secrets.token_urlsafe(32)}"
        
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
        
        # Return the response with the plaintext token (only shown once)
        return {
            "id": api_token.id,
            "name": api_token.name,
            "description": api_token.description,
            "token": token_value,  # Only shown during creation
            "created_at": api_token.created_at,
            "last_used_at": api_token.last_used_at
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
    
    def delete_token(self, token_id: str, user_id: int) -> bool:
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
    
    def verify_token(self, token_value: str) -> Optional[APIToken]:
        """Verify a token and return the associated token record."""
        token_hash = self._hash_token(token_value)
        
        token = self.db.query(APIToken).filter(
            APIToken.token_hash == token_hash,
            APIToken.is_active == True
        ).first()
        
        if token:
            # Update last used timestamp
            token.last_used_at = datetime.utcnow()
            self.db.commit()
        
        return token
    
    def _hash_token(self, token_value: str) -> str:
        """Hash a token value for storage."""
        import hashlib
        return hashlib.sha256(token_value.encode()).hexdigest()