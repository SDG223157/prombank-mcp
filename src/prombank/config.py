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
    
    # Logging
    log_level: str = "info"
    log_format: str = "json"
    log_file: str = "/app/logs/prombank.log"
    
    # CORS Configuration
    allowed_origins: str = "https://prombank.app,https://www.prombank.app"
    allowed_methods: str = "GET,POST,PUT,DELETE,OPTIONS"
    allowed_headers: str = "*"
    allow_credentials: bool = True
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600
    
    # Health Check
    health_check_enabled: bool = True
    health_check_path: str = "/health"
    
    # MCP Server
    mcp_server_name: str = "prombank-mcp"
    mcp_server_version: str = "1.0.0"
    
    # Legacy environment variables (for backwards compatibility)
    app_port: Optional[int] = None
    environment: Optional[str] = None
    
    # Coolify-specific variables (will be ignored but won't cause errors)
    source_commit: Optional[str] = None
    coolify_url: Optional[str] = None
    coolify_fqdn: Optional[str] = None
    coolify_branch: Optional[str] = None
    coolify_resource_uuid: Optional[str] = None
    coolify_container_name: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_prefix = "PROMBANK_"
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()

# Ensure data directory exists
settings.data_dir.mkdir(parents=True, exist_ok=True)

if settings.backup_dir:
    settings.backup_dir.mkdir(parents=True, exist_ok=True)