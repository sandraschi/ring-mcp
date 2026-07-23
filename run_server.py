"""PyInstaller entry point — dual transport (HTTP on MCP_PORT, stdio otherwise)."""

import _strptime  # noqa: F401
import os
import sys

sys.path.insert(0, ".")

port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
if port:
    import uvicorn
    from ring_mcp.http_server import app
    uvicorn.run(app, host=os.environ.get("MCP_HOST", "127.0.0.1"), port=int(port))
else:
    from ring_mcp import main
    main()
