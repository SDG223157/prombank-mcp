"""Command-line interface for Prombank MCP."""

import json
import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm

from .database import SessionLocal, init_db
from .services import PromptService, CategoryService, TagService, ImportExportService
from .models.prompt import PromptType, PromptStatus
from .config import settings

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Prombank MCP - A comprehensive prompt management system."""
    # Initialize database if needed
    init_db()


@cli.group()
def prompt():
    """Manage prompts."""
    pass


@cli.group()
def category():
    """Manage categories."""
    pass


@cli.group()
def tag():
    """Manage tags."""
    pass


@cli.group()
def import_cmd():
    """Import prompts from various sources."""
    pass


@cli.group()
def export():
    """Export prompts to various formats."""
    pass


# Prompt Commands

@prompt.command("list")
@click.option("--search", "-s", help="Search query")
@click.option("--category", "-c", help="Filter by category name")
@click.option("--tags", "-t", help="Filter by tags (comma-separated)")
@click.option("--type", "prompt_type", type=click.Choice([t.value for t in PromptType]), help="Filter by type")
@click.option("--status", type=click.Choice([s.value for s in PromptStatus]), help="Filter by status")
@click.option("--public/--private", default=None, help="Filter by public status")
@click.option("--favorite/--not-favorite", default=None, help="Filter by favorite status")
@click.option("--limit", "-l", default=20, help="Limit number of results")
@click.option("--sort", default="created_at", help="Sort by field")
@click.option("--order", type=click.Choice(["asc", "desc"]), default="desc", help="Sort order")
def list_prompts(search, category, tags, prompt_type, status, public, favorite, limit, sort, order):
    """List prompts with optional filtering."""
    db = SessionLocal()
    try:
        service = PromptService(db)
        
        # Get category ID if provided
        category_id = None
        if category:
            cat_service = CategoryService(db)
            cat_obj = cat_service.get_category_by_name(category)
            category_id = cat_obj.id if cat_obj else None
        
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
        
        prompts, total = service.get_prompts(
            search=search,
            category_id=category_id,
            tags=tag_list,
            prompt_type=PromptType(prompt_type) if prompt_type else None,
            status=PromptStatus(status) if status else None,
            is_public=public,
            is_favorite=favorite,
            limit=limit,
            sort_by=sort,
            sort_order=order,
        )
        
        if not prompts:
            console.print("[yellow]No prompts found.[/yellow]")
            return
        
        table = Table(title=f"Prompts ({len(prompts)}/{total})")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="bold")
        table.add_column("Type", style="green")
        table.add_column("Category", style="blue")
        table.add_column("Tags", style="magenta")
        table.add_column("Usage", style="red")
        table.add_column("Public", style="yellow")
        table.add_column("Created", style="dim")
        
        for prompt in prompts:
            table.add_row(
                str(prompt.id),
                prompt.title[:50] + "..." if len(prompt.title) > 50 else prompt.title,
                prompt.prompt_type.value,
                prompt.category.name if prompt.category else "None",
                ", ".join(tag.name for tag in prompt.tags[:3]) + ("..." if len(prompt.tags) > 3 else ""),
                str(prompt.usage_count),
                "✓" if prompt.is_public else "✗",
                prompt.created_at.strftime("%Y-%m-%d"),
            )
        
        console.print(table)
    
    finally:
        db.close()


@prompt.command("show")
@click.argument("prompt_id", type=int)
@click.option("--use", is_flag=True, help="Record usage of this prompt")
def show_prompt(prompt_id, use):
    """Show detailed information about a prompt."""
    db = SessionLocal()
    try:
        service = PromptService(db)
        prompt = service.get_prompt(prompt_id)
        
        if not prompt:
            console.print(f"[red]Prompt with ID {prompt_id} not found.[/red]")
            return
        
        # Record usage if requested
        if use:
            service.use_prompt(prompt_id)
            prompt = service.get_prompt(prompt_id)  # Refresh to get updated usage
        
        # Display prompt details
        panel_content = []
        panel_content.append(f"[bold]ID:[/bold] {prompt.id}")
        panel_content.append(f"[bold]Type:[/bold] {prompt.prompt_type.value}")
        panel_content.append(f"[bold]Status:[/bold] {prompt.status.value}")
        panel_content.append(f"[bold]Version:[/bold] {prompt.version}")
        panel_content.append(f"[bold]Category:[/bold] {prompt.category.name if prompt.category else 'None'}")
        panel_content.append(f"[bold]Tags:[/bold] {', '.join(tag.name for tag in prompt.tags) if prompt.tags else 'None'}")
        panel_content.append(f"[bold]Usage Count:[/bold] {prompt.usage_count}")
        panel_content.append(f"[bold]Public:[/bold] {'Yes' if prompt.is_public else 'No'}")
        panel_content.append(f"[bold]Template:[/bold] {'Yes' if prompt.is_template else 'No'}")
        panel_content.append(f"[bold]Created:[/bold] {prompt.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        panel_content.append(f"[bold]Updated:[/bold] {prompt.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        console.print(Panel("\n".join(panel_content), title=prompt.title, border_style="blue"))
        
        if prompt.description:
            console.print(Panel(prompt.description, title="Description", border_style="green"))
        
        # Show content with syntax highlighting
        syntax = Syntax(prompt.content, "text", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Content", border_style="yellow"))
    
    finally:
        db.close()


@prompt.command("create")
@click.option("--title", "-t", prompt=True, help="Prompt title")
@click.option("--content", "-c", help="Prompt content (or use --file)")
@click.option("--file", "-f", type=click.Path(exists=True), help="Read content from file")
@click.option("--description", "-d", help="Prompt description")
@click.option("--category", help="Category name")
@click.option("--tags", help="Tags (comma-separated)")
@click.option("--type", "prompt_type", type=click.Choice([t.value for t in PromptType]), default="user", help="Prompt type")
@click.option("--public", is_flag=True, help="Make prompt public")
@click.option("--template", is_flag=True, help="Mark as template")
def create_prompt(title, content, file, description, category, tags, prompt_type, public, template):
    """Create a new prompt."""
    db = SessionLocal()
    try:
        # Get content from file or prompt
        if file:
            with open(file, 'r') as f:
                content = f.read()
        elif not content:
            content = click.edit("\n# Enter your prompt content here\n")
            if not content:
                console.print("[red]No content provided.[/red]")
                return
        
        # Get category ID if provided
        category_id = None
        if category:
            cat_service = CategoryService(db)
            cat_obj = cat_service.get_category_by_name(category)
            if not cat_obj:
                if Confirm.ask(f"Category '{category}' doesn't exist. Create it?"):
                    cat_obj = cat_service.create_category(category)
                    category_id = cat_obj.id
            else:
                category_id = cat_obj.id
        
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
        
        service = PromptService(db)
        prompt = service.create_prompt(
            title=title,
            content=content,
            description=description,
            prompt_type=PromptType(prompt_type),
            category_id=category_id,
            tags=tag_list,
            is_public=public,
            is_template=template,
        )
        
        console.print(f"[green]Successfully created prompt '{prompt.title}' with ID {prompt.id}[/green]")
    
    except Exception as e:
        console.print(f"[red]Error creating prompt: {str(e)}[/red]")
    
    finally:
        db.close()


@prompt.command("update")
@click.argument("prompt_id", type=int)
@click.option("--title", "-t", help="New title")
@click.option("--content", "-c", help="New content (or use --file)")
@click.option("--file", "-f", type=click.Path(exists=True), help="Read content from file")
@click.option("--description", "-d", help="New description")
@click.option("--category", help="New category name")
@click.option("--tags", help="New tags (comma-separated)")
@click.option("--status", type=click.Choice([s.value for s in PromptStatus]), help="New status")
@click.option("--public/--private", default=None, help="Change public status")
@click.option("--favorite/--not-favorite", default=None, help="Change favorite status")
@click.option("--version", is_flag=True, help="Create new version")
@click.option("--version-comment", help="Comment for new version")
def update_prompt(prompt_id, title, content, file, description, category, tags, status, public, favorite, version, version_comment):
    """Update an existing prompt."""
    db = SessionLocal()
    try:
        service = PromptService(db)
        
        # Check if prompt exists
        existing = service.get_prompt(prompt_id)
        if not existing:
            console.print(f"[red]Prompt with ID {prompt_id} not found.[/red]")
            return
        
        # Get content from file if provided
        if file:
            with open(file, 'r') as f:
                content = f.read()
        
        # Get category ID if provided
        category_id = None
        if category:
            cat_service = CategoryService(db)
            cat_obj = cat_service.get_category_by_name(category)
            if not cat_obj:
                if Confirm.ask(f"Category '{category}' doesn't exist. Create it?"):
                    cat_obj = cat_service.create_category(category)
                    category_id = cat_obj.id
            else:
                category_id = cat_obj.id
        
        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
        
        prompt = service.update_prompt(
            prompt_id=prompt_id,
            title=title,
            content=content,
            description=description,
            category_id=category_id,
            tags=tag_list,
            status=PromptStatus(status) if status else None,
            is_public=public,
            is_favorite=favorite,
            create_version=version,
            version_comment=version_comment,
        )
        
        console.print(f"[green]Successfully updated prompt '{prompt.title}'[/green]")
    
    except Exception as e:
        console.print(f"[red]Error updating prompt: {str(e)}[/red]")
    
    finally:
        db.close()


@prompt.command("delete")
@click.argument("prompt_id", type=int)
@click.option("--archive", is_flag=True, help="Archive instead of delete")
@click.confirmation_option(prompt="Are you sure you want to delete this prompt?")
def delete_prompt(prompt_id, archive):
    """Delete or archive a prompt."""
    db = SessionLocal()
    try:
        service = PromptService(db)
        
        if archive:
            prompt = service.archive_prompt(prompt_id)
            if prompt:
                console.print(f"[green]Successfully archived prompt '{prompt.title}'[/green]")
            else:
                console.print(f"[red]Prompt with ID {prompt_id} not found.[/red]")
        else:
            success = service.delete_prompt(prompt_id)
            if success:
                console.print(f"[green]Successfully deleted prompt with ID {prompt_id}[/green]")
            else:
                console.print(f"[red]Prompt with ID {prompt_id} not found.[/red]")
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
    
    finally:
        db.close()


# Category Commands

@category.command("list")
def list_categories():
    """List all categories."""
    db = SessionLocal()
    try:
        service = CategoryService(db)
        categories = service.get_categories(active_only=False)
        
        if not categories:
            console.print("[yellow]No categories found.[/yellow]")
            return
        
        table = Table(title="Categories")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Name", style="bold")
        table.add_column("Description", style="dim")
        table.add_column("Color", style="magenta")
        table.add_column("Active", style="green")
        
        for cat in categories:
            table.add_row(
                str(cat.id),
                cat.name,
                cat.description[:50] + "..." if cat.description and len(cat.description) > 50 else cat.description or "",
                cat.color or "",
                "✓" if cat.is_active else "✗",
            )
        
        console.print(table)
    
    finally:
        db.close()


@category.command("create")
@click.option("--name", "-n", prompt=True, help="Category name")
@click.option("--description", "-d", help="Category description")
@click.option("--color", "-c", help="Hex color code (e.g., #ff0000)")
def create_category(name, description, color):
    """Create a new category."""
    db = SessionLocal()
    try:
        service = CategoryService(db)
        category = service.create_category(name=name, description=description, color=color)
        console.print(f"[green]Successfully created category '{category.name}' with ID {category.id}[/green]")
    
    except Exception as e:
        console.print(f"[red]Error creating category: {str(e)}[/red]")
    
    finally:
        db.close()


# Import Commands

@import_cmd.command("file")
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--format", "format_type", type=click.Choice(["json", "csv", "yaml", "markdown", "fabric"]), 
              help="File format (auto-detected if not specified)")
@click.option("--category", help="Default category for imported prompts")
@click.option("--skip-duplicates/--allow-duplicates", default=True, help="Skip duplicate prompts")
@click.option("--update-existing", is_flag=True, help="Update existing prompts")
def import_file(filepath, format_type, category, skip_duplicates, update_existing):
    """Import prompts from a file."""
    db = SessionLocal()
    try:
        # Auto-detect format if not specified
        if not format_type:
            ext = Path(filepath).suffix.lower()
            format_map = {
                ".json": "json",
                ".csv": "csv", 
                ".yml": "yaml",
                ".yaml": "yaml",
                ".md": "markdown",
            }
            format_type = format_map.get(ext, "markdown")
        
        service = ImportExportService(db)
        imported_prompts, errors = service.import_prompts(
            data=Path(filepath),
            format_type=format_type,
            default_category=category,
            skip_duplicates=skip_duplicates,
            update_existing=update_existing,
        )
        
        console.print(f"[green]Import completed:[/green]")
        console.print(f"  - Imported: {len(imported_prompts)} prompts")
        console.print(f"  - Errors: {len(errors)}")
        
        if errors:
            console.print("\n[red]Errors:[/red]")
            for error in errors[:10]:  # Show first 10 errors
                console.print(f"  - {error}")
    
    except Exception as e:
        console.print(f"[red]Error importing file: {str(e)}[/red]")
    
    finally:
        db.close()


@import_cmd.command("fabric")
@click.argument("patterns_dir", type=click.Path(exists=True))
@click.option("--skip-duplicates/--allow-duplicates", default=True, help="Skip duplicate prompts")
def import_fabric(patterns_dir, skip_duplicates):
    """Import Fabric patterns from directory."""
    db = SessionLocal()
    try:
        service = ImportExportService(db)
        imported_prompts, errors = service.import_from_fabric_patterns(
            Path(patterns_dir),
            skip_duplicates=skip_duplicates
        )
        
        console.print(f"[green]Fabric import completed:[/green]")
        console.print(f"  - Imported: {len(imported_prompts)} patterns")
        console.print(f"  - Errors: {len(errors)}")
        
        if errors:
            console.print("\n[red]Errors:[/red]")
            for error in errors[:10]:
                console.print(f"  - {error}")
    
    except Exception as e:
        console.print(f"[red]Error importing Fabric patterns: {str(e)}[/red]")
    
    finally:
        db.close()


# Export Commands

@export.command("file")
@click.argument("output_file", type=click.Path())
@click.option("--format", "format_type", type=click.Choice(["json", "csv", "yaml", "markdown"]), default="json",
              help="Export format")
@click.option("--prompts", help="Comma-separated prompt IDs (exports all if not specified)")
@click.option("--include-versions", is_flag=True, help="Include version history")
@click.option("--include-metadata/--no-metadata", default=True, help="Include metadata")
def export_file(output_file, format_type, prompts, include_versions, include_metadata):
    """Export prompts to a file."""
    db = SessionLocal()
    try:
        service = ImportExportService(db)
        
        # Parse prompt IDs if provided
        prompt_ids = None
        if prompts:
            prompt_ids = [int(pid.strip()) for pid in prompts.split(",")]
        
        exported_data = service.export_prompts(
            format_type=format_type,
            prompt_ids=prompt_ids,
            include_versions=include_versions,
            include_metadata=include_metadata,
        )
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(exported_data)
        
        console.print(f"[green]Successfully exported prompts to {output_file}[/green]")
    
    except Exception as e:
        console.print(f"[red]Error exporting prompts: {str(e)}[/red]")
    
    finally:
        db.close()


# Server Commands

@cli.command("server")
@click.option("--host", default="localhost", help="Server host")
@click.option("--port", default=8000, help="Server port")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def run_server(host, port, reload):
    """Run the FastAPI server."""
    import uvicorn
    uvicorn.run(
        "prombank.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@cli.command("mcp-server")
def run_mcp_server():
    """Run the MCP server for tool integration."""
    import asyncio
    from .mcp_server import main
    
    console.print("[green]Starting Prombank MCP Server...[/green]")
    console.print("[dim]Connect this server to your MCP-compatible tools.[/dim]")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]MCP Server stopped.[/yellow]")


@cli.command("init")
def initialize():
    """Initialize the database and create default data."""
    try:
        init_db()
        console.print("[green]Database initialized successfully![/green]")
        console.print(f"[dim]Database location: {settings.database_url}[/dim]")
    except Exception as e:
        console.print(f"[red]Error initializing database: {str(e)}[/red]")


def main():
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()