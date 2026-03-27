# Contributing to Salla MCP Server

Thank you for your interest in contributing to the Salla MCP Server project! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions with other contributors and users.

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/yourusername/fastmcp-openapi-spec.git
cd fastmcp-openapi-spec
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
make dev
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

## Development Workflow

### Code Style

We use:
- **Black** for code formatting (100 char line length)
- **isort** for import sorting
- **Flake8** for linting
- **mypy** for type checking

Run formatting and linting:

```bash
make format
make lint
```

### Writing Tests

- Place tests in `tests/` directory
- Use `tests/unit/` for unit tests
- Use `tests/integration/` for integration tests
- Write tests for all new features
- Ensure tests pass before submitting PR

```bash
make test           # Run all tests
make test-cov       # Run with coverage report
```

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit:

```bash
make dev  # Installs pre-commit hooks
```

To manually run hooks:

```bash
pre-commit run --all-files
```

## Project Structure

```
.
├── src/salla_mcp/        # Main package
│   ├── config.py         # Configuration management
│   ├── main.py           # Server implementation
│   ├── tools/            # MCP tools
│   ├── services/         # Core services
│   └── utils/            # Utilities
├── tests/                # Test suite
├── deployment/           # Docker, K8s configs
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## Making Changes

### 1. Add or Modify Code

- Keep functions small and focused
- Write clear docstrings
- Add type hints
- Add logging as appropriate

### 2. Add Tests

```python
# tests/unit/test_example.py
import pytest

@pytest.mark.unit
def test_example_feature():
    """Test description."""
    # Arrange
    # Act
    # Assert
```

### 3. Update Documentation

If your change affects:
- API behavior → Update README.md
- Configuration → Update config module docstrings
- Architecture → Update ARCHITECTURE.md
- Code Mode → Update CODE_MODE_GUIDE.md

### 4. Commit Messages

Use clear, descriptive commit messages:

```
feat: Add new feature
fix: Fix bug description
docs: Update documentation
refactor: Refactor component name
test: Add test for feature
chore: Update dependencies
```

## Submitting a Pull Request

1. **Ensure all checks pass:**
   ```bash
   make lint
   make test
   ```

2. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub with:
   - Clear title describing the change
   - Description of what changed and why
   - Reference to related issues
   - Any relevant screenshots or examples

4. **Address Review Comments:**
   - Be responsive to feedback
   - Make requested changes
   - Push updates to the same branch

## Release Process

Releases follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Tagged releases trigger automatic Docker image publishing.

## Reporting Issues

When reporting bugs:

1. **Search existing issues** to avoid duplicates
2. **Provide reproduction steps**
3. **Include environment details:**
   - Python version
   - OS
   - Installation method
4. **Include error logs** and stack traces
5. **Provide minimal reproducible example**

Use the issue template if available.

## Documentation

### API Documentation

Document all public APIs:

```python
def search_endpoints(query: str, limit: int = 10) -> List[dict]:
    """
    Search for endpoints matching query.

    Args:
        query: Search query matching path/summary/tags
        limit: Maximum results to return (1-100)

    Returns:
        List of matching endpoint definitions

    Raises:
        SearchError: If search fails
    """
```

### Type Hints

Always include type hints:

```python
from typing import Optional, List, Dict

def execute(
    endpoint: str,
    method: str = "GET",
    parameters: Optional[Dict[str, any]] = None,
) -> Dict[str, any]:
    """Execute API endpoint."""
    pass
```

## Development Tools

### Useful Commands

```bash
# Run specific test
pytest tests/unit/test_search.py::test_search_products -v

# Run with coverage threshold
pytest tests/ --cov=src/salla_mcp --cov-fail-under=80

# Check specific file with mypy
mypy src/salla_mcp/tools/search.py

# Format specific directory
black src/salla_mcp/tools

# View Makefile help
make help
```

### VS Code Extensions (Recommended)

- Python (microsoft.python)
- Pylance (ms-python.vscode-pylance)
- Black Formatter (ms-python.black-formatter)
- isort (ms-python.isort)
- Flake8 (ms-python.flake8)
- Pytest (littlefoxteam.vscode-pytest)

## Questions?

- Open a discussion on GitHub
- Check existing documentation
- Review closed issues for solutions
- Ask in pull request comments

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
