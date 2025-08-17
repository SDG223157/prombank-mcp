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
                        "type": "string",
                        "description": "Filter by tags (comma-separated, optional)"
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
            description="Create a new prompt with title, content, and metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the prompt"
                    },
                    "content": {
                        "type": "string", 
                        "description": "The prompt content with variables in {{variable}} format"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the prompt (optional)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category of the prompt (optional)"
                    },
                    "tags": {
                        "type": "string",
                        "description": "Comma-separated tags (optional)"
                    },
                    "is_public": {
                        "type": "boolean",
                        "description": "Whether the prompt should be public",
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
                        "description": "The ID of the prompt to update"
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
                        "description": "New category (optional)"
                    },
                    "tags": {
                        "type": "string",
                        "description": "New comma-separated tags (optional)"
                    },
                    "is_public": {
                        "type": "boolean",
                        "description": "Whether the prompt should be public (optional)"
                    }
                },
                "required": ["prompt_id"]
            }
        ),
        Tool(
            name="list_templates",
            description="Get available prompt templates",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by category (optional)"
                    }
                }
            }
        ),
        Tool(
            name="get_user_info",
            description="Get user information and statistics",
            inputSchema={
                "type": "object",
                "properties": {}
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
                        "description": "The ID of the prompt to delete"
                    }
                },
                "required": ["prompt_id"]
            }
        ),
        Tool(
            name="bulk_import",
            description="Bulk import prompts from Fabric patterns or markdown files",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_type": {
                        "type": "string",
                        "enum": ["fabric", "markdown"],
                        "description": "Type of source files to import"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to import (for single file import)"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Optional pattern to filter files (e.g., 'analyze_*')"
                    },
                    "category": {
                        "type": "string",
                        "description": "Default category for imported prompts (optional)"
                    }
                },
                "required": ["source_type"]
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
        elif name == "list_templates":
            return await _list_templates(db, arguments)
        elif name == "get_user_info":
            return await _get_user_info(db, arguments)
        elif name == "bulk_import":
            return await _bulk_import(db, arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    finally:
        db.close()


# Tool Implementation Functions

async def _search_prompts(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Search for prompts by title, content, or tags."""
    query = arguments.get("query", "")
    category = arguments.get("category")
    tags = arguments.get("tags")
    limit = arguments.get("limit", 10)
    
    try:
        prompt_service = PromptService(db)
        
        # Convert tag string to list if provided
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
        
        # Search prompts
        prompts = prompt_service.search_prompts(
            query=query,
            category_name=category,
            tag_names=tag_list,
            limit=limit
        )
        
        results = []
        for prompt in prompts:
            results.append({
                "id": prompt.id,
                "title": prompt.title,
                "description": prompt.description,
                "category": prompt.category.name if prompt.category else None,
                "tags": [tag.name for tag in prompt.tags] if prompt.tags else [],
                "is_public": prompt.is_public,
                "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None,
                "preview": prompt.content[:200] + "..." if len(prompt.content) > 200 else prompt.content
            })
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "results": results,
                "count": len(results),
                "query": query
            }, indent=2)
        )]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Search error: {str(e)}")]


async def _get_prompt(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Get a specific prompt by ID."""
    prompt_id = arguments.get("prompt_id")
    
    if not prompt_id:
        return [TextContent(type="text", text="Error: prompt_id is required")]
    
    try:
        prompt_service = PromptService(db)
        prompt = prompt_service.get_prompt(prompt_id)
        
        if not prompt:
            return [TextContent(type="text", text=f"Prompt with ID {prompt_id} not found")]
        
        # Extract variables from content
        variables = _extract_variables(prompt.content)
        
        result = {
            "id": prompt.id,
            "title": prompt.title,
            "description": prompt.description,
            "content": prompt.content,
            "category": prompt.category.name if prompt.category else None,
            "tags": [tag.name for tag in prompt.tags] if prompt.tags else [],
            "is_public": prompt.is_public,
            "variables": variables,
            "statistics": {
                "characters": len(prompt.content),
                "words": len(prompt.content.split()) if prompt.content else 0,
                "estimated_tokens": len(prompt.content) // 4 if prompt.content else 0
            },
            "created_at": prompt.created_at.isoformat() if prompt.created_at else None,
            "updated_at": prompt.updated_at.isoformat() if prompt.updated_at else None
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Get prompt error: {str(e)}")]


async def _create_prompt(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Create a new prompt."""
    title = arguments.get("title")
    content = arguments.get("content")
    description = arguments.get("description")
    category = arguments.get("category")
    tags = arguments.get("tags")
    is_public = arguments.get("is_public", False)
    
    if not title or not content:
        return [TextContent(type="text", text="Error: title and content are required")]
    
    try:
        prompt_service = PromptService(db)
        
        # Convert tag string to list if provided
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
        
        # For MCP, we'll use a default user ID (1) - in a real scenario, this would come from authentication
        prompt = prompt_service.create_prompt(
            title=title,
            content=content,
            description=description,
            category_name=category,
            tag_names=tag_list,
            is_public=is_public,
            user_id=1  # Default user for MCP
        )
        
        variables = _extract_variables(content)
        
        result = {
            "success": True,
            "message": "Prompt created successfully",
            "prompt": {
                "id": prompt.id,
                "title": prompt.title,
                "description": prompt.description,
                "category": prompt.category.name if prompt.category else None,
                "tags": [tag.name for tag in prompt.tags] if prompt.tags else [],
                "is_public": prompt.is_public,
                "variables": variables,
                "statistics": {
                    "characters": len(content),
                    "words": len(content.split()),
                    "estimated_tokens": len(content) // 4
                }
            }
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Create prompt error: {str(e)}")]


async def _update_prompt(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Update an existing prompt."""
    prompt_id = arguments.get("prompt_id")
    
    if not prompt_id:
        return [TextContent(type="text", text="Error: prompt_id is required")]
    
    try:
        prompt_service = PromptService(db)
        
        # Get existing prompt
        existing_prompt = prompt_service.get_prompt(prompt_id)
        if not existing_prompt:
            return [TextContent(type="text", text=f"Prompt with ID {prompt_id} not found")]
        
        # Prepare update data
        update_data = {}
        if "title" in arguments:
            update_data["title"] = arguments["title"]
        if "content" in arguments:
            update_data["content"] = arguments["content"]
        if "description" in arguments:
            update_data["description"] = arguments["description"]
        if "category" in arguments:
            update_data["category_name"] = arguments["category"]
        if "tags" in arguments:
            tags = arguments["tags"]
            update_data["tag_names"] = [tag.strip() for tag in tags.split(",")] if tags else []
        if "is_public" in arguments:
            update_data["is_public"] = arguments["is_public"]
        
        # Update prompt
        prompt = prompt_service.update_prompt(prompt_id, **update_data)
        
        result = {
            "success": True,
            "message": "Prompt updated successfully",
            "prompt": {
                "id": prompt.id,
                "title": prompt.title,
                "description": prompt.description,
                "category": prompt.category.name if prompt.category else None,
                "tags": [tag.name for tag in prompt.tags] if prompt.tags else [],
                "is_public": prompt.is_public
            }
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Update prompt error: {str(e)}")]


async def _delete_prompt(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Delete a prompt by ID."""
    prompt_id = arguments.get("prompt_id")
    
    if not prompt_id:
        return [TextContent(type="text", text="Error: prompt_id is required")]
    
    try:
        prompt_service = PromptService(db)
        
        # Check if prompt exists
        existing_prompt = prompt_service.get_prompt(prompt_id)
        if not existing_prompt:
            return [TextContent(type="text", text=f"Prompt with ID {prompt_id} not found")]
        
        # Delete prompt
        prompt_service.delete_prompt(prompt_id)
        
        result = {
            "success": True,
            "message": "Prompt deleted successfully",
            "prompt_id": prompt_id
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Delete prompt error: {str(e)}")]


async def _list_templates(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """List available prompt templates."""
    category = arguments.get("category")
    
    try:
        # Predefined templates based on the reference implementation
        templates = [
            {
                "id": "writing-assistant",
                "name": "Writing Assistant",
                "description": "Professional writing assistant for content creation",
                "category": "writing",
                "variables": ["role", "field", "task", "context", "requirement1", "requirement2"]
            },
            {
                "id": "code-reviewer",
                "name": "Code Reviewer", 
                "description": "Expert code review and feedback system",
                "category": "development",
                "variables": ["language", "code_type", "code", "focus1", "focus2", "focus3"]
            },
            {
                "id": "data-analyst",
                "name": "Data Analysis",
                "description": "Comprehensive data analysis and insights",
                "category": "analysis",
                "variables": ["data_type", "data", "goal1", "goal2", "goal3", "additional_request"]
            },
            {
                "id": "customer-support",
                "name": "Customer Support",
                "description": "Professional customer service and support",
                "category": "support",
                "variables": ["company", "customer_issue", "customer_name", "account_type", "previous_contact", "response_goal1", "response_goal2", "response_goal3"]
            },
            {
                "id": "marketing-copy",
                "name": "Marketing Copy",
                "description": "Persuasive marketing and sales content",
                "category": "marketing",
                "variables": ["content_type", "product_name", "target_audience", "benefit1", "benefit2", "benefit3", "usp", "cta", "tone", "length", "additional_requirements"]
            },
            {
                "id": "educational-tutor",
                "name": "Educational Tutor",
                "description": "Personalized tutoring and explanation system",
                "category": "education",
                "variables": ["subject", "topic", "level", "learning_style", "question", "instruction1", "instruction2", "instruction3", "teaching_method", "examples_type"]
            }
        ]
        
        # Filter by category if provided
        if category:
            templates = [t for t in templates if t["category"] == category]
        
        result = {
            "templates": templates,
            "count": len(templates)
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"List templates error: {str(e)}")]


async def _get_user_info(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Get user information and statistics."""
    try:
        prompt_service = PromptService(db)
        
        # For MCP, we'll use default user ID (1) - in a real scenario, this would come from authentication
        user_id = 1
        
        # Get prompt counts
        prompts = prompt_service.get_prompts_by_user(user_id)
        total_prompts = len(prompts)
        public_prompts = len([p for p in prompts if p.is_public])
        private_prompts = total_prompts - public_prompts
        
        stats = {
            "user": {
                "id": user_id,
                "name": "MCP User",
                "email": "mcp@prombank.com"
            },
            "prompts": {
                "total": total_prompts,
                "public": public_prompts,
                "private": private_prompts
            },
            "categories": len(set(p.category.name for p in prompts if p.category)),
            "tags": len(set(tag.name for p in prompts for tag in p.tags))
        }
        
        return [TextContent(type="text", text=json.dumps(stats, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Get user info error: {str(e)}")]


async def _bulk_import(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Bulk import prompts from content."""
    source_type = arguments.get("source_type")
    content = arguments.get("content")
    pattern = arguments.get("pattern")
    category = arguments.get("category")
    
    if not source_type:
        return [TextContent(type="text", text="Error: source_type is required")]
    
    if not content:
        return [TextContent(type="text", text="Error: content is required for import")]
    
    try:
        import_export_service = ImportExportService(db)
        
        # Import prompts based on source type
        if source_type == "markdown":
            result = import_export_service.import_markdown(content, category)
        elif source_type == "fabric":
            result = import_export_service.import_fabric_pattern(content, category)
        else:
            return [TextContent(type="text", text=f"Unsupported source type: {source_type}")]
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Bulk import error: {str(e)}")]


def _extract_variables(content: str) -> List[str]:
    """Extract variables from prompt content (variables in {{variable}} format)."""
    import re
    
    # Find all {{variable}} patterns
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, content)
    
    # Return unique variables, trimmed
    return list(set(match.strip() for match in matches))


# Server startup
def main():
    """Main entry point for the MCP server."""
    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="prombank-mcp",
                    server_version="1.0.0",
                    capabilities=app.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )

    # Initialize database
    init_db()
    
    # Run the server
    asyncio.run(run_server())


if __name__ == "__main__":
    main()