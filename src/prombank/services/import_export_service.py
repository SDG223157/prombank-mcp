"""Import and export service for prompts."""

import json
import csv
import yaml
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from sqlalchemy.orm import Session

from ..models.prompt import Prompt, PromptType, PromptStatus
from .prompt_service import PromptService
from .category_service import CategoryService
from .tag_service import TagService


class ImportExportService:
    """Service for importing and exporting prompts."""
    
    def __init__(self, db: Session):
        self.db = db
        self.prompt_service = PromptService(db)
        self.category_service = CategoryService(db)
        self.tag_service = TagService(db)
    
    def export_prompts(
        self,
        format_type: str = "json",
        prompt_ids: Optional[List[int]] = None,
        include_versions: bool = False,
        include_metadata: bool = True,
    ) -> Union[str, bytes]:
        """Export prompts to various formats."""
        
        # Get prompts to export
        if prompt_ids:
            prompts = []
            for prompt_id in prompt_ids:
                prompt = self.prompt_service.get_prompt(prompt_id, include_versions=include_versions)
                if prompt:
                    prompts.append(prompt)
        else:
            prompts, _ = self.prompt_service.get_prompts(limit=10000)  # Get all
        
        if format_type.lower() == "json":
            return self._export_to_json(prompts, include_versions, include_metadata)
        elif format_type.lower() == "csv":
            return self._export_to_csv(prompts, include_metadata)
        elif format_type.lower() == "yaml":
            return self._export_to_yaml(prompts, include_versions, include_metadata)
        elif format_type.lower() == "markdown":
            return self._export_to_markdown(prompts, include_metadata)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def import_prompts(
        self,
        data: Union[str, bytes, Path],
        format_type: str = "json",
        source_type: Optional[str] = None,
        default_category: Optional[str] = None,
        skip_duplicates: bool = True,
        update_existing: bool = False,
    ) -> Tuple[List[Prompt], List[str]]:
        """Import prompts from various formats."""
        
        errors = []
        imported_prompts = []
        
        try:
            if isinstance(data, Path):
                with open(data, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = data if isinstance(data, str) else data.decode('utf-8')
            
            if format_type.lower() == "json":
                prompt_data = self._parse_json(content)
            elif format_type.lower() == "csv":
                prompt_data = self._parse_csv(content)
            elif format_type.lower() == "yaml":
                prompt_data = self._parse_yaml(content)
            elif format_type.lower() == "markdown":
                prompt_data = self._parse_markdown(content)
            elif format_type.lower() == "fabric":
                prompt_data = self._parse_fabric_pattern(content)
            else:
                raise ValueError(f"Unsupported import format: {format_type}")
            
            # Get or create default category
            category_id = None
            if default_category:
                category = self.category_service.get_category_by_name(default_category)
                if not category:
                    category = self.category_service.create_category(default_category)
                category_id = category.id
            
            # Process each prompt
            for i, prompt_item in enumerate(prompt_data):
                try:
                    imported_prompt = self._import_single_prompt(
                        prompt_item,
                        source_type=source_type,
                        default_category_id=category_id,
                        skip_duplicates=skip_duplicates,
                        update_existing=update_existing,
                    )
                    
                    if imported_prompt:
                        imported_prompts.append(imported_prompt)
                
                except Exception as e:
                    errors.append(f"Error importing prompt {i + 1}: {str(e)}")
        
        except Exception as e:
            errors.append(f"Error parsing file: {str(e)}")
        
        return imported_prompts, errors
    
    def import_from_fabric_patterns(
        self,
        patterns_dir: Path,
        skip_duplicates: bool = True,
    ) -> Tuple[List[Prompt], List[str]]:
        """Import prompts from Fabric patterns directory."""
        
        imported_prompts = []
        errors = []
        
        if not patterns_dir.exists() or not patterns_dir.is_dir():
            errors.append(f"Patterns directory not found: {patterns_dir}")
            return imported_prompts, errors
        
        # Get or create Fabric category
        fabric_category = self.category_service.get_category_by_name("Fabric")
        if not fabric_category:
            fabric_category = self.category_service.create_category(
                "Fabric",
                "Imported from Fabric patterns",
                "#0ea5e9"
            )
        
        # Process each pattern directory
        for pattern_dir in patterns_dir.iterdir():
            if pattern_dir.is_dir():
                try:
                    prompt = self._import_fabric_pattern(
                        pattern_dir,
                        fabric_category.id,
                        skip_duplicates
                    )
                    
                    if prompt:
                        imported_prompts.append(prompt)
                
                except Exception as e:
                    errors.append(f"Error importing pattern {pattern_dir.name}: {str(e)}")
        
        return imported_prompts, errors
    
    def _export_to_json(
        self, 
        prompts: List[Prompt], 
        include_versions: bool, 
        include_metadata: bool
    ) -> str:
        """Export prompts to JSON format."""
        
        export_data = {
            "format": "prombank_export",
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "total_prompts": len(prompts),
            "prompts": []
        }
        
        for prompt in prompts:
            prompt_data = {
                "id": prompt.id,
                "title": prompt.title,
                "content": prompt.content,
                "description": prompt.description,
                "prompt_type": prompt.prompt_type.value,
                "status": prompt.status.value,
                "version": prompt.version,
                "is_public": prompt.is_public,
                "is_favorite": prompt.is_favorite,
                "is_template": prompt.is_template,
                "template_variables": json.loads(prompt.template_variables) if prompt.template_variables else None,
                "usage_count": prompt.usage_count,
                "created_at": prompt.created_at.isoformat(),
                "updated_at": prompt.updated_at.isoformat(),
            }
            
            if include_metadata:
                prompt_data.update({
                    "category": prompt.category.name if prompt.category else None,
                    "tags": [tag.name for tag in prompt.tags],
                    "source_url": prompt.source_url,
                    "source_type": prompt.source_type,
                })
            
            if include_versions:
                prompt_data["versions"] = [
                    {
                        "version": v.version,
                        "content": v.content,
                        "title": v.title,
                        "change_log": v.change_log,
                        "created_at": v.created_at.isoformat(),
                    }
                    for v in prompt.versions
                ]
            
            export_data["prompts"].append(prompt_data)
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def _export_to_csv(self, prompts: List[Prompt], include_metadata: bool) -> str:
        """Export prompts to CSV format."""
        
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        headers = ["id", "title", "content", "description", "type", "status", "version"]
        if include_metadata:
            headers.extend(["category", "tags", "is_public", "is_favorite", "usage_count"])
        
        writer.writerow(headers)
        
        # Data
        for prompt in prompts:
            row = [
                prompt.id,
                prompt.title,
                prompt.content,
                prompt.description or "",
                prompt.prompt_type.value,
                prompt.status.value,
                prompt.version,
            ]
            
            if include_metadata:
                row.extend([
                    prompt.category.name if prompt.category else "",
                    ", ".join(tag.name for tag in prompt.tags),
                    prompt.is_public,
                    prompt.is_favorite,
                    prompt.usage_count,
                ])
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def _export_to_yaml(
        self, 
        prompts: List[Prompt], 
        include_versions: bool, 
        include_metadata: bool
    ) -> str:
        """Export prompts to YAML format."""
        
        export_data = {
            "format": "prombank_export",
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "prompts": []
        }
        
        for prompt in prompts:
            prompt_data = {
                "title": prompt.title,
                "content": prompt.content,
                "description": prompt.description,
                "type": prompt.prompt_type.value,
                "status": prompt.status.value,
            }
            
            if include_metadata:
                prompt_data.update({
                    "category": prompt.category.name if prompt.category else None,
                    "tags": [tag.name for tag in prompt.tags],
                    "is_public": prompt.is_public,
                    "is_template": prompt.is_template,
                })
            
            export_data["prompts"].append(prompt_data)
        
        return yaml.dump(export_data, default_flow_style=False, allow_unicode=True)
    
    def _export_to_markdown(self, prompts: List[Prompt], include_metadata: bool) -> str:
        """Export prompts to Markdown format."""
        
        lines = [
            "# Prombank Export",
            f"",
            f"Exported on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            f"Total prompts: {len(prompts)}",
            f"",
        ]
        
        for i, prompt in enumerate(prompts, 1):
            lines.extend([
                f"## {i}. {prompt.title}",
                f"",
            ])
            
            if include_metadata:
                lines.extend([
                    f"**Type:** {prompt.prompt_type.value}",
                    f"**Status:** {prompt.status.value}",
                    f"**Category:** {prompt.category.name if prompt.category else 'None'}",
                    f"**Tags:** {', '.join(tag.name for tag in prompt.tags) if prompt.tags else 'None'}",
                    f"",
                ])
            
            if prompt.description:
                lines.extend([
                    f"**Description:** {prompt.description}",
                    f"",
                ])
            
            lines.extend([
                f"**Content:**",
                f"```",
                prompt.content,
                f"```",
                f"",
            ])
        
        return "\n".join(lines)
    
    def _parse_json(self, content: str) -> List[Dict[str, Any]]:
        """Parse JSON content."""
        data = json.loads(content)
        
        if isinstance(data, dict) and "prompts" in data:
            return data["prompts"]
        elif isinstance(data, list):
            return data
        else:
            return [data]
    
    def _parse_csv(self, content: str) -> List[Dict[str, Any]]:
        """Parse CSV content."""
        import io
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)
    
    def _parse_yaml(self, content: str) -> List[Dict[str, Any]]:
        """Parse YAML content."""
        data = yaml.safe_load(content)
        
        if isinstance(data, dict) and "prompts" in data:
            return data["prompts"]
        elif isinstance(data, list):
            return data
        else:
            return [data]
    
    def _parse_markdown(self, content: str) -> List[Dict[str, Any]]:
        """Parse Markdown content into prompts."""
        prompts = []
        
        # Split by headers (# or ##)
        sections = re.split(r'\n(?=#+\s)', content)
        
        for section in sections:
            if not section.strip():
                continue
            
            lines = section.strip().split('\n')
            if not lines:
                continue
            
            # Extract title from header
            title_line = lines[0]
            title_match = re.match(r'^#+\s*(.+)', title_line)
            if not title_match:
                continue
            
            title = title_match.group(1).strip()
            
            # Extract content (everything after the title)
            content_lines = lines[1:]
            content = '\n'.join(content_lines).strip()
            
            if content:
                prompts.append({
                    "title": title,
                    "content": content,
                    "type": "user",
                })
        
        return prompts
    
    def _parse_fabric_pattern(self, content: str) -> List[Dict[str, Any]]:
        """Parse Fabric pattern format."""
        # Fabric patterns typically have a specific structure
        lines = content.strip().split('\n')
        
        title = "Fabric Pattern"
        description = ""
        content_lines = []
        
        # Extract title and content
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
            elif line.startswith('## '):
                description = line[3:].strip()
            else:
                content_lines.append(line)
        
        content = '\n'.join(content_lines).strip()
        
        return [{
            "title": title,
            "description": description if description else None,
            "content": content,
            "type": "system",
            "tags": ["fabric", "pattern"],
        }]
    
    def _import_single_prompt(
        self,
        prompt_data: Dict[str, Any],
        source_type: Optional[str] = None,
        default_category_id: Optional[int] = None,
        skip_duplicates: bool = True,
        update_existing: bool = False,
    ) -> Optional[Prompt]:
        """Import a single prompt from data dictionary."""
        
        # Required fields
        title = prompt_data.get("title", "").strip()
        content = prompt_data.get("content", "").strip()
        
        if not title or not content:
            raise ValueError("Title and content are required")
        
        # Check for duplicates
        import hashlib
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        existing_prompts = self.prompt_service.get_duplicate_prompts(content_hash)
        
        if existing_prompts and skip_duplicates and not update_existing:
            return None  # Skip duplicate
        
        if existing_prompts and update_existing:
            # Update existing prompt
            existing_prompt = existing_prompts[0]
            return self.prompt_service.update_prompt(
                existing_prompt.id,
                title=title,
                content=content,
                description=prompt_data.get("description"),
                create_version=True,
                version_comment="Updated from import",
            )
        
        # Get or create category
        category_id = default_category_id
        if "category" in prompt_data and prompt_data["category"]:
            category = self.category_service.get_category_by_name(prompt_data["category"])
            if not category:
                category = self.category_service.create_category(prompt_data["category"])
            category_id = category.id
        
        # Parse prompt type
        prompt_type = PromptType.USER
        if "type" in prompt_data:
            try:
                prompt_type = PromptType(prompt_data["type"])
            except ValueError:
                pass
        
        # Parse tags
        tags = []
        if "tags" in prompt_data:
            if isinstance(prompt_data["tags"], list):
                tags = prompt_data["tags"]
            elif isinstance(prompt_data["tags"], str):
                tags = [tag.strip() for tag in prompt_data["tags"].split(",") if tag.strip()]
        
        # Create prompt
        return self.prompt_service.create_prompt(
            title=title,
            content=content,
            description=prompt_data.get("description"),
            prompt_type=prompt_type,
            category_id=category_id,
            tags=tags,
            is_public=prompt_data.get("is_public", False),
            is_template=prompt_data.get("is_template", False),
            template_variables=prompt_data.get("template_variables"),
            source_type=source_type,
        )
    
    def _import_fabric_pattern(
        self,
        pattern_dir: Path,
        category_id: int,
        skip_duplicates: bool,
    ) -> Optional[Prompt]:
        """Import a single Fabric pattern from directory."""
        
        # Look for system.md file
        system_file = pattern_dir / "system.md"
        if not system_file.exists():
            # Try alternative names
            for alt_name in ["prompt.md", "pattern.md", f"{pattern_dir.name}.md"]:
                alt_file = pattern_dir / alt_name
                if alt_file.exists():
                    system_file = alt_file
                    break
            else:
                raise ValueError(f"No system prompt file found in {pattern_dir}")
        
        # Read content
        with open(system_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content:
            raise ValueError("Empty system prompt file")
        
        # Use directory name as title
        title = pattern_dir.name.replace('_', ' ').replace('-', ' ').title()
        
        # Check for duplicates
        import hashlib
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        existing_prompts = self.prompt_service.get_duplicate_prompts(content_hash)
        
        if existing_prompts and skip_duplicates:
            return None
        
        # Create prompt
        return self.prompt_service.create_prompt(
            title=title,
            content=content,
            description=f"Fabric pattern: {pattern_dir.name}",
            prompt_type=PromptType.SYSTEM,
            category_id=category_id,
            tags=["fabric", "pattern", pattern_dir.name],
            source_type="fabric",
            source_url=str(pattern_dir),
        )