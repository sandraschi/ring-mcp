"""
Ring MCP - Unified Security Ecosystem.

FastMCP 3.4+ implementation for Ring doorbell, burglar alarm, fire alarm, and security cameras.
Universal security control through Ring API with real-time monitoring and emergency automation.

The served tool surface is built by ring_mcp.server.create_app() so every stdio entry
point (python -m ring_mcp, ring-mcp script, Claude Desktop) exposes the same tools:
domain modules + help/status + list_devices + Prefab cards + ring_shutdown.
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .server import create_app

# Served FastMCP application (single surface for all stdio transports).
mcp = create_app()


def main():
    """Main entry point for Ring MCP server (stdio transport)."""
    logger.info("Starting Ring MCP server with stdio transport")
    # FastMCP.run() is synchronous and blocks until shutdown (do not wrap in asyncio.run).
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
