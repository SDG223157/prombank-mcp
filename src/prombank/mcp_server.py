"""MCP (Model Context Protocol) server implementation for Prombank."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, GetResourceRequest, ListResourcesRequest, ListToolsRequest
)
from pydantic import AnyUrl

from .database import SessionLocal, init_db
from .services import PromptService, CategoryService, TagService, ImportExportService
from .models.prompt import PromptStatus, PromptType
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global server instance
app = Server("prombank-mcp")


# MCP Tools Implementation

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_prompts",
            description="Search for prompts by title, content, or tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find prompts"
                    },
                    "category": {
                        "type": "string", 
                        "description": "Filter by category name (optional)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tag names (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_prompt",
            description="Get a specific prompt by ID with full details",
            inputSchema={
                "type": "object", 
                "properties": {
                    "prompt_id": {
                        "type": "integer",
                        "description": "The ID of the prompt to retrieve"
                    }
                },
                "required": ["prompt_id"]
            }
        ),
        Tool(
            name="create_prompt",
            description="Create a new prompt",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the prompt"
                    },
                    "content": {
                        "type": "string", 
                        "description": "Content of the prompt"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the prompt (optional)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category name (optional)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tag names (optional)"
                    },
                    "is_public": {
                        "type": "boolean",
                        "description": "Whether the prompt is public (default: false)",
                        "default": False
                    },
                    "is_template": {
                        "type": "boolean", 
                        "description": "Whether the prompt is a template (default: false)",
                        "default": False
                    }
                },
                "required": ["title", "content"]
            }
        ),
        Tool(
            name="update_prompt",
            description="Update an existing prompt",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt_id": {
                        "type": "integer",
                        "description": "ID of the prompt to update"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title (optional)"
                    },
                    "content": {
                        "type": "string",
                        "description": "New content (optional)"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description (optional)"
                    },
                    "category": {
                        "type": "string",
                        "description": "New category name (optional)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New list of tag names (optional)"
                    },
                    "create_version": {
                        "type": "boolean",
                        "description": "Create new version on update (default: false)",
                        "default": False
                    }
                },
                "required": ["prompt_id"]
            }
        ),
        Tool(
            name="delete_prompt",
            description="Delete a prompt by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt_id": {
                        "type": "integer",
                        "description": "ID of the prompt to delete"
                    }
                },
                "required": ["prompt_id"]
            }
        ),
        Tool(
            name="list_categories", 
            description="List all available categories",
            inputSchema={
                "type": "object",
                "properties": {
                    "active_only": {
                        "type": "boolean",
                        "description": "Only return active categories (default: true)",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="list_tags",
            description="List all available tags or search tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search query for tags (optional)"
                    },
                    "popular": {
                        "type": "boolean", 
                        "description": "Get popular tags with usage counts (default: false)",
                        "default": False
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 20)",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="import_prompts",
            description="Import prompts from text content",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Content to import"
                    },
                    "format_type": {
                        "type": "string",
                        "enum": ["json", "markdown", "yaml", "fabric"],
                        "description": "Format of the content (default: markdown)",
                        "default": "markdown"
                    },
                    "title": {
                        "type": "string", 
                        "description": "Title for single prompt import (optional)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Default category for imported prompts (optional)"
                    }
                },
                "required": ["content"]
            }
        ),
        Tool(
            name="export_prompts",
            description="Export prompts in specified format",
            inputSchema={
                "type": "object",
                "properties": {
                    "format_type": {
                        "type": "string",
                        "enum": ["json", "markdown", "yaml", "csv"],
                        "description": "Export format (default: json)",
                        "default": "json"
                    },
                    "prompt_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Specific prompt IDs to export (optional, exports all if not provided)"
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "description": "Include metadata in export (default: true)",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="get_popular_prompts",
            description="Get most frequently used prompts",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="get_recent_prompts", 
            description="Get recently created prompts",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    
    # Create database session
    db = SessionLocal()
    
    try:
        if name == "search_prompts":
            return await _search_prompts(db, arguments)
        elif name == "get_prompt":
            return await _get_prompt(db, arguments)
        elif name == "create_prompt":
            return await _create_prompt(db, arguments)
        elif name == "update_prompt":
            return await _update_prompt(db, arguments)
        elif name == "delete_prompt":
            return await _delete_prompt(db, arguments)
        elif name == "list_categories":
            return await _list_categories(db, arguments)
        elif name == "list_tags":
            return await _list_tags(db, arguments)
        elif name == "import_prompts":
            return await _import_prompts(db, arguments)
        elif name == "export_prompts":
            return await _export_prompts(db, arguments)
        elif name == "get_popular_prompts":
            return await _get_popular_prompts(db, arguments)
        elif name == "get_recent_prompts":
            return await _get_recent_prompts(db, arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    finally:
        db.close()


# Tool Implementation Functions

async def _search_prompts(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Search for prompts."""
    service = PromptService(db)
    
    query = arguments.get("query", "")
    category = arguments.get("category")
    tags = arguments.get("tags")
    limit = arguments.get("limit", 10)
    
    # Get category ID if category name provided
    category_id = None
    if category:
        cat_service = CategoryService(db)
        cat_obj = cat_service.get_category_by_name(category)
        category_id = cat_obj.id if cat_obj else None
    
    prompts, total = service.get_prompts(
        limit=limit,
        search=query,
        category_id=category_id,
        tags=tags,
        status=PromptStatus.ACTIVE,
    )
    
    if not prompts:
        return [TextContent(type="text", text=f"No prompts found for query: '{query}'")]
    
    result = [f"Found {len(prompts)} prompts (total: {total}):\n"]
    for i, prompt in enumerate(prompts, 1):
        category_name = prompt.category.name if prompt.category else "None"
        tag_names = ", ".join(tag.name for tag in prompt.tags) if prompt.tags else "None"
        
        result.append(
            f"{i}. **{prompt.title}** (ID: {prompt.id})\n"
            f"   Type: {prompt.prompt_type.value} | Category: {category_name} | Tags: {tag_names}\n"
            f"   Usage: {prompt.usage_count} times | Created: {prompt.created_at.strftime('%Y-%m-%d')}\n"
            f"   Description: {prompt.description or 'No description'}\n"
        )
    
    return [TextContent(type="text", text="\n".join(result))]


async def _get_prompt(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Get a specific prompt by ID."""
    service = PromptService(db)
    prompt_id = arguments.get("prompt_id")
    
    if not prompt_id:
        return [TextContent(type="text", text="Error: prompt_id is required")]
    
    prompt = service.get_prompt(prompt_id)
    if not prompt:
        return [TextContent(type="text", text=f"Prompt with ID {prompt_id} not found")]
    
    # Record usage
    service.use_prompt(prompt_id)
    
    category_name = prompt.category.name if prompt.category else "None"
    tag_names = ", ".join(tag.name for tag in prompt.tags) if prompt.tags else "None"
    
    result = [
        f"**{prompt.title}** (ID: {prompt.id})\n",
        f"Type: {prompt.prompt_type.value}",
        f"Status: {prompt.status.value}",
        f"Category: {category_name}",
        f"Tags: {tag_names}",
        f"Version: {prompt.version}",
        f"Usage Count: {prompt.usage_count}",
        f"Public: {'Yes' if prompt.is_public else 'No'}",
        f"Template: {'Yes' if prompt.is_template else 'No'}",
        f"Created: {prompt.created_at.strftime('%Y-%m-%d %H:%M')}",
        f"Updated: {prompt.updated_at.strftime('%Y-%m-%d %H:%M')}",
        f"\n**Description:**\n{prompt.description or 'No description'}",
        f"\n**Content:**\n{prompt.content}"
    ]
    
    return [TextContent(type="text", text="\n".join(result))]


async def _create_prompt(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Create a new prompt."""
    service = PromptService(db)
    
    title = arguments.get("title")
    content = arguments.get("content") 
    description = arguments.get("description")
    category = arguments.get("category")
    tags = arguments.get("tags", [])
    is_public = arguments.get("is_public", False)
    is_template = arguments.get("is_template", False)
    
    if not title or not content:
        return [TextContent(type="text", text="Error: title and content are required")]
    
    # Get or create category
    category_id = None
    if category:
        cat_service = CategoryService(db)
        cat_obj = cat_service.get_category_by_name(category)
        if not cat_obj:
            cat_obj = cat_service.create_category(category)
        category_id = cat_obj.id
    
    try:
        prompt = service.create_prompt(
            title=title,
            content=content,
            description=description,
            category_id=category_id,
            tags=tags,
            is_public=is_public,
            is_template=is_template,
        )
        
        return [TextContent(
            type="text", 
            text=f"Successfully created prompt '{title}' with ID {prompt.id}"
        )]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error creating prompt: {str(e)}")]


async def _update_prompt(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Update an existing prompt."""
    service = PromptService(db)
    
    prompt_id = arguments.get("prompt_id")
    if not prompt_id:
        return [TextContent(type="text", text="Error: prompt_id is required")]
    
    # Get category ID if category name provided
    category_id = None
    category = arguments.get("category")
    if category:
        cat_service = CategoryService(db)
        cat_obj = cat_service.get_category_by_name(category)
        if not cat_obj:
            cat_obj = cat_service.create_category(category)
        category_id = cat_obj.id
    
    try:
        prompt = service.update_prompt(
            prompt_id=prompt_id,
            title=arguments.get("title"),
            content=arguments.get("content"),
            description=arguments.get("description"),
            category_id=category_id,
            tags=arguments.get("tags"),
            create_version=arguments.get("create_version", False),
        )
        
        if not prompt:
            return [TextContent(type="text", text=f"Prompt with ID {prompt_id} not found")]
        
        return [TextContent(
            type="text",
            text=f"Successfully updated prompt '{prompt.title}' (ID: {prompt.id})"
        )]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error updating prompt: {str(e)}")]


async def _delete_prompt(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Delete a prompt."""
    service = PromptService(db)
    
    prompt_id = arguments.get("prompt_id")
    if not prompt_id:
        return [TextContent(type="text", text="Error: prompt_id is required")]
    
    success = service.delete_prompt(prompt_id)
    if success:
        return [TextContent(type="text", text=f"Successfully deleted prompt with ID {prompt_id}")]
    else:
        return [TextContent(type="text", text=f"Prompt with ID {prompt_id} not found")]


async def _list_categories(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """List all categories."""
    service = CategoryService(db)
    active_only = arguments.get("active_only", True)
    
    categories = service.get_categories(active_only=active_only)
    
    if not categories:
        return [TextContent(type="text", text="No categories found")]
    
    result = [f"Found {len(categories)} categories:\n"]
    for i, category in enumerate(categories, 1):
        result.append(
            f"{i}. **{category.name}** (ID: {category.id})\n"
            f"   Description: {category.description or 'No description'}\n"
            f"   Color: {category.color or 'None'} | Active: {'Yes' if category.is_active else 'No'}\n"
        )
    
    return [TextContent(type="text", text="\n".join(result))]


async def _list_tags(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """List tags."""
    service = TagService(db)
    search = arguments.get("search")
    popular = arguments.get("popular", False)
    limit = arguments.get("limit", 20)
    
    if search:
        tags = service.search_tags(search, limit)
        result_text = f"Found {len(tags)} tags matching '{search}':\n"
    elif popular:
        tags_with_counts = service.get_popular_tags(limit)
        result = [f"Top {len(tags_with_counts)} popular tags:\n"]
        for i, tag_data in enumerate(tags_with_counts, 1):
            result.append(
                f"{i}. **{tag_data.name}** (used {tag_data.usage_count} times)\n"
                f"   Description: {tag_data.description or 'No description'}\n"
            )
        return [TextContent(type="text", text="\n".join(result))]
    else:
        tags = service.get_tags()
        result_text = f"Found {len(tags)} tags:\n"
    
    result = [result_text]
    for i, tag in enumerate(tags, 1):
        result.append(
            f"{i}. **{tag.name}** (ID: {tag.id})\n"
            f"   Description: {tag.description or 'No description'}\n"
        )
    
    return [TextContent(type="text", text="\n".join(result))]


async def _import_prompts(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Import prompts from content."""
    service = ImportExportService(db)
    
    content = arguments.get("content")
    format_type = arguments.get("format_type", "markdown")
    title = arguments.get("title")
    category = arguments.get("category")
    
    if not content:
        return [TextContent(type="text", text="Error: content is required")]
    
    try:
        imported_prompts, errors = service.import_prompts(
            data=content,
            format_type=format_type,
            default_category=category,
            skip_duplicates=True,
        )
        
        result = [
            f"Import completed:",
            f"- Imported: {len(imported_prompts)} prompts",
            f"- Errors: {len(errors)}",
        ]
        
        if errors:
            result.append("\nErrors:")
            for error in errors[:5]:  # Show first 5 errors
                result.append(f"  - {error}")
        
        if imported_prompts:
            result.append("\nImported prompts:")
            for prompt in imported_prompts[:10]:  # Show first 10
                result.append(f"  - {prompt.title} (ID: {prompt.id})")
        
        return [TextContent(type="text", text="\n".join(result))]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error importing prompts: {str(e)}")]


async def _export_prompts(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Export prompts."""
    service = ImportExportService(db)
    
    format_type = arguments.get("format_type", "json")
    prompt_ids = arguments.get("prompt_ids")
    include_metadata = arguments.get("include_metadata", True)
    
    try:
        exported_data = service.export_prompts(
            format_type=format_type,
            prompt_ids=prompt_ids,
            include_metadata=include_metadata,
        )
        
        return [TextContent(
            type="text",
            text=f"Exported prompts in {format_type} format:\n\n{exported_data}"
        )]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error exporting prompts: {str(e)}")]


async def _get_popular_prompts(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Get popular prompts."""
    service = PromptService(db)
    limit = arguments.get("limit", 10)
    
    prompts = service.get_popular_prompts(limit)
    
    if not prompts:
        return [TextContent(type="text", text="No popular prompts found")]
    
    result = [f"Top {len(prompts)} popular prompts:\n"]
    for i, prompt in enumerate(prompts, 1):
        result.append(
            f"{i}. **{prompt.title}** (ID: {prompt.id})\n"
            f"   Used {prompt.usage_count} times | Type: {prompt.prompt_type.value}\n"
            f"   Category: {prompt.category.name if prompt.category else 'None'}\n"
        )
    
    return [TextContent(type="text", text="\n".join(result))]


async def _get_recent_prompts(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Get recent prompts."""
    service = PromptService(db)
    limit = arguments.get("limit", 10)
    
    prompts = service.get_recent_prompts(limit)
    
    if not prompts:
        return [TextContent(type="text", text="No recent prompts found")]
    
    result = [f"Last {len(prompts)} created prompts:\n"]
    for i, prompt in enumerate(prompts, 1):
        result.append(
            f"{i}. **{prompt.title}** (ID: {prompt.id})\n"
            f"   Created: {prompt.created_at.strftime('%Y-%m-%d %H:%M')} | Type: {prompt.prompt_type.value}\n"
            f"   Category: {prompt.category.name if prompt.category else 'None'}\n"
        )
    
    return [TextContent(type="text", text="\n".join(result))]


# Resources (for future expansion)

@app.list_resources()
async def list_resources() -> List[Resource]:
    """List available resources."""
    return []


@app.get_resource()
async def get_resource(uri: AnyUrl) -> str:
    """Get a specific resource."""
    return "Resource not implemented yet"


# Main server function

async def main():
    """Run the MCP server."""
    # Initialize database
    init_db()
    
    logger.info("Starting Prombank MCP Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="prombank-mcp",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())