# Salla API MCP Server

A production-grade Model Context Protocol (MCP) server that wraps the Salla E-commerce API using OpenAPI specifications. Built with the two-tool Code Mode design pattern for optimal efficiency with AI agents.

[![Tests](https://github.com/jamalla/fastmcp-openapi-spec/workflows/Tests/badge.svg)](https://github.com/jamalla/fastmcp-openapi-spec/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview

This MCP server provides intelligent access to the Salla API through a two-tool design pattern:

- **`search` tool**: Query available endpoints from the OpenAPI spec without loading the full documentation
- **`execute` tool**: Call API endpoints with dynamic parameters and request bodies

This Code Mode pattern dramatically reduces token usage and improves agent reasoning compared to large tool catalogs.

## Key Features

✅ **Efficient Code Mode Design** - Two composable tools scale to any API size  
✅ **OpenAPI 3.1 Support** - Parse and query any OpenAPI specification  
✅ **Bearer Token Authentication** - Secure API calls with environment-based credentials  
✅ **Production-Ready** - Comprehensive configuration, logging, error handling  
✅ **Type-Safe** - Full type hints and validation with Pydantic  
✅ **Async/Await** - Non-blocking I/O with httpx  
✅ **Docker & Kubernetes** - Container and orchestration support included  
✅ **CI/CD Ready** - GitHub Actions workflows for testing and publishing  

## Quick Start

### 1. Installation

```bash
git clone https://github.com/jamalla/fastmcp-openapi-spec.git
cd fastmcp-openapi-spec

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -e .
```

### 2. Configuration

```bash
cp config/development.env .env
# Edit .env and set SALLA_API_TOKEN
```

### 3. Run Server

```bash
python server.py
```

Expected output:
```
Initializing Salla MCP Server
Loaded OpenAPI spec from ./openapi.json
Found 47 endpoints
Server initialized successfully
Starting Salla MCP Server
```

## Project Structure

```
fastmcp-openapi-spec/
├── src/salla_mcp/              # Main package
│   ├── config.py               # Configuration management
│   ├── main.py                 # MCP server implementation
│   ├── tools/                  # MCP tools (search, execute)
│   ├── services/               # Services (OpenAPI loader, API client)
│   └── utils/                  # Utilities (logging, errors)
├── tests/                      # Test suite (unit, integration)
├── deployment/                 # Docker, systemd, Kubernetes configs
├── docs/                       # Project documentation
├── scripts/                    # Utility scripts
├── config/                     # Environment configurations
├── pyproject.toml              # Project metadata & dependencies
├── Makefile                    # Development tasks
└── server.py                   # Entry point
```

## Tool Reference

### Search Tool

Query available endpoints in the OpenAPI specification.

```python
# Search for endpoints related to "products"
search(query="products", limit=10)
```

**Response:**
```json
{
  "results": [
    {
      "path": "/products",
      "method": "GET",
      "summary": "Get all products",
      "description": "Retrieve a paginated list of products",
      "tags": ["Products"],
      "parameters": [...]
    }
  ],
  "count": 1,
  "query": "products"
}
```

### Execute Tool

Call an API endpoint with authentication and error handling.

```python
# Get first 10 products
execute(
  endpoint="/products",
  method="GET",
  parameters={"page": 1, "limit": 10}
)
```

**Response:**
```json
{
  "status": "success",
  "statusCode": 200,
  "data": {
    "products": [...],
    "pagination": {...}
  }
}
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SALLA_API_TOKEN` | ✓ | — | Bearer token for API authentication |
| `SALLA_BASE_URL` | | `https://api.salla.dev/v2` | API base URL |
| `LOG_LEVEL` | | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | | `json` | Log format (json, text) |
| `API_TIMEOUT` | | `30` | Request timeout in seconds |
| `API_RETRIES` | | `0` | Number of retries for failed requests |

### Configuration Files

- **Development**: `config/development.env`
- **Staging**: `config/staging.env`
- **Production**: `config/production.env`

## Usage with Copilot Agents

### VS Code Setup

See [VSCODE_SETUP.md](docs/VSCODE_SETUP.md) for detailed configuration.

### Example Agent Prompt

```
@agent Search for products endpoint and fetch the first 5 products
        ordered by price.
```

The agent will:
1. Call `search("products")`
2. Identify the GET /products endpoint
3. Call `execute` with appropriate parameters
4. Return formatted product data

## Development

### Setup Development Environment

```bash
make dev
```

### Run Tests

```bash
make test          # Run all tests
make test-cov      # With coverage report
```

### Code Quality

```bash
make lint          # Run linters
make format        # Auto-format code
```

### See All Commands

```bash
make help
```

## Docker Deployment

### Build Image

```bash
docker build -f deployment/Dockerfile -t salla-mcp:latest .
```

### Run Container

```bash
docker run -d \
  -e SALLA_API_TOKEN=your-token \
  -v $(pwd)/openapi.json:/app/openapi.json \
  salla-mcp:latest
```

### Docker Compose

```bash
docker-compose -f deployment/docker-compose.yml up -d
```

## Kubernetes Deployment

```bash
kubectl apply -f deployment/kubernetes/deployment.yaml
```

See [INSTALLATION.md](docs/INSTALLATION.md) for detailed deployment instructions.

## Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Setup for all environments
- **[Architecture](docs/ARCHITECTURE.md)** - System design and patterns
- **[Code Mode Guide](docs/CODE_MODE_GUIDE.md)** - Why two-tool design scales better
- **[VS Code Integration](docs/VSCODE_SETUP.md)** - Agent Mode configuration
- **[Contributing](CONTRIBUTING.md)** - Development guidelines

## Architecture Highlights

### Two-Tool Code Mode Pattern

Instead of 47 individual tools (one per endpoint), this server provides:

| Traditional | Code Mode (This Server) |
|-----------|----------------------|
| 47 tools in agent context | 2 tools in agent context |
| ~18,000 tokens overhead | ~1,200 tokens overhead |
| Inflexible to API changes | Automatic discovery of new endpoints |
| Poor reasoning efficiency | Better agent decision-making |

See [CODE_MODE_GUIDE.md](docs/CODE_MODE_GUIDE.md) for depth analysis.

### Component Design

```
┌──────────────────────────────────┐
│       MCP Server (main.py)       │
└────────┬─────────────────────────┘
         │
    ┌────┴────┐
    │          │
┌───▼───┐  ┌──▼────┐
│ Search│  │Execute │
│ Tool  │  │ Tool   │
└───┬───┘  └──┬─────┘
    │         │
    │    ┌────▼──────────┐
    │    │  API Client   │
    │    │  (httpx)      │
    │    └────┬──────────┘
    │         │
    ▼    ┌────▼──────────┐
  OpenAPI │   Salla API   │
    ▲    └───────────────┘
    │
Load at
startup
```

## Security

### Authentication
- Bearer token authentication via Authorization header
- Token stored in environment variables (never in code/git)
- Validation at server startup

### Best Practices
- Use environment-based secrets management
- Never commit `.env` files
- Rotate tokens regularly
- Monitor API access logs
- Use HTTPS for all connections

**Production Hardening:**
- Add request rate limiting
- Implement OAuth token refresh
- Add scope-based access control
- Use API key rotation

## Performance

- **Search**: O(n) where n = endpoints in spec (typically < 100ms)
- **Execute**: Network latency + API latency (typically 200-2000ms)
- **Context Efficiency**: 22x token savings vs. large tool catalog

## Troubleshooting

### Common Issues

**"SALLA_API_TOKEN not configured"**
```bash
export SALLA_API_TOKEN=your-token
```

**"OpenAPI spec not found"**
```bash
# Ensure openapi.json exists
ls -la openapi.json
```

**"Endpoint not found in search"**
1. Search uses path, summary, description, tags
2. Try broader search terms
3. Check endpoint exists in spec

See [INSTALLATION.md](docs/INSTALLATION.md#troubleshooting) for more.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code style and standards
- Testing requirements
- Pull request process
- Development setup

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_search.py -v

# Run with coverage
pytest tests/ --cov=src/salla_mcp --cov-report=html
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## Citation

If you use this project in research or production, please cite:

```bibtex
@software{salla_mcp_2024,
  title={Salla API MCP Server},
  author={Jamalla},
  year={2024},
  url={https://github.com/jamalla/fastmcp-openapi-spec}
}
```

## Resources

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)
- [Salla Developer Portal](https://developer.salla.dev/)
- [Claude Model Card](https://www.anthropic.com/model-cards)

## Support

For help:
1. 📖 Check [documentation](docs/README.md)
2. 🔍 Search [GitHub issues](https://github.com/jamalla/fastmcp-openapi-spec/issues)
3. 🆕 Open a [new issue](https://github.com/jamalla/fastmcp-openapi-spec/issues/new)
4. 💬 Start a [discussion](https://github.com/jamalla/fastmcp-openapi-spec/discussions)

---

Built with ❤️ for AI agents and production systems.
