"""
Salla MCP Server
A production-level Model Context Protocol server for the Salla API.
Implements the two-tool Code Mode pattern for optimal agent efficiency.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "MCP server for Salla API with Code Mode optimization"

from .config import Settings
from .main import create_server

__all__ = ["Settings", "create_server", "__version__"]
