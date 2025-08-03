"""Database configuration and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session

from .config import settings
from .models.base import Base


# Synchronous database engine and session
connect_args = {}
if "sqlite" in settings.database_url:
    connect_args = {"check_same_thread": False}
elif "mysql" in settings.database_url:
    connect_args = {
        "charset": "utf8mb4",
        "use_unicode": True,
    }

sync_engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False
)

# Async database setup (for future use)
if settings.database_url.startswith("sqlite"):
    async_database_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
elif settings.database_url.startswith("mysql"):
    async_database_url = settings.database_url.replace("mysql+pymysql://", "mysql+aiomysql://")
else:
    async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

async_engine = create_async_engine(
    async_database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False
)


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=sync_engine)


def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Initialize database on import
def init_db():
    """Initialize the database with tables and default data."""
    create_tables()
    
    # Create default categories if they don't exist
    with SessionLocal() as db:
        from .models.prompt import PromptCategory
        
        default_categories = [
            {"name": "General", "description": "General purpose prompts", "color": "#6366f1"},
            {"name": "Coding", "description": "Programming and development prompts", "color": "#10b981"},
            {"name": "Writing", "description": "Content creation and writing prompts", "color": "#f59e0b"},
            {"name": "Analysis", "description": "Data analysis and research prompts", "color": "#ef4444"},
            {"name": "Creative", "description": "Creative and artistic prompts", "color": "#8b5cf6"},
        ]
        
        for cat_data in default_categories:
            existing = db.query(PromptCategory).filter(PromptCategory.name == cat_data["name"]).first()
            if not existing:
                category = PromptCategory(**cat_data)
                db.add(category)
        
        db.commit()


if __name__ == "__main__":
    init_db()