"""Category management service."""

from typing import List, Optional
from sqlalchemy.orm import Session

from ..models.prompt import PromptCategory


class CategoryService:
    """Service for managing prompt categories."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_category(
        self,
        name: str,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> PromptCategory:
        """Create a new category."""
        category = PromptCategory(
            name=name,
            description=description,
            color=color,
        )
        
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        
        return category
    
    def get_category(self, category_id: int) -> Optional[PromptCategory]:
        """Get a category by ID."""
        return self.db.query(PromptCategory).filter(PromptCategory.id == category_id).first()
    
    def get_category_by_name(self, name: str) -> Optional[PromptCategory]:
        """Get a category by name."""
        return self.db.query(PromptCategory).filter(PromptCategory.name == name).first()
    
    def get_categories(self, active_only: bool = True) -> List[PromptCategory]:
        """Get all categories."""
        query = self.db.query(PromptCategory)
        
        if active_only:
            query = query.filter(PromptCategory.is_active == True)
        
        return query.order_by(PromptCategory.name).all()
    
    def update_category(
        self,
        category_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[PromptCategory]:
        """Update a category."""
        category = self.get_category(category_id)
        if not category:
            return None
        
        if name is not None:
            category.name = name
        
        if description is not None:
            category.description = description
        
        if color is not None:
            category.color = color
        
        if is_active is not None:
            category.is_active = is_active
        
        self.db.commit()
        self.db.refresh(category)
        
        return category
    
    def delete_category(self, category_id: int) -> bool:
        """Delete a category."""
        category = self.get_category(category_id)
        if not category:
            return False
        
        # Check if category has prompts
        if category.prompts:
            # Move prompts to "General" category or set to None
            general_category = self.get_category_by_name("General")
            for prompt in category.prompts:
                prompt.category_id = general_category.id if general_category else None
        
        self.db.delete(category)
        self.db.commit()
        
        return True