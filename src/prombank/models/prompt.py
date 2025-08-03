"""Prompt-related database models."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, 
    Table, Column, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PromptStatus(str, Enum):
    """Prompt status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class PromptType(str, Enum):
    """Prompt type enumeration."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TEMPLATE = "template"
    FUNCTION = "function"


# Association table for many-to-many relationship between prompts and tags
prompt_tags = Table(
    'prompt_tags',
    Base.metadata,
    Column('prompt_id', Integer, ForeignKey('prompts.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)


class PromptCategory(Base):
    """Prompt category model."""
    
    __tablename__ = "categories"
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color code
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    prompts: Mapped[List["Prompt"]] = relationship("Prompt", back_populates="category")
    
    def __repr__(self) -> str:
        return f"<PromptCategory(name='{self.name}')>"


class PromptTag(Base):
    """Prompt tag model."""
    
    __tablename__ = "tags"
    
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color code
    
    # Relationships
    prompts: Mapped[List["Prompt"]] = relationship(
        "Prompt", 
        secondary=prompt_tags, 
        back_populates="tags"
    )
    
    def __repr__(self) -> str:
        return f"<PromptTag(name='{self.name}')>"


class Prompt(Base):
    """Main prompt model."""
    
    __tablename__ = "prompts"
    
    # Basic information
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata
    prompt_type: Mapped[PromptType] = mapped_column(String(20), default=PromptType.USER)
    status: Mapped[PromptStatus] = mapped_column(String(20), default=PromptStatus.ACTIVE)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    
    # Categorization
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.id"), 
        nullable=True,
        index=True
    )
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Flags
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Template variables (JSON string for variable definitions)
    template_variables: Mapped[Optional[str]] = mapped_column(Text)
    
    # Source information (for imported prompts)
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    import_hash: Mapped[Optional[str]] = mapped_column(String(64))  # SHA256 hash
    
    # Relationships
    category: Mapped[Optional["PromptCategory"]] = relationship(
        "PromptCategory", 
        back_populates="prompts"
    )
    tags: Mapped[List["PromptTag"]] = relationship(
        "PromptTag",
        secondary=prompt_tags,
        back_populates="prompts"
    )
    versions: Mapped[List["PromptVersion"]] = relationship(
        "PromptVersion",
        back_populates="prompt",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('ix_prompts_title_status', 'title', 'status'),
        Index('ix_prompts_type_status', 'prompt_type', 'status'),
        Index('ix_prompts_category_status', 'category_id', 'status'),
    )
    
    def __repr__(self) -> str:
        return f"<Prompt(title='{self.title}', type='{self.prompt_type}', status='{self.status}')>"


class PromptVersion(Base):
    """Prompt version history model."""
    
    __tablename__ = "prompt_versions"
    
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Change information
    change_log: Mapped[Optional[str]] = mapped_column(Text)
    is_major_change: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="versions")
    
    __table_args__ = (
        UniqueConstraint('prompt_id', 'version', name='uq_prompt_version'),
        Index('ix_prompt_versions_prompt_version', 'prompt_id', 'version'),
    )
    
    def __repr__(self) -> str:
        return f"<PromptVersion(prompt_id={self.prompt_id}, version='{self.version}')>"