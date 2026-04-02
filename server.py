"""
Salla API MCP Server

Converts an OpenAPI specification into an MCP server with two tools:
  - search: discover API endpoints by keyword
  - execute: call any discovered endpoint with authentication

Usage:
  python server.py                    # stdio (default)
  python server.py streamable-http    # HTTP server
  python server.py sse                # Server-Sent Events
"""

import sys

from mcp.server.fastmcp import FastMCP

from src.config import HOST, PORT
from src.tools import execute, list_orders, sales_report, search, store_dashboard

mcp = FastMCP("salla-api", host=HOST, port=PORT)

mcp.tool()(search)
mcp.tool()(execute)
mcp.tool()(list_orders)
mcp.tool()(store_dashboard)
mcp.tool()(sales_report)

if __name__ == "__main__":
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    if transport not in ("stdio", "sse", "streamable-http"):
        print("Usage: python server.py [stdio|sse|streamable-http]")
        sys.exit(1)
    print(f"Starting MCP server ({transport}) ...")
    mcp.run(transport=transport)
