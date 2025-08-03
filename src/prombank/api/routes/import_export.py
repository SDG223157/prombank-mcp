"""Import/Export API routes."""

from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ...database import get_db
from ...services.import_export_service import ImportExportService
from ...schemas import MessageResponse, PromptListResponse

router = APIRouter()


def get_import_export_service(db: Session = Depends(get_db)) -> ImportExportService:
    """Get import/export service instance."""
    return ImportExportService(db)


@router.post("/import", response_model=dict)
async def import_prompts(
    file: UploadFile = File(..., description="File to import"),
    format_type: str = Form("json", description="Import format (json, csv, yaml, markdown, fabric)"),
    source_type: Optional[str] = Form(None, description="Source type for tracking"),
    default_category: Optional[str] = Form(None, description="Default category name"),
    skip_duplicates: bool = Form(True, description="Skip duplicate prompts"),
    update_existing: bool = Form(False, description="Update existing prompts"),
    service: ImportExportService = Depends(get_import_export_service)
):
    """Import prompts from uploaded file."""
    try:
        # Read file content
        content = await file.read()
        
        # Import prompts
        imported_prompts, errors = service.import_prompts(
            data=content,
            format_type=format_type,
            source_type=source_type,
            default_category=default_category,
            skip_duplicates=skip_duplicates,
            update_existing=update_existing,
        )
        
        return {
            "message": f"Import completed",
            "imported_count": len(imported_prompts),
            "error_count": len(errors),
            "errors": errors,
            "prompts": [
                {
                    "id": p.id,
                    "title": p.title,
                    "type": p.prompt_type.value,
                }
                for p in imported_prompts
            ]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Import failed: {str(e)}"
        )


@router.post("/import/fabric", response_model=dict)
async def import_fabric_patterns(
    patterns_dir: str = Form(..., description="Path to Fabric patterns directory"),
    skip_duplicates: bool = Form(True, description="Skip duplicate prompts"),
    service: ImportExportService = Depends(get_import_export_service)
):
    """Import prompts from Fabric patterns directory."""
    try:
        patterns_path = Path(patterns_dir)
        
        if not patterns_path.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Patterns directory not found: {patterns_dir}"
            )
        
        imported_prompts, errors = service.import_from_fabric_patterns(
            patterns_path,
            skip_duplicates=skip_duplicates
        )
        
        return {
            "message": "Fabric patterns import completed",
            "imported_count": len(imported_prompts),
            "error_count": len(errors),
            "errors": errors,
            "prompts": [
                {
                    "id": p.id,
                    "title": p.title,
                    "pattern_name": p.source_url,
                }
                for p in imported_prompts
            ]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fabric import failed: {str(e)}"
        )


@router.get("/export")
async def export_prompts(
    format_type: str = Query("json", description="Export format (json, csv, yaml, markdown)"),
    prompt_ids: Optional[List[int]] = Query(None, description="Specific prompt IDs to export"),
    include_versions: bool = Query(False, description="Include version history"),
    include_metadata: bool = Query(True, description="Include metadata"),
    service: ImportExportService = Depends(get_import_export_service)
):
    """Export prompts in various formats."""
    try:
        exported_data = service.export_prompts(
            format_type=format_type,
            prompt_ids=prompt_ids,
            include_versions=include_versions,
            include_metadata=include_metadata,
        )
        
        # Determine content type and filename
        content_types = {
            "json": "application/json",
            "csv": "text/csv",
            "yaml": "application/x-yaml",
            "markdown": "text/markdown",
        }
        
        extensions = {
            "json": "json",
            "csv": "csv", 
            "yaml": "yml",
            "markdown": "md",
        }
        
        content_type = content_types.get(format_type, "text/plain")
        extension = extensions.get(format_type, "txt")
        filename = f"prombank_export.{extension}"
        
        headers = {
            "Content-Disposition": f"attachment; filename={filename}"
        }
        
        return Response(
            content=exported_data,
            media_type=content_type,
            headers=headers
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export failed: {str(e)}"
        )


@router.post("/import/text", response_model=dict)
async def import_text_prompts(
    content: str = Form(..., description="Text content to import"),
    format_type: str = Form("markdown", description="Format type"),
    title: Optional[str] = Form(None, description="Title for single prompt"),
    category: Optional[str] = Form(None, description="Category name"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    service: ImportExportService = Depends(get_import_export_service)
):
    """Import prompts from text content."""
    try:
        # If it's a single prompt (has title), format as single item
        if title:
            prompt_data = [{
                "title": title,
                "content": content,
                "category": category,
                "tags": tags.split(",") if tags else None,
            }]
        else:
            # Parse as format
            prompt_data = service._parse_markdown(content) if format_type == "markdown" else [{"title": "Imported Prompt", "content": content}]
        
        imported_prompts = []
        errors = []
        
        for item in prompt_data:
            try:
                prompt = service._import_single_prompt(
                    item,
                    default_category_id=None,
                    skip_duplicates=True,
                    update_existing=False,
                )
                if prompt:
                    imported_prompts.append(prompt)
            except Exception as e:
                errors.append(str(e))
        
        return {
            "message": "Text import completed",
            "imported_count": len(imported_prompts),
            "error_count": len(errors),
            "errors": errors,
            "prompts": [
                {
                    "id": p.id,
                    "title": p.title,
                }
                for p in imported_prompts
            ]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Text import failed: {str(e)}"
        )