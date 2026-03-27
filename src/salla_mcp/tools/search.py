"""
Search tool for querying OpenAPI specification.
Allows agents to discover available endpoints.
"""

from typing import Dict, List, Any
from ..services import OpenAPILoader
from ..utils import SearchError, get_logger

logger = get_logger(__name__)


class SearchTool:
    """Search tool implementation."""

    def __init__(self, openapi_loader: OpenAPILoader):
        """
        Initialize search tool.

        Args:
            openapi_loader: OpenAPI loader instance
        """
        self.loader = openapi_loader

    def execute(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for endpoints matching query.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            Search results dictionary
        """
        try:
            if not query or not isinstance(query, str):
                raise SearchError("Query must be a non-empty string")

            if limit < 1 or limit > 100:
                raise SearchError("Limit must be between 1 and 100")

            results = self.loader.search_endpoints(query, limit)

            return {
                "results": results,
                "count": len(results),
                "query": query,
                "status": "success",
            }

        except SearchError:
            raise
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise SearchError(f"Search operation failed: {str(e)}")

    def get_tool_definition(self) -> Dict[str, Any]:
        """Get MCP tool definition for search."""
        return {
            "name": "search",
            "description": "Search available API endpoints in the OpenAPI specification. Returns matching endpoints with details about parameters, methods, and descriptions.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find endpoints (searches path, method, summary, description, tags)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10, max: 100)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": ["query"],
            },
        }
