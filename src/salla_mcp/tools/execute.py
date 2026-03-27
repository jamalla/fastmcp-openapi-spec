"""
Execute tool for calling API endpoints.
Allows agents to invoke API operations with authentication and error handling.
"""

from typing import Dict, Optional, Any
from ..services import APIClient
from ..utils import ExecutionError, ValidationError, get_logger

logger = get_logger(__name__)


class ExecuteTool:
    """Execute tool implementation."""

    def __init__(self, api_client: APIClient):
        """
        Initialize execute tool.

        Args:
            api_client: API client instance
        """
        self.client = api_client

    async def execute(
        self,
        endpoint: str,
        method: str = "GET",
        parameters: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute API endpoint call.

        Args:
            endpoint: API endpoint path (e.g., /products)
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            parameters: Query/path parameters
            body: Request body for POST/PUT/PATCH

        Returns:
            API response dictionary
        """
        try:
            # Validate inputs
            self._validate_inputs(endpoint, method)

            # Make API call
            result = await self.client.request(
                method, endpoint, parameters, body
            )

            return result

        except (ExecutionError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Execute failed: {str(e)}")
            raise ExecutionError(f"Execution failed: {str(e)}")

    def _validate_inputs(self, endpoint: str, method: str) -> None:
        """
        Validate tool inputs.

        Args:
            endpoint: Endpoint path
            method: HTTP method

        Raises:
            ValidationError: If inputs are invalid
        """
        if not endpoint or not isinstance(endpoint, str):
            raise ValidationError("Endpoint must be a non-empty string", "endpoint")

        if not endpoint.startswith("/"):
            raise ValidationError(
                "Endpoint must start with /", "endpoint"
            )

        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        if method.upper() not in valid_methods:
            raise ValidationError(
                f"Method must be one of: {', '.join(valid_methods)}",
                "method",
            )

    def get_tool_definition(self) -> Dict[str, Any]:
        """Get MCP tool definition for execute."""
        return {
            "name": "execute",
            "description": "Execute an API endpoint call with optional parameters and request body. Requires SALLA_API_TOKEN to be configured.",
            "inputSchema": {
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
        }
