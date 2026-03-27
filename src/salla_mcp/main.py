"""
Main MCP server implementation.
Integrates all components into a working MCP server.
"""

from typing import Any, Dict
import mcp.server.models as models
from mcp.server import Server
from .config import Settings
from .services import OpenAPILoader, APIClient
from .tools import SearchTool, ExecuteTool
from .utils import setup_logging, get_logger

logger = get_logger(__name__)


class SallaMCPServer:
    """Salla API MCP Server."""

    def __init__(self, settings: Settings):
        """
        Initialize the MCP server.

        Args:
            settings: Server configuration
        """
        self.settings = settings
        self.server = Server("salla-api-mcp")

        # Initialize components
        self.openapi_loader = OpenAPILoader()
        self.api_client = APIClient(settings)
        self.search_tool = SearchTool(self.openapi_loader)
        self.execute_tool = ExecuteTool(self.api_client)

        # Register handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP tool handlers."""

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Any:
            """Handle tool calls."""
            logger.info(f"Tool called: {name}", extra={"extra_fields": {"args": arguments}})

            if name == "search":
                result = self.search_tool.execute(
                    query=arguments.get("query", ""),
                    limit=arguments.get("limit", 10),
                )
                return result

            elif name == "execute":
                result = await self.execute_tool.execute(
                    endpoint=arguments.get("endpoint", ""),
                    method=arguments.get("method", "GET"),
                    parameters=arguments.get("parameters"),
                    body=arguments.get("body"),
                )
                return result

            else:
                return {"error": f"Unknown tool: {name}", "status": "error"}

        @self.server.list_tools()
        async def list_tools() -> list[models.Tool]:
            """List available tools."""
            return [
                models.Tool(**self.search_tool.get_tool_definition()),
                models.Tool(**self.execute_tool.get_tool_definition()),
            ]

    async def initialize(self) -> None:
        """Initialize server (load OpenAPI spec, validate config)."""
        logger.info("Initializing Salla MCP Server")

        # Validate configuration
        self.settings.validate_required_fields()

        # Load OpenAPI spec
        self.openapi_loader.load_from_file(self.settings.openapi_spec_path)

        logger.info("Server initialized successfully")

    async def run(self) -> None:
        """Run the MCP server (stdio transport)."""
        logger.info("Starting Salla MCP Server")
        await self.server.run_stdio()

    async def shutdown(self) -> None:
        """Shutdown the server gracefully."""
        logger.info("Shutting down Salla MCP Server")


def create_server(settings: Settings = None) -> SallaMCPServer:
    """
    Create and configure the MCP server.

    Args:
        settings: Server settings (uses environment if not provided)

    Returns:
        Configured server instance
    """
    if settings is None:
        settings = Settings()

    # Setup logging
    setup_logging(
        "salla_mcp",
        level=settings.log_level,
        format_type=settings.log_format,
    )

    return SallaMCPServer(settings)
