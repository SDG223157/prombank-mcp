"""Configuration settings for Prombank MCP."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "sqlite:///./prombank.db"
    
    # Server
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
    
    # MCP Server
    mcp_host: str = "localhost"
    mcp_port: int = 8001
    
    # Storage
    data_dir: Path = Path.home() / ".prombank"
    backup_dir: Optional[Path] = None
    
    # Security
    secret_key: str = "your-secret-key-here"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    
    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "https://prombank.app/api/auth/google/callback"
    
    # Frontend URL for redirects
    frontend_url: str = "https://prombank.app"
    
    # JWT
    jwt_algorithm: str = "HS256"
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    class Config:
        env_file = ".env"
        env_prefix = "PROMBANK_"


# Global settings instance
settings = Settings()

# Ensure data directory exists
settings.data_dir.mkdir(parents=True, exist_ok=True)

if settings.backup_dir:
    settings.backup_dir.mkdir(parents=True, exist_ok=True)