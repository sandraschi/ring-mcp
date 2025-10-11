#!/usr/bin/env python3
"""Test script to verify tool registration in Ring MCP server."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ring_mcp.server import create_app

async def test_server():
    try:
        print("Creating Ring MCP app...")
        app = create_app()
        print(f'[SUCCESS] Server created successfully - Type: {type(app)}')

        # Check if app has tools using get_tools
        try:
            tools = app.get_tools()
            tool_count = len(tools)
            print(f'[SUCCESS] App has {tool_count} registered tools')
            for tool in sorted(tools, key=lambda t: t.name)[:15]:  # Show first 15
                print(f'  - {tool.name}')
            if tool_count > 15:
                print(f'  ... and {tool_count - 15} more tools')
        except Exception as e:
            print(f'[ERROR] Failed to get tools: {e}')

        # Try to get registered tools via MCP protocol
        try:
            if hasattr(app, '_list_tools'):
                mcp_tools = await app._list_tools()
                print(f'[SUCCESS] MCP _list_tools() returned: {len(mcp_tools)} tools')
                for tool in mcp_tools[:10]:
                    tool_name = tool.get('name', 'unknown') if isinstance(tool, dict) else str(tool)
                    print(f'  - {tool_name}')
            else:
                print('[INFO] No _list_tools method available')
        except Exception as e:
            print(f'[ERROR] _list_tools() failed: {e}')

        print("\n[SUCCESS] Tool registration test completed!")

    except Exception as e:
        print(f'[ERROR] Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_server())
