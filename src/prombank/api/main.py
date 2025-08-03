"""Main FastAPI application."""

import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db, init_db
from ..config import settings
from .routes import prompts, categories, tags, import_export

# Get the base directory for static files and templates
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"


# Create FastAPI app
app = FastAPI(
    title="Prombank MCP API",
    description="A comprehensive prompt management system with MCP server capabilities",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(prompts.router, prefix="/api/v1/prompts", tags=["prompts"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(tags.router, prefix="/api/v1/tags", tags=["tags"])
app.include_router(import_export.router, prefix="/api/v1/import-export", tags=["import-export"])

# Auth routes - temporarily disabled until dependencies are resolved
# from .routes import auth
# app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])


@app.get("/app", response_class=HTMLResponse)
async def main_interface(request: Request):
    """Serve the main prompt management interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main prompt management interface."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api", response_model=dict)
async def api_info():
    """API information endpoint."""
    return {
        "message": "Prombank MCP API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "app": "/app",
    }


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Simple database query to check connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "version": "0.1.0",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"}
    )