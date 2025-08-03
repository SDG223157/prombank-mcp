# Contributing to Prombank MCP

Thank you for your interest in contributing to Prombank MCP! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

- Use the [GitHub Issues](https://github.com/SDG223157/prombank-mcp/issues) page to report bugs
- Search existing issues before creating a new one
- Include detailed information about the bug, including steps to reproduce
- Provide system information (OS, Python version, etc.)

### Suggesting Features

- Open a feature request on [GitHub Issues](https://github.com/SDG223157/prombank-mcp/issues)
- Describe the feature and its use case
- Explain why this feature would be beneficial

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Install dependencies** and set up development environment:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```
3. **Make your changes** following the coding standards
4. **Add tests** for new functionality
5. **Update documentation** if needed
6. **Test your changes** thoroughly
7. **Submit a pull request** with a clear description

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment (recommended)

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/your-username/prombank-mcp
cd prombank-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Initialize database
prombank init

# Run tests
pytest tests/
```

## Coding Standards

### Python Code Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use type hints where possible
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

### Code Organization

- Place new features in appropriate modules
- Update `__init__.py` files when adding new modules
- Follow the existing project structure
- Separate concerns (models, services, API routes)

### Documentation

- Update README.md for significant changes
- Add docstrings to new functions and classes
- Update API documentation if adding new endpoints
- Include examples in documentation

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/prombank

# Run specific test file
pytest tests/test_prompt_service.py
```

### Writing Tests

- Write tests for all new functionality
- Include both positive and negative test cases
- Test edge cases and error conditions
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

### Test Structure

```python
def test_create_prompt_with_valid_data():
    # Arrange
    service = PromptService(db)
    prompt_data = {"title": "Test", "content": "Test content"}
    
    # Act
    result = service.create_prompt(**prompt_data)
    
    # Assert
    assert result.title == "Test"
    assert result.content == "Test content"
```

## Database Changes

### Migrations

- Use Alembic for all database schema changes
- Create migrations for model changes:
  ```bash
  alembic revision --autogenerate -m "Description of change"
  ```
- Test migrations both up and down
- Include migration in your pull request

### Model Changes

- Update both the model and corresponding Pydantic schemas
- Ensure backward compatibility when possible
- Update API documentation for schema changes

## API Changes

### REST API

- Follow RESTful conventions
- Use appropriate HTTP status codes
- Include proper error handling
- Update OpenAPI documentation
- Maintain backward compatibility when possible

### MCP Server

- Follow MCP protocol specifications
- Test tools with actual MCP clients
- Update tool descriptions and schemas
- Document new tools in README

## Commit Guidelines

### Commit Message Format

```
type(scope): brief description

Optional longer description explaining the change.

Fixes #issue-number
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(api): add prompt search endpoint

Add new endpoint for searching prompts by content with
filtering and pagination support.

Fixes #123

fix(database): resolve connection pooling issue

Update MySQL connection configuration to properly handle
connection pooling in production environments.

docs(readme): update installation instructions

Add section about MySQL setup and Docker deployment
options for better clarity.
```

## Release Process

### Version Numbering

- Follow [Semantic Versioning](https://semver.org/)
- MAJOR.MINOR.PATCH (e.g., 1.2.3)
- Update version in `pyproject.toml`

### Creating Releases

1. Update version number
2. Update CHANGELOG.md
3. Create release notes
4. Tag the release
5. Publish to PyPI (maintainers only)

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Assume good intentions

### Getting Help

- Check existing documentation first
- Search closed issues for solutions
- Ask questions in GitHub Discussions
- Join community discussions

## Security

### Reporting Security Issues

- **Do not** open public issues for security vulnerabilities
- Email security concerns to the maintainers
- Provide detailed information about the vulnerability
- Allow time for fixes before public disclosure

### Security Best Practices

- Never commit sensitive data (passwords, keys, etc.)
- Use environment variables for configuration
- Validate all user inputs
- Follow secure coding practices

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Documentation acknowledgments

Thank you for contributing to Prombank MCP! 🚀