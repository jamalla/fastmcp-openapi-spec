# Salla API MCP Server

An MCP (Model Context Protocol) server that wraps the Salla API using an OpenAPI specification. Built with the two-tool design pattern (`search` + `execute`) for Code Mode optimization.

## Overview

This MCP server provides intelligent access to the Salla API through:

- **`search` tool**: Query available endpoints from the OpenAPI spec without loading the full spec into the agent context
- **`execute` tool**: Call API endpoints with dynamic parameters and request bodies

This design follows **Code Mode principles** — the agent doesn't need to ingest endpoint definitions; instead, it queries them on demand through the `search` tool.

## Features

✅ Load and parse OpenAPI 3.1 specifications  
✅ Search endpoints by path, method, summary, description, or tags  
✅ Execute API calls with query/path parameters and request bodies  
✅ Bearer token authentication  
✅ Comprehensive error handling  
✅ Type-safe request/response handling  

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# or: source venv/bin/activate  # On macOS/Linux

pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update with your Salla API credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
SALLA_BASE_URL=https://api.salla.dev/v2
SALLA_API_TOKEN=your-salla-api-token-here
OPENAPI_SPEC_PATH=./openapi.json
```

### 3. Run the Server

```bash
python server.py
```

The server will:
- Load the OpenAPI specification
- Report the number of endpoints found
- Start listening for MCP client connections

## Tool Reference

### `search` Tool

Search for available API endpoints.

**Input:**
```json
{
  "query": "products",
  "limit": 10
}
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
      "parameters": [...],
      "requestBody": null
    }
  ],
  "count": 1,
  "query": "products"
}
```

### `execute` Tool

Call an API endpoint.

**Input:**
```json
{
  "endpoint": "/products",
  "method": "GET",
  "parameters": {
    "page": 1,
    "limit": 20
  }
}
```

**For POST/PUT endpoints with body:**
```json
{
  "endpoint": "/products",
  "method": "POST",
  "body": {
    "name": "New Product",
    "price": 99.99,
    "description": "Product description"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "statusCode": 200,
  "data": { ... }
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "SALLA_API_TOKEN not configured"
}
```

## Project Structure

```
.
├── server.py              # Main MCP server implementation
├── openapi.json           # Salla API OpenAPI specification
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment configuration
├── .env                  # Local environment configuration (not in git)
└── README.md             # This file
```

## Architecture

### Two-Tool Design Pattern

This server implements Code Mode principles with two tools:

1. **search**: Query the OpenAPI spec for endpoint details
   - Lightweight query interface
   - Doesn't expose full spec to agent
   - Matches on path, method, summary, description, tags

2. **execute**: Call endpoints with validated parameters
   - Strict request/response contracts
   - Bearer token authentication
   - Error handling and reporting

**Why this matters:**
- Agents only receive endpoint metadata when needed
- Reduces context window usage
- Scales better than embedding full API documentation
- Enables agent discovery of API capabilities

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SALLA_API_TOKEN` | Yes | — | Bearer token for Salla API authentication |
| `SALLA_BASE_URL` | No | `https://api.salla.dev/v2` | Base URL for API calls |
| `OPENAPI_SPEC_PATH` | No | `./openapi.json` | Path to OpenAPI specification file |

### API Token Setup

1. Go to [Salla Developer Console](https://developer.salla.dev/)
2. Create or select your application
3. Generate API credentials
4. Add token to `.env`: `SALLA_API_TOKEN=your-token-here`

## Usage with Agents

### VS Code Copilot Agent Mode

To use this server with a Copilot agent:

1. **Configure the MCP transport** in VS Code settings:

```json
{
  "claude.mcpServers": {
    "salla-api": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/fastmcp-openapi-spec"
    }
  }
}
```

2. **Example agent prompt:**

```
Search for products endpoint, then list the first 5 products using the Salla API.
```

The agent will:
- Call `search` with query "products"
- Examine results to find GET /products endpoint
- Call `execute` with appropriate parameters
- Return product data

## Development Guide

### Adding to the OpenAPI Spec

If you need to update or add endpoints:

1. Modify `openapi.json` directly
2. Restart the server to reload the spec
3. New endpoints will be immediately searchable

### Extending the Server

To add more tools or modify behavior:

1. Edit `server.py`
2. Add new tool handler in `call_tool()` function
3. Add tool metadata in `list_tools()` function
4. Restart the server

### Error Debugging

- Missing token: `{"error": "SALLA_API_TOKEN not configured", "status": "error"}`
- Invalid endpoint: Check the `search` tool output for correct path and method
- Authentication failed: Verify token is valid in Salla console

## Testing

### Manual Testing

```bash
# Start the server
python server.py

# In another terminal, test tools via MCP client
# Example: search for products
mcp-cli call-tool salla-api search --query "products"

# Execute GET request
mcp-cli call-tool salla-api execute \
  --endpoint "/products" \
  --method "GET" \
  --parameters '{"page": 1, "limit": 10}'
```

## Troubleshooting

**Issue: "OpenAPI spec not found"**
- Verify `openapi.json` exists in the project directory
- Check `OPENAPI_SPEC_PATH` in `.env` is correct

**Issue: API calls return 401 Unauthorized**
- Verify `SALLA_API_TOKEN` is set correctly
- Token may have expired; refresh in Salla console
- Check token has required scopes for the endpoint

**Issue: Search returns no results**
- Try broader search terms
- Check endpoint exists in OpenAPI spec
- Verify spec is being loaded (check startup logs)

## Performance Notes

- **Search performance**: O(n) where n = number of endpoints in spec
- **Execute performance**: Depends on Salla API response time
- **Context efficiency**: Two-tool design reduces token usage vs. sending full spec

## Security Considerations

⚠️ **Production Deployment:**
- Use environment-based secrets management (not `.env` files)
- Implement request validation and rate limiting
- Add OAuth token refresh mechanism
- Audit API access logs
- Use HTTPS for all connections
- Restrict `execute` tool scope in production

### Auth Strategy

Current implementation:
- Bearer token in Authorization header
- Token provided via environment variable

Future extensions:
- OAuth with token downscoping
- API key rotation
- Scope-based access control

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test locally
4. Submit PR with clear description

## License

MIT

## Resources

- [Salla Developer Docs](https://developer.salla.dev/)
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [OpenAPI 3.1 Spec](https://spec.openapis.org/oas/v3.1.0)
- [fastmcp Framework](https://github.com/zeke/fastmcp)

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review [MCP Server Debugging Guide](./docs/debugging.md)
3. Open an issue with environment details and error logs