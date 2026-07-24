# ring-mcp Agent Context

FastMCP 3.4+ server for Ring doorbells, security cameras, and alarm systems.

## Quick Ref

```powershell
uv run ruff check src/
uv run pytest tests/ -q
uv run python -m ring_mcp    # MCP stdio
.\start.ps1                  # full stack
```

## Ports

| Port | Service |
|------|---------|
| 10728 | Webapp frontend (Vite) |
| 10729 | Webapp backend (FastAPI + MCP HTTP) |

## Key Files

| File | Purpose |
|------|---------|
| `ring_mcp/__init__.py` | FastMCP server entry, tool registration |
| `ring_mcp/http_server.py` | FastAPI HTTP server |
| `ring_mcp/tools/` | Individual tool modules |
| `web_sota/src/` | React SPA dashboard |
| `native/` | Tauri 2.0 desktop wrapper |
