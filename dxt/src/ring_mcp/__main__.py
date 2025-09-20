"""
Ring MCP - Main entry point.

This module provides the main entry point for the Ring MCP server.
"""
import logging
import os
import sys
from pathlib import Path

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
    print("\n2FA verification code required.")
    print("Check your authenticator app or SMS for the code.")
    while True:
        code = input("Enter 2FA code: ").strip()
        if code:
            return code
        print("Error: 2FA code cannot be empty")

async def initialize_ring_client():
    """Initialize the Ring client with 2FA support if needed."""
    # Load environment variables from .env file if it exists
    from dotenv import load_dotenv
    load_dotenv()

    # Check for required environment variables
    required_vars = ["RING_USERNAME", "RING_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars and not os.getenv("RING_TOKEN"):
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nPlease set these variables in a .env file or in your environment.")
        print("See .env.example for an example configuration.")
        sys.exit(1)

    # Initialize the Ring client with 2FA support if needed
    if not os.getenv("RING_TOKEN"):
        from ring_mcp.core.ring_client_modern import RingClient

        print("Initializing Ring client...")
        client = RingClient()

        try:
            # Try to connect with 2FA support
            await client.connect(two_factor_callback=prompt_for_2fa_code)
            print("Successfully authenticated with Ring API")

            # Save the token for future use
            if client.token:
                print("\nAuthentication successful!")
                print("You can add the following to your .env file to avoid 2FA in the future:")
                print(f"RING_TOKEN={client.token}")

            return client

        except Exception as e:
            logger.error("Failed to initialize Ring client: %s", str(e))
            print(f"\nError: {str(e)}")
            print("Please check your credentials and try again.")
            sys.exit(1)

    return None

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

    print(f"\nStarting Ring MCP server on http://{host}:{port}")
    print("Press Ctrl+C to stop")
    print_port_info(port)

    try:
        # Run the server with both stdio and HTTP transports
        # FastMCP's app.run() handles its own event loop
        app.run(
            host=host,
            port=port,
            log_level=os.getenv("LOG_LEVEL", "info").lower()
        )
    except KeyboardInterrupt:
        print("\nShutting down Ring MCP server...")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or later is required")
        sys.exit(1)

    # Run the main function (now synchronous)
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
