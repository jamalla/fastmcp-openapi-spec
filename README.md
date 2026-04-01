# OpenAPI → MCP Server

Convert any OpenAPI specification into an MCP server that AI agents can use. Instead of registering one tool per endpoint (which bloats agent context), this server exposes just **two tools**:

| Tool | Purpose |
|------|---------|
| `search` | Find API endpoints by keyword (searches paths, summaries, descriptions, tags) |
| `execute` | Call any endpoint with automatic Bearer token authentication |

This keeps the agent's context small (~1,200 tokens) regardless of how many endpoints the API has.

## How It Works

```
┌─────────────┐     ┌──────────────────┐     ┌──────────┐
│  AI Agent    │────▶│  MCP Server      │────▶│ REST API │
│  (Claude,    │◀────│                  │◀────│ (Salla)  │
│   Cursor,..) │     │  search: query   │     └──────────┘
│              │     │    OpenAPI spec   │
│              │     │  execute: proxy   │
│              │     │    HTTP + auth    │
└─────────────┘     └──────────────────┘
```

1. **At startup**, the server loads `openapi.json` and indexes all paths in memory
2. **`search("products")`** — scans the spec and returns matching endpoints with their parameters, methods, and descriptions
3. **`execute("/products", "GET", parameters={"page": 1})`** — makes the actual HTTP call to the API, injecting the Bearer token automatically
4. The agent never sees the full spec — it discovers what it needs on demand

## Quick Start

```bash
# Install
pip install -e .

# Configure
cp .env.example .env
# Edit .env → set SALLA_API_TOKEN

# Run (stdio for MCP clients like Claude Desktop, VS Code)
python server.py

# Run as HTTP server (for direct agent access)
python server.py streamable-http
```

## Transport Modes

| Mode | Command | Use Case |
|------|---------|----------|
| **stdio** | `python server.py` | MCP clients (Claude Desktop, VS Code Copilot, Cursor) |
| **streamable-http** | `python server.py streamable-http` | Direct HTTP access from AI agents, web apps |
| **sse** | `python server.py sse` | Server-Sent Events for streaming clients |

### HTTP Mode

When running with `streamable-http`, the server listens on `http://0.0.0.0:8000/mcp` by default. Configure with environment variables:

```bash
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

## Configuration

All via environment variables (or `.env` file):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SALLA_API_TOKEN` | Yes | — | Bearer token for API authentication |
| `SALLA_BASE_URL` | | `https://api.salla.dev/v2` | API base URL |
| `OPENAPI_SPEC_PATH` | | `./openapi.json` | Path to OpenAPI spec file |
| `SERVER_HOST` | | `0.0.0.0` | HTTP server bind address |
| `SERVER_PORT` | | `8000` | HTTP server port |
| `API_TIMEOUT` | | `30` | Request timeout (seconds) |

## Using with AI Agents

### Claude Desktop / Claude Code

Add to your MCP config (`claude_desktop_config.json` or `.claude.json`):

```json
{
  "mcpServers": {
    "salla-api": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/fastmcp-openapi-spec"
    }
  }
}
```

Then ask Claude:

> "Search for product endpoints and list the first 5 products"

Claude will:
1. Call `search("products")` → discovers `GET /products`, `POST /products`, etc.
2. Call `execute("/products", "GET", parameters={"limit": 5})` → gets the data
3. Present the results

### Direct HTTP Access (for custom agents)

Start the server in HTTP mode:

```bash
python server.py streamable-http
```

Then any AI agent or application can connect using the MCP protocol over HTTP at `http://localhost:8000/mcp`.

#### Python agent example (using `mcp` client SDK):

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client("http://localhost:8000/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()

            # Discover endpoints
            result = await session.call_tool("search", {"query": "orders"})
            print(result)

            # Execute an API call
            result = await session.call_tool("execute", {
                "endpoint": "/orders",
                "method": "GET",
                "parameters": {"page": 1, "limit": 10}
            })
            print(result)
```

#### cURL example (raw MCP-over-HTTP):

```bash
# Initialize session
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'

# Call the search tool
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search","arguments":{"query":"products","limit":5}}}'
```

### VS Code Copilot Agent Mode

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "salla-api": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "salla-api": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/fastmcp-openapi-spec"
    }
  }
}
```

## Agent Workflow Examples

### Example 1: Browse products

```
Agent                          MCP Server                    Salla API
  │                               │                             │
  │ search("products")            │                             │
  │──────────────────────────────▶│                             │
  │   [{path:"/products",         │                             │
  │     method:"GET", ...}]       │                             │
  │◀──────────────────────────────│                             │
  │                               │                             │
  │ execute("/products","GET",    │  GET /v2/products?limit=5   │
  │   {limit:5})                  │────────────────────────────▶│
  │                               │   {products: [...]}         │
  │   {status:"success",          │◀────────────────────────────│
  │    data:{products:[...]}}     │                             │
  │◀──────────────────────────────│                             │
```

### Example 2: Create an order

```
User: "Create an order for customer 123 with product SKU-456"

Agent thinks: I need to find the create order endpoint first.

→ search("create order")
← [{path: "/orders", method: "POST", requestBody: {required: ["customer_id", "items"]}}]

Agent thinks: Now I know the endpoint and required fields.

→ execute("/orders", "POST", body={"customer_id": 123, "items": [{"sku": "SKU-456", "quantity": 1}]})
← {status: "success", statusCode: 201, data: {id: 789, status: "pending"}}

Agent: "Order #789 created successfully for customer 123."
```

### Example 3: Multi-step investigation

```
User: "What's the status of order 789 and who placed it?"

→ search("order")
← [GET /orders/{id}, GET /orders, POST /orders, ...]

→ execute("/orders/789", "GET")
← {data: {id: 789, status: "shipped", customer_id: 123}}

→ search("customer")
← [GET /customers/{id}, ...]

→ execute("/customers/123", "GET")
← {data: {id: 123, name: "Ahmad", email: "ahmad@example.com"}}

Agent: "Order 789 is shipped. It was placed by Ahmad (ahmad@example.com)."
```

## Adapting for Other APIs

This server works with **any OpenAPI 3.x spec**. To use it with a different API:

1. Replace `openapi.json` with your API's spec
2. Update `.env` with your API's base URL and auth token:
   ```
   SALLA_BASE_URL=https://api.yourservice.com/v1
   SALLA_API_TOKEN=your-token
   ```
3. Run `python server.py`

The `search` and `execute` tools automatically adapt to whatever endpoints are defined in the spec.

## Project Structure

```
server.py          ← entry point (registers tools, runs transport)
src/
  config.py        ← env vars + OpenAPI spec loading
  tools.py         ← search and execute tool implementations
openapi.json       ← your API specification
.env.example       ← configuration template
pyproject.toml     ← dependencies
```

## License

MIT
