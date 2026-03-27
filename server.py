"""
MCP Server for Salla API with OpenAPI spec.
Implements two-tool design pattern: search (query available endpoints) and execute (call endpoints).
"""

import json
import os
import httpx
from typing import Any, Optional
from contextlib import asynccontextmanager

import mcp.server.models as models
from mcp.server import Server
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SALLA_BASE_URL = os.getenv("SALLA_BASE_URL", "https://api.salla.dev/v2")
SALLA_API_TOKEN = os.getenv("SALLA_API_TOKEN", "")
OPENAPI_SPEC_PATH = os.getenv("OPENAPI_SPEC_PATH", "./openapi.json")

# Global OpenAPI spec
openapi_spec: dict = {}


def load_openapi_spec() -> dict:
    """Load OpenAPI specification from file."""
    global openapi_spec
    try:
        with open(OPENAPI_SPEC_PATH, "r") as f:
            openapi_spec = json.load(f)
        return openapi_spec
    except FileNotFoundError:
        raise RuntimeError(f"OpenAPI spec not found at {OPENAPI_SPEC_PATH}")


class SearchQuery(BaseModel):
    """Model for search tool input."""
    query: str
    limit: int = 10


class ExecuteRequest(BaseModel):
    """Model for execute tool input."""
    endpoint: str
    method: str
    parameters: Optional[dict] = None
    body: Optional[dict] = None


def search_endpoints(query: str, limit: int = 10) -> list[dict]:
    """
    Search available endpoints in the OpenAPI spec.
    
    Args:
        query: Search query (matches path, method, summary, description)
        limit: Maximum number of results to return
        
    Returns:
        List of matching endpoint definitions
    """
    if not openapi_spec:
        return []
    
    results = []
    query_lower = query.lower()
    paths = openapi_spec.get("paths", {})
    
    for path, path_item in paths.items():
        for method in ["get", "post", "put", "delete", "patch"]:
            if method not in path_item:
                continue
            
            operation = path_item[method]
            summary = operation.get("summary", "").lower()
            description = operation.get("description", "").lower()
            tags = [tag.lower() for tag in operation.get("tags", [])]
            
            # Check if query matches
            match_found = (
                query_lower in path.lower()
                or query_lower in summary
                or query_lower in description
                or any(query_lower in tag for tag in tags)
            )
            
            if match_found:
                results.append({
                    "path": path,
                    "method": method.upper(),
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "tags": operation.get("tags", []),
                    "parameters": operation.get("parameters", []),
                    "requestBody": operation.get("requestBody"),
                })
        
        if len(results) >= limit:
            break
    
    return results[:limit]


async def execute_endpoint(
    endpoint: str,
    method: str,
    parameters: Optional[dict] = None,
    body: Optional[dict] = None,
) -> dict:
    """
    Execute an API endpoint call.
    
    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        parameters: Query/path parameters
        body: Request body
        
    Returns:
        API response as dictionary
    """
    if not SALLA_API_TOKEN:
        return {
            "error": "SALLA_API_TOKEN not configured",
            "status": "error",
        }
    
    try:
        # Prepare URL
        url = f"{SALLA_BASE_URL}{endpoint}"
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {SALLA_API_TOKEN}",
            "Content-Type": "application/json",
        }
        
        # Make request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method.upper(),
                url=url,
                params=parameters,
                json=body,
                headers=headers,
            )
        
        return {
            "status": "success",
            "statusCode": response.status_code,
            "data": response.json() if response.text else None,
        }
    
    except httpx.HTTPError as e:
        return {
            "status": "error",
            "error": f"HTTP request failed: {str(e)}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Execution failed: {str(e)}",
        }


# Initialize MCP server
server = Server("salla-api-mcp")


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> Any:
    """Handle tool calls from MCP clients."""
    
    if name == "search":
        # Search endpoints
        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)
        results = search_endpoints(query, limit)
        return {
            "results": results,
            "count": len(results),
            "query": query,
        }
    
    elif name == "execute":
        # Execute endpoint
        endpoint = arguments.get("endpoint", "")
        method = arguments.get("method", "GET")
        parameters = arguments.get("parameters")
        body = arguments.get("body")
        
        if not endpoint:
            return {"error": "endpoint parameter is required", "status": "error"}
        
        result = await execute_endpoint(endpoint, method, parameters, body)
        return result
    
    else:
        return {"error": f"Unknown tool: {name}", "status": "error"}


@server.list_tools()
async def list_tools() -> list[models.Tool]:
    """List available tools."""
    return [
        models.Tool(
            name="search",
            description="Search available API endpoints in the OpenAPI specification. Returns matching endpoints with details about parameters, methods, and descriptions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find endpoints (searches path, method, summary, description, tags)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        models.Tool(
            name="execute",
            description="Execute an API endpoint call with optional parameters and request body. Requires SALLA_API_TOKEN to be configured.",
            inputSchema={
                "type": "object",
                "properties": {
                    "endpoint": {
                        "type": "string",
                        "description": "The API endpoint path (e.g., /products, /orders/{id})",
                    },
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                        "description": "HTTP method to use",
                        "default": "GET",
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Query or path parameters as key-value pairs",
                    },
                    "body": {
                        "type": "object",
                        "description": "Request body for POST/PUT/PATCH requests",
                    },
                },
                "required": ["endpoint"],
            },
        ),
    ]


@asynccontextmanager
async def lifespan(server: Server):
    """Initialize and cleanup resources."""
    # Startup
    load_openapi_spec()
    print(f"Loaded OpenAPI spec from {OPENAPI_SPEC_PATH}")
    print(f"Found {len(openapi_spec.get('paths', {}))} endpoints")
    
    yield
    
    # Cleanup (if needed)


async def main():
    """Run the MCP server."""
    # For stdio transport (standard MCP setup)
    async with lifespan(server):
        await server.run_stdio()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
