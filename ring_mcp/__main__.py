"""
Ring MCP - Main entry point.

This module provides the main entry point for the Ring MCP server.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Import the server after setting up logging
from ring_mcp.server import create_app  # noqa: E402

def prompt_for_2fa_code() -> str:
    """Prompt the user to enter their 2FA code."""
    logging.info("\n2FA verification code required.")
    logging.info("Check your authenticator app or SMS for the code.")
    while True:
        code = input("Enter 2FA code: ").strip()
        if code:
            return code
        logging.error("Error: 2FA code cannot be empty")

async def initialize_ring_client():
    """Initialize the Ring client with lazy authentication."""
    # Load environment variables from .env file if it exists
    from dotenv import load_dotenv
    load_dotenv()

    # For MCP server mode, we initialize the client but don't authenticate yet
    # Authentication will happen lazily when tools are actually called
    from ring_mcp.core.ring_client_modern import RingClient

    logging.info("Initializing Ring client (lazy authentication)...")
    client = RingClient()

    # Check if we have credentials available
    has_credentials = (
        (os.getenv("RING_USERNAME") and os.getenv("RING_PASSWORD")) or
        os.getenv("RING_TOKEN")
    )

    if has_credentials:
        logging.info("Ring credentials found - authentication will happen on first API call")
    else:
        logging.info("No Ring credentials found - tools will require manual authentication")

    return client

def main():
    """Run the Ring MCP server."""
    # Run the async initialization first
    ring_client = asyncio.run(initialize_ring_client())

    # Create and run the FastMCP application
    app = create_app(ring_client) if ring_client else create_app()

    # Port management with graceful termination of previous instances
    from ring_mcp.core.port_manager import get_ring_mcp_port, print_port_info

    # Get host and port from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = get_ring_mcp_port()

    logging.info(f"\nStarting Ring MCP server on http://{host}:{port}")
    logging.info("Press Ctrl+C to stop")
    print_port_info(port)

    try:
        # Run the server with stdio transport for Claude Desktop
        # FastMCP 2.12 stdio mode - no parameters needed
        app.run()
    except KeyboardInterrupt:
        logging.info("\nShutting down Ring MCP server...")
    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if sys.version_info < (3, 7):
        logging.error("Error: Python 3.7 or later is required")
        sys.exit(1)

    # Run the main function (now synchronous)
    try:
        main()
    except KeyboardInterrupt:
        logging.info("\nShutting down...")
        sys.exit(0)
