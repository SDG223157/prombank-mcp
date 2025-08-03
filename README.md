# Prombank MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io/)

A comprehensive prompt management system with MCP (Model Context Protocol) server capabilities for seamless integration with AI tools like Cursor.

## Features

### Core Functionality
- **CRUD Operations**: Create, read, update, delete prompts with full version history
- **Advanced Search**: Search prompts by title, content, tags, or category
- **Categories & Tags**: Organize prompts with hierarchical categories and flexible tagging
- **Template System**: Create reusable prompt templates with variable substitution
- **Usage Tracking**: Monitor prompt usage statistics and popularity

### Import/Export
- **Multiple Formats**: JSON, CSV, YAML, Markdown support
- **Fabric Integration**: Import prompts from Fabric patterns
- **Bulk Operations**: Import/export multiple prompts at once
- **Duplicate Detection**: Smart duplicate handling during imports

### MCP Server Integration
- **Tool Integration**: Seamless integration with MCP-compatible tools like Cursor
- **Real-time Access**: Direct prompt access from your development environment
- **Search & Retrieval**: Find and use prompts without leaving your editor
- **Version Management**: Access different versions of prompts

### REST API
- **Full REST API**: Complete HTTP API for all operations
- **OpenAPI Documentation**: Auto-generated API docs at `/docs`
- **Pagination**: Efficient handling of large prompt collections
- **Filtering**: Advanced filtering and sorting capabilities

### CLI Interface
- **Command Line Tools**: Full CLI for prompt management
- **Interactive Features**: Rich terminal interface with syntax highlighting
- **Batch Operations**: Bulk import/export from command line
- **Server Management**: Start/stop API and MCP servers

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/SDG223157/prombank-mcp
cd prombank-mcp

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Initialize the database
prombank init
```

### Using pip (when published)

```bash
pip install prombank-mcp
prombank init
```

## Quick Start

### 1. Initialize the Database

```bash
prombank init
```

### 2. Create Your First Prompt

```bash
prombank prompt create --title "Code Review Prompt" --content "Please review this code for best practices and potential issues."
```

### 3. Start the MCP Server

```bash
prombank mcp-server
```

### 4. Start the REST API Server

```bash
prombank server --host 0.0.0.0 --port 8000
```

## Usage

### CLI Commands

#### Prompt Management

```bash
# List prompts
prombank prompt list

# Search prompts
prombank prompt list --search "code review" --category "development"

# Show prompt details
prombank prompt show 1

# Create prompt from file
prombank prompt create --title "My Prompt" --file prompt.txt

# Update prompt
prombank prompt update 1 --title "New Title" --version

# Delete prompt
prombank prompt delete 1
```

#### Category Management

```bash
# List categories
prombank category list

# Create category
prombank category create --name "Development" --description "Coding prompts" --color "#10b981"
```

#### Import/Export

```bash
# Import from JSON file
prombank import file prompts.json

# Import Fabric patterns
prombank import fabric ~/fabric/patterns

# Export to markdown
prombank export file prompts.md --format markdown
```

### MCP Server Integration

The MCP server provides these tools for integration with MCP-compatible editors:

- `search_prompts` - Search for prompts by content or metadata
- `get_prompt` - Retrieve a specific prompt by ID
- `create_prompt` - Create a new prompt
- `update_prompt` - Update an existing prompt
- `delete_prompt` - Delete a prompt
- `list_categories` - List all categories
- `list_tags` - List all tags
- `import_prompts` - Import prompts from text content
- `export_prompts` - Export prompts in various formats
- `get_popular_prompts` - Get most used prompts
- `get_recent_prompts` - Get recently created prompts

### REST API

The REST API is available at `http://localhost:8000` with documentation at `/docs`.

#### Example API calls:

```bash
# Get all prompts
curl "http://localhost:8000/api/v1/prompts"

# Search prompts
curl "http://localhost:8000/api/v1/prompts?search=code&limit=10"

# Get specific prompt
curl "http://localhost:8000/api/v1/prompts/1"

# Create prompt
curl -X POST "http://localhost:8000/api/v1/prompts" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Prompt", "content": "Test content"}'
```

## Configuration

Configuration can be set via environment variables or `.env` file:

```bash
# Database
PROMBANK_DATABASE_URL=sqlite:///./prombank.db

# Server
PROMBANK_HOST=localhost
PROMBANK_PORT=8000
PROMBANK_DEBUG=false

# MCP Server
PROMBANK_MCP_HOST=localhost
PROMBANK_MCP_PORT=8001

# Storage
PROMBANK_DATA_DIR=~/.prombank
```

## Database Schema

The system uses SQLAlchemy with the following main models:

- **Prompt**: Main prompt entity with content, metadata, and relationships
- **PromptCategory**: Hierarchical categorization system
- **PromptTag**: Flexible tagging system with many-to-many relationships
- **PromptVersion**: Version history tracking for prompts

## Development

### Setting up Development Environment

```bash
# Clone repository
git clone https://github.com/SDG223157/prombank-mcp
cd prombank-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Initialize database
prombank init

# Run tests
pytest tests/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

### Running Services

```bash
# Run FastAPI server with auto-reload
prombank server --reload

# Run MCP server
prombank mcp-server

# Run CLI
prombank --help
```

## Integration Examples

### Cursor IDE Integration

1. Start the MCP server:
```bash
prombank mcp-server
```

2. Add to your Cursor MCP configuration:
```json
{
  "prombank-mcp": {
    "command": "prombank",
    "args": ["mcp-server"]
  }
}
```

### Custom Tool Integration

The MCP server follows the Model Context Protocol standard, making it compatible with any MCP-compatible tool.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/SDG223157/prombank-mcp/issues)
- Documentation: [Full documentation](https://github.com/SDG223157/prombank-mcp/wiki)

## Changelog

### v0.1.0
- Initial release
- Core prompt management functionality
- MCP server implementation
- REST API with OpenAPI documentation
- CLI interface with rich terminal support
- Import/export capabilities
- Fabric patterns integration