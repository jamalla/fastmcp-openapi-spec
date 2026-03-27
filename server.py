#!/usr/bin/env python
"""
Entry point for Salla MCP Server.
This script initializes and runs the server using stdio transport.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from salla_mcp import create_server


async def main():
    """Main entry point."""
    try:
        # Create server with environment configuration
        server = create_server()

        # Initialize
        await server.initialize()

        # Run
        await server.run()

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
