"""
Ring MCP - Unified Security Ecosystem

FastMCP 3.1 implementation for Ring doorbell, burglar alarm, fire alarm, and security cameras.
Universal security control through Ring API with real-time monitoring and emergency automation.
Supports sampling, agentic workflows, and MCP prompts/skills per FastMCP 3.1.
"""

import logging

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server with stdio transport
mcp = FastMCP("Ring Security")

# Import and register tool modules
from .tools import (
    security_system_tools,
    doorbell_tools, 
    fire_safety_tools,
    camera_tools,
    monitoring_tools,
    automation_tools
)

# Register all tool groups with the server
security_system_tools.register_tools(mcp)
doorbell_tools.register_tools(mcp)
fire_safety_tools.register_tools(mcp)
camera_tools.register_tools(mcp)
monitoring_tools.register_tools(mcp)
automation_tools.register_tools(mcp)

logger.info("Ring MCP server initialized with all security tool modules")

def main():
    """Main entry point for Ring MCP server."""
    logger.info("Starting Ring MCP server with stdio transport")
    # FastMCP.run() is synchronous and blocks until shutdown (do not wrap in asyncio.run).
    mcp.run(transport="stdio", show_banner=False)

if __name__ == "__main__":
    main()
