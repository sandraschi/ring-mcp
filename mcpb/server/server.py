'''MCP server entry point for Ring-MCP.

This is the MCPB-compliant server wrapper that launches the Ring-MCP server.
'''

import sys
from pathlib import Path

# Add parent directory to path to import main server
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Import and run main server
try:
    from server import main
except ImportError:
    # Fallback
    try:
        from ring_mcp.server import main
    except ImportError:
        # Another fallback
        import ring_mcp
        main = ring_mcp.main

if __name__ == '__main__':
    main()

