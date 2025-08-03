"""Tag management service."""

from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.prompt import PromptTag, prompt_tags


class TagService:
    """Service for managing prompt tags."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_tag(
        self,
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> PromptTag:
        """Create a new tag."""
        tag = PromptTag(
            name=name,
            description=description,
            color=color,
        )
        
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        
        return tag
    
    def get_tag(self, tag_id: int) -> Optional[PromptTag]:
        """Get a tag by ID."""
        return self.db.query(PromptTag).filter(PromptTag.id == tag_id).first()
    
    def get_tag_by_name(self, name: str) -> Optional[PromptTag]:
        """Get a tag by name."""
        return self.db.query(PromptTag).filter(PromptTag.name == name).first()
    
    def get_tags(self) -> List[PromptTag]:
        """Get all tags."""
        return self.db.query(PromptTag).order_by(PromptTag.name).all()
    
    def get_popular_tags(self, limit: int = 20) -> List[tuple]:
        """Get most used tags with usage counts."""
        return (
            self.db.query(
                PromptTag.id,
                PromptTag.name,
                PromptTag.description,
                PromptTag.color,
                func.count(prompt_tags.c.prompt_id).label('usage_count')
            )
            .outerjoin(prompt_tags)
            .group_by(PromptTag.id)
            .order_by(func.count(prompt_tags.c.prompt_id).desc())
            .limit(limit)
            .all()
        )
    
    def search_tags(self, query: str, limit: int = 10) -> List[PromptTag]:
        """Search tags by name."""
        return (
            self.db.query(PromptTag)
            .filter(PromptTag.name.ilike(f"%{query}%"))
            .order_by(PromptTag.name)
            .limit(limit)
            .all()
        )
    
    def update_tag(
        self,
        tag_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Optional[PromptTag]:
        """Update a tag."""
        tag = self.get_tag(tag_id)
        if not tag:
            return None
        
        if name is not None:
            tag.name = name
        
        if description is not None:
            tag.description = description
        
        if color is not None:
            tag.color = color
        
        self.db.commit()
        self.db.refresh(tag)
        
        return tag
    
    def delete_tag(self, tag_id: int) -> bool:
        """Delete a tag."""
        tag = self.get_tag(tag_id)
        if not tag:
            return False
        
        self.db.delete(tag)
        self.db.commit()
        
        return True
    
    def get_or_create_tag(self, name: str) -> PromptTag:
        """Get existing tag or create new one."""
        tag = self.get_tag_by_name(name)
        if not tag:
            tag = self.create_tag(name)
        return tag