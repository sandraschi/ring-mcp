"""
Basic test for Ring MCP server functionality.

This is a simplified test to verify the server can start and register tools properly.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def test_server():
    """Test that the server can be created and has tools registered."""
    try:
        from ring_mcp.server import create_app

        print("Creating Ring MCP server...")
        app = create_app()

        print("Server created successfully!")
        print(f"Server type: {type(app)}")

        # Check if tools are registered
        if hasattr(app, "_tools"):
            tool_count = len(app._tools)
            print(f"Tools registered: {tool_count}")

            # List first few tools
            tool_names = sorted(list(app._tools.keys()))[:10]
            for name in tool_names:
                print(f"  - {name}")

            if tool_count > 10:
                print(f"  ... and {tool_count - 10} more tools")

            return tool_count > 0
        else:
            print("No tools found on server")
            return False

    except Exception as e:
        print(f"Error testing server: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_server())
    if success:
        print("\n✅ Server test PASSED")
        sys.exit(0)
    else:
        print("\n❌ Server test FAILED")
        sys.exit(1)
