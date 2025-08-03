# Setup Instructions for Prombank MCP

This guide will help you set up and test the Prombank MCP system.

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install the Package

```bash
pip install -e .
```

### 3. Initialize the Database

```bash
prombank init
```

## Quick Test

Run the setup test script to verify everything works:

```bash
python setup_test.py
```

This will:
- Install the package
- Initialize the database
- Create a test prompt
- List and search prompts
- Verify all components are working

## Manual Testing

### 1. Test CLI

```bash
# Create a prompt
prombank prompt create --title "My First Prompt" --content "Hello, this is a test prompt"

# List prompts
prombank prompt list

# Show prompt details
prombank prompt show 1

# Search prompts
prombank prompt list --search "test"
```

### 2. Test MCP Server

In one terminal:
```bash
prombank mcp-server
```

This starts the MCP server that can be connected to tools like Cursor.

### 3. Test REST API

In another terminal:
```bash
prombank server
```

Then visit: http://localhost:8000/docs for the interactive API documentation.

### 4. Test API Endpoints

```bash
# Get all prompts
curl "http://localhost:8000/api/v1/prompts"

# Search prompts
curl "http://localhost:8000/api/v1/prompts?search=test"

# Get health status
curl "http://localhost:8000/health"
```

## Integration with Cursor

1. Start the MCP server:
```bash
prombank mcp-server
```

2. Add to your Cursor MCP configuration file:
```json
{
  "prombank-mcp": {
    "command": "prombank",
    "args": ["mcp-server"]
  }
}
```

3. Restart Cursor to load the new MCP server.

4. You should now be able to use prompts directly from Cursor using the MCP tools.

## Common Commands

### Prompt Management
```bash
# Create from file
prombank prompt create --title "Code Review" --file my_prompt.txt

# Update existing prompt
prombank prompt update 1 --title "Updated Title" --version

# Archive prompt
prombank prompt delete 1 --archive

# Show with usage tracking
prombank prompt show 1 --use
```

### Import/Export
```bash
# Import from JSON
prombank import file prompts.json

# Import Fabric patterns
prombank import fabric ~/fabric/patterns

# Export to markdown
prombank export file my_prompts.md --format markdown
```

### Categories and Tags
```bash
# Create category
prombank category create --name "Development" --color "#10b981"

# List categories
prombank category list

# Filter by category
prombank prompt list --category "Development"
```

## Troubleshooting

### Database Issues
```bash
# Reinitialize database
rm prombank.db
prombank init
```

### Import Issues
- Check file format and encoding
- Verify JSON structure for JSON imports
- Use `--format` option to specify format explicitly

### MCP Server Issues
- Ensure no other process is using the same port
- Check that the MCP client supports the protocol version
- Verify the command path in MCP configuration

### API Server Issues
- Check if port 8000 is available
- Use `--host 0.0.0.0` to bind to all interfaces
- Use `--port 8080` to use a different port

## Configuration

Create a `.env` file (copy from `.env.example`) to customize:

```bash
cp .env.example .env
```

Edit the `.env` file to change database URL, ports, etc.

## Development

For development work:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Create database migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## Support

If you encounter issues:

1. Check the logs for error messages
2. Verify all dependencies are installed
3. Ensure Python version compatibility
4. Check database permissions and disk space
5. Consult the README.md for detailed documentation

For more help, create an issue on the GitHub repository.