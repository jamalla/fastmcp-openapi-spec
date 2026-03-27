# Architecture & Design

## Overview

The Salla API MCP Server implements a **two-tool Code Mode design pattern** optimized for efficient agent interactions with OpenAPI-based APIs.

## Design Philosophy: Code Mode Pattern

### Traditional Approach (Large Tool Catalog)
```
Agent Context: [Tool 1][Tool 2][Tool 3]...[Tool 47] + Full API Documentation
               ↓
Massive token consumption, context bloat, slower reasoning
```

### Code Mode Pattern (This Implementation)
```
Agent Context: [Search Tool][Execute Tool]
               ↓
Agent queries endpoint definitions on-demand via search
               ↓
Efficient reasoning + dynamic discovery + token savings
```

## Two-Tool Architecture

### Tool 1: `search`

**Purpose**: Query the OpenAPI specification for endpoint metadata without loading the full spec.

**Design**:
- Lightweight query interface (path, method, summary, description, tags)
- Returns only relevant endpoint metadata
- No large documentation embedded in agent context
- Fast O(n) search across all endpoints

**Example Flow**:
```
Agent: "Find the products endpoint"
  ↓
search("products") 
  ↓
Returns: GET /products, POST /products (as structured data)
  ↓
Agent examines response and selects appropriate operation
```

### Tool 2: `execute`

**Purpose**: Call actual API endpoints with validated parameters.

**Design**:
- Strict request/response contracts
- Bearer token authentication
- Error handling and reporting
- Parameter validation (query, path, body)

**Example Flow**:
```
Agent: "Get first 10 products"
  ↓
execute(endpoint="/products", method="GET", parameters={"limit": 10})
  ↓
Returns: {"status": "success", "statusCode": 200, "data": {...}}
  ↓
Agent processes API response
```

## Data Flow Diagram

```
┌─────────────────────────────────────┐
│    VS Code Copilot Agent Mode       │
│                                     │
│  "Search for products endpoint"     │
│  "Then fetch the first 10 products" │
└────────────┬────────────────────────┘
             │
             │ MCP Protocol
             ↓
   ┌─────────────────────────┐
   │  MCP Server (this code) │
   │                         │
   │  ┌──────────────────┐   │
   │  │  search tool     │   │ ← Queries OpenAPI spec
   │  │  (lightweight)   │   │
   │  └──────────────────┘   │
   │                         │
   │  ┌──────────────────┐   │
   │  │  execute tool    │   │ ← Calls actual API
   │  │  (w/ auth)       │   │
   │  └──────────────────┘   │
   │                         │
   │  ┌──────────────────┐   │
   │  │  openapi.json    │   │ ← Server-side spec
   │  │  (not in agent   │   │
   │  │   context)       │   │
   │  └──────────────────┘   │
   └────────────┬────────────┘
                │
                │ HTTPS
                ↓
        ┌───────────────────┐
        │   Salla API       │
        │  (saas ecommerce) │
        └───────────────────┘
```

## Message Protocol

### Search Tool Call

**Request**:
```
{
  "tool": "search",
  "input": {
    "query": "products",
    "limit": 10
  }
}
```

**Response**:
```
{
  "results": [
    {
      "path": "/products",
      "method": "GET",
      "summary": "Get all products",
      "description": "List products with pagination",
      "tags": ["Products"],
      "parameters": [
        {
          "name": "page",
          "in": "query",
          "schema": {"type": "integer"}
        }
      ]
    }
  ],
  "count": 1,
  "query": "products"
}
```

### Execute Tool Call

**Request**:
```
{
  "tool": "execute",
  "input": {
    "endpoint": "/products",
    "method": "GET",
    "parameters": {
      "page": 1,
      "limit": 10
    }
  }
}
```

**Response (Success)**:
```
{
  "status": "success",
  "statusCode": 200,
  "data": {
    "products": [
      {"id": 1, "name": "Product 1", "price": 99.99},
      {...}
    ],
    "pagination": {"page": 1, "limit": 10, "total": 150}
  }
}
```

**Response (Error)**:
```
{
  "status": "error",
  "error": "SALLA_API_TOKEN not configured"
}
```

## Component Architecture

```
┌──────────────────────────────────────────────────────┐
│            MCP Server (server.py)                    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────┐        ┌─────────────────────┐  │
│  │  list_tools()  │        │  call_tool()        │  │
│  │                │        │  - search handler   │  │
│  │  Returns:      │        │  - execute handler  │  │
│  │  - search      │        └─────────────────────┘  │
│  │  - execute     │                                 │
│  └────────────────┘        ┌─────────────────────┐  │
│                            │ search_endpoints()  │  │
│                            │                     │  │
│                            │ - Query parsing     │  │
│                            │ - OpenAPI matching  │  │
│                            │ - Result formatting │  │
│                            └─────────────────────┘  │
│                                                      │
│                            ┌─────────────────────┐  │
│                            │execute_endpoint()   │  │
│                            │                     │  │
│                            │ - Auth handling     │  │
│                            │ - HTTP request      │  │
│                            │ - Response parsing  │  │
│                            │ - Error handling    │  │
│                            └─────────────────────┘  │
│                                                      │
├──────────────────────────────────────────────────────┤
│  load_openapi_spec()                                 │
│  - Reads openapi.json at startup                     │
│  - Parses and validates spec structure               │
│  - Maintains in-memory for search queries            │
├──────────────────────────────────────────────────────┤
│  Configuration (from .env)                           │
│  - SALLA_API_TOKEN (Bearer auth)                     │
│  - SALLA_BASE_URL (API endpoint)                     │
│  - OPENAPI_SPEC_PATH (spec file location)            │
└──────────────────────────────────────────────────────┘
```

## Request/Response Contracts

### Search Input Schema
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query"
    },
    "limit": {
      "type": "integer",
      "description": "Max results (default: 10)"
    }
  },
  "required": ["query"]
}
```

### Execute Input Schema
```json
{
  "type": "object",
  "properties": {
    "endpoint": {
      "type": "string",
      "description": "API endpoint path"
    },
    "method": {
      "type": "string",
      "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]
    },
    "parameters": {
      "type": "object",
      "description": "Query/path params"
    },
    "body": {
      "type": "object",
      "description": "Request body"
    }
  },
  "required": ["endpoint"]
}
```

## Security Model

### Authentication Layer
```
┌──────────────────────────────┐
│  MCP Client (Agent)          │
│                              │
│  [No credentials needed]     │
└──────────────┬───────────────┘
               │
               │ MCP Protocol (stdio/HTTP)
               ↓
┌──────────────────────────────┐
│  MCP Server                  │
│                              │
│  - Holds SALLA_API_TOKEN     │
│  - Validates all requests    │
│  - Auth enforcement layer    │
└──────────────┬───────────────┘
               │
               │ HTTPS + Bearer Token
               ↓
┌──────────────────────────────┐
│  Salla API                   │
│                              │
│  - Validates Bearer Token    │
│  - Enforces scope            │
│  - Rate limiting             │
│  - Audit logging             │
└──────────────────────────────┘
```

**Key Points**:
- Agent never handles credentials
- Server acts as auth proxy
- Token stored safely in `.env` (not in code/git)
- All API calls authenticated with Bearer token

## Performance Characteristics

### Search Performance
- **Complexity**: O(n) where n = number of endpoints
- **Typical Time**: < 100ms for spec with 50+ endpoints
- **Memory Usage**: Entire spec loaded once at startup
- **Scalability**: Suitable for APIs with < 1000 endpoints

### Execute Performance
- **Latency**: Network latency + Salla API latency
- **Typical Time**: 200-2000ms depending on endpoint
- **Timeouts**: 30 second default timeout
- **Retries**: No automatic retries (agent handles strategy)

## Error Handling Strategy

```
┌─────────────────────────┐
│  Tool Call              │
└────────────┬────────────┘
             │
             ↓
    ┌────────────────┐
    │  Validation    │ ← Input schema validation
    └────┬───────────┘
         │ Error? 
         ├─ Yes → Return {"error": "msg", "status": "error"}
         │
         ↓ No
    ┌────────────────┐
    │  Execution     │ ← Network call or query
    └────┬───────────┘
         │ Error?
         ├─ Yes → Return {"error": "msg", "status": "error"}
         │
         ↓ No
    ┌────────────────┐
    │  Response      │ ← Format and return result
    │  Formatting    │
    └────────────────┘
```

## Comparison: Tool Design Patterns

### Pattern 1: Large Catalog (Not Recommended)
```
Tools: [GET /products][POST /products][GET /orders][...]
Problems:
- 47 tools = massive agent context
- Hard to discover capabilities
- Inflexible to API changes
- High token cost
```

### Pattern 2: Two-Tool Code Mode (This Implementation)
```
Tools: [search][execute]
Benefits:
- Small context (2 tools only)
- Dynamic discovery
- Easy to adapt
- Low token cost
- Better reasoning
```

### Pattern 3: Hierarchical Tools
```
Tools: [resources][products][orders][...]
Problems:
- Still large number of tools
- Rigid category structure
- Hard to cross-domain queries
```

## Extensibility

### Adding Custom Logic
Current search only matches metadata. To add:
- Semantic search capabilities
- Usage-based ranking
- Related endpoint suggestions

### Caching Strategy
Current loads full spec at startup. Future:
- Cache invalidation on spec updates
- Lazy loading for large specs
- Endpoint popularity tracking

### Rate Limiting
Current implementation has no rate limiting. Add:
- Per-client limits
- Token bucket system
- Quota management

## Testing Strategy

```
Unit Tests:
- search_endpoints() with various queries
- execute_endpoint() with mock responses

Integration Tests:
- Full flow: search → execute
- Error scenarios
- Auth failures

Performance Tests:
- Search speed with various spec sizes
- Memory usage under load
- API timeout handling
```

## Future Enhancements

1. **OAuth Token Refresh**
   - Automatic token renewal
   - Scope-based access control

2. **Caching Layer**
   - Cache search results
   - Cache execute responses with TTL

3. **Request Validation**
   - Schema-based parameter validation
   - Type coercion

4. **Monitoring**
   - Usage metrics
   - Performance tracking
   - Error rate monitoring

5. **Multi-API Support**
   - Switch between different base URLs
   - Multiple API tokens per service

## References

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [OpenAPI 3.1 Standard](https://spec.openapis.org/oas/v3.1.0)
- [HTTP Bearer Authentication](https://tools.ietf.org/html/rfc6750)
- [Code Mode Deep Dive](./CODE_MODE_GUIDE.md)
