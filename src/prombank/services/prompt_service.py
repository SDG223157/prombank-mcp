"""Prompt management service with CRUD operations."""

import hashlib
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import Session, joinedload

from ..models.prompt import Prompt, PromptStatus, PromptType, PromptVersion, PromptTag
from ..models.base import Base


class PromptService:
    """Service for managing prompts."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_prompt(
        self,
        title: str,
        content: str,
        description: Optional[str] = None,
        prompt_type: PromptType = PromptType.USER,
        category_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        is_public: bool = False,
        is_template: bool = False,
        template_variables: Optional[Dict[str, Any]] = None,
        source_url: Optional[str] = None,
        source_type: Optional[str] = None,
    ) -> Prompt:
        """Create a new prompt."""
        
        # Generate import hash for content deduplication
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        prompt = Prompt(
            title=title,
            content=content,
            description=description,
            prompt_type=prompt_type,
            category_id=category_id,
            is_public=is_public,
            is_template=is_template,
            template_variables=json.dumps(template_variables) if template_variables else None,
            source_url=source_url,
            source_type=source_type,
            import_hash=content_hash,
        )
        
        self.db.add(prompt)
        self.db.flush()  # To get the ID
        
        # Add tags if provided
        if tags:
            self._add_tags_to_prompt(prompt, tags)
        
        # Create initial version
        self._create_version(prompt, "1.0.0", "Initial version")
        
        self.db.commit()
        self.db.refresh(prompt)
        
        return prompt
    
    def get_prompt(self, prompt_id: int, include_versions: bool = False) -> Optional[Prompt]:
        """Get a prompt by ID."""
        query = self.db.query(Prompt).options(
            joinedload(Prompt.category),
            joinedload(Prompt.tags)
        )
        
        if include_versions:
            query = query.options(joinedload(Prompt.versions))
        
        return query.filter(Prompt.id == prompt_id).first()
    
    def get_prompts(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        prompt_type: Optional[PromptType] = None,
        status: Optional[PromptStatus] = None,
        is_public: Optional[bool] = None,
        is_favorite: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Prompt], int]:
        """Get prompts with filtering and pagination."""
        
        query = self.db.query(Prompt).options(
            joinedload(Prompt.category),
            joinedload(Prompt.tags)
        )
        
        # Apply filters
        filters = []
        
        if search:
            search_filter = or_(
                Prompt.title.ilike(f"%{search}%"),
                Prompt.description.ilike(f"%{search}%"),
                Prompt.content.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        if category_id is not None:
            filters.append(Prompt.category_id == category_id)
        
        if prompt_type is not None:
            filters.append(Prompt.prompt_type == prompt_type)
        
        if status is not None:
            filters.append(Prompt.status == status)
        else:
            # By default, exclude archived and deprecated prompts
            filters.append(Prompt.status.in_([PromptStatus.ACTIVE, PromptStatus.DRAFT]))
        
        if is_public is not None:
            filters.append(Prompt.is_public == is_public)
        
        if is_favorite is not None:
            filters.append(Prompt.is_favorite == is_favorite)
        
        if tags:
            # Filter by tags (prompts that have ALL specified tags)
            for tag_name in tags:
                query = query.join(Prompt.tags).filter(PromptTag.name == tag_name)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Count total results
        total = query.count()
        
        # Apply sorting
        sort_column = getattr(Prompt, sort_by, Prompt.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        prompts = query.offset(skip).limit(limit).all()
        
        return prompts, total
    
    def update_prompt(
        self,
        prompt_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        status: Optional[PromptStatus] = None,
        is_public: Optional[bool] = None,
        is_favorite: Optional[bool] = None,
        template_variables: Optional[Dict[str, Any]] = None,
        create_version: bool = False,
        version_comment: Optional[str] = None,
    ) -> Optional[Prompt]:
        """Update a prompt."""
        
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None
        
        # Store original content for version creation
        original_content = prompt.content
        original_title = prompt.title
        
        # Update fields
        if title is not None:
            prompt.title = title
        
        if content is not None:
            prompt.content = content
            # Update import hash
            prompt.import_hash = hashlib.sha256(content.encode()).hexdigest()
        
        if description is not None:
            prompt.description = description
        
        if category_id is not None:
            prompt.category_id = category_id
        
        if status is not None:
            prompt.status = status
        
        if is_public is not None:
            prompt.is_public = is_public
        
        if is_favorite is not None:
            prompt.is_favorite = is_favorite
        
        if template_variables is not None:
            prompt.template_variables = json.dumps(template_variables)
        
        # Update tags
        if tags is not None:
            # Remove existing tags
            prompt.tags.clear()
            # Add new tags
            self._add_tags_to_prompt(prompt, tags)
        
        # Create version if requested or content changed significantly
        if create_version or (content and content != original_content):
            # Increment version
            latest_version = self._get_latest_version_number(prompt)
            new_version = self._increment_version(latest_version, major=create_version)
            
            self._create_version(
                prompt, 
                new_version, 
                version_comment or "Content updated",
                is_major_change=create_version
            )
            prompt.version = new_version
        
        prompt.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(prompt)
        
        return prompt
    
    def delete_prompt(self, prompt_id: int) -> bool:
        """Delete a prompt and all its versions."""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return False
        
        self.db.delete(prompt)
        self.db.commit()
        
        return True
    
    def archive_prompt(self, prompt_id: int) -> Optional[Prompt]:
        """Archive a prompt instead of deleting it."""
        return self.update_prompt(prompt_id, status=PromptStatus.ARCHIVED)
    
    def use_prompt(self, prompt_id: int) -> Optional[Prompt]:
        """Record prompt usage."""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None
        
        prompt.usage_count += 1
        prompt.last_used_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(prompt)
        
        return prompt
    
    def get_prompt_versions(self, prompt_id: int) -> List[PromptVersion]:
        """Get all versions of a prompt."""
        return (
            self.db.query(PromptVersion)
            .filter(PromptVersion.prompt_id == prompt_id)
            .order_by(desc(PromptVersion.created_at))
            .all()
        )
    
    def get_popular_prompts(self, limit: int = 10) -> List[Prompt]:
        """Get most used prompts."""
        return (
            self.db.query(Prompt)
            .filter(Prompt.status == PromptStatus.ACTIVE)
            .order_by(desc(Prompt.usage_count))
            .limit(limit)
            .all()
        )
    
    def get_recent_prompts(self, limit: int = 10) -> List[Prompt]:
        """Get recently created prompts."""
        return (
            self.db.query(Prompt)
            .filter(Prompt.status == PromptStatus.ACTIVE)
            .order_by(desc(Prompt.created_at))
            .limit(limit)
            .all()
        )
    
    def search_prompts(self, query: str, limit: int = 20) -> List[Prompt]:
        """Full-text search for prompts."""
        search_filter = or_(
            Prompt.title.ilike(f"%{query}%"),
            Prompt.description.ilike(f"%{query}%"),
            Prompt.content.ilike(f"%{query}%")
        )
        
        return (
            self.db.query(Prompt)
            .options(joinedload(Prompt.category), joinedload(Prompt.tags))
            .filter(search_filter)
            .filter(Prompt.status == PromptStatus.ACTIVE)
            .order_by(desc(Prompt.usage_count))
            .limit(limit)
            .all()
        )
    
    def get_duplicate_prompts(self, content_hash: str) -> List[Prompt]:
        """Find prompts with the same content hash."""
        return (
            self.db.query(Prompt)
            .filter(Prompt.import_hash == content_hash)
            .all()
        )
    
    def _add_tags_to_prompt(self, prompt: Prompt, tag_names: List[str]):
        """Add tags to a prompt, creating tags if they don't exist."""
        for tag_name in tag_names:
            tag = self.db.query(PromptTag).filter(PromptTag.name == tag_name).first()
            if not tag:
                tag = PromptTag(name=tag_name)
                self.db.add(tag)
                self.db.flush()
            
            if tag not in prompt.tags:
                prompt.tags.append(tag)
    
    def _create_version(
        self, 
        prompt: Prompt, 
        version: str, 
        change_log: str,
        is_major_change: bool = False
    ):
        """Create a new version record for a prompt."""
        version_record = PromptVersion(
            prompt_id=prompt.id,
            version=version,
            content=prompt.content,
            title=prompt.title,
            description=prompt.description,
            change_log=change_log,
            is_major_change=is_major_change
        )
        
        self.db.add(version_record)
    
    def _get_latest_version_number(self, prompt: Prompt) -> str:
        """Get the latest version number for a prompt."""
        latest_version = (
            self.db.query(PromptVersion)
            .filter(PromptVersion.prompt_id == prompt.id)
            .order_by(desc(PromptVersion.created_at))
            .first()
        )
        
        return latest_version.version if latest_version else "1.0.0"
    
    def _increment_version(self, current_version: str, major: bool = False) -> str:
        """Increment version number."""
        try:
            parts = current_version.split(".")
            major_num = int(parts[0])
            minor_num = int(parts[1]) if len(parts) > 1 else 0
            patch_num = int(parts[2]) if len(parts) > 2 else 0
            
            if major:
                return f"{major_num + 1}.0.0"
            else:
                return f"{major_num}.{minor_num}.{patch_num + 1}"
        
        except (ValueError, IndexError):
            return "1.0.1"