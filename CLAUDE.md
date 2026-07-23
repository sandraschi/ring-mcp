# ring-mcp Agent Context

FastMCP 3.4+ server for Ring Security Ecosystem (doorbells, cameras, alarms).

## Entry Points
- `ring_mcp/__init__.py` — stdio main entry, tool registration
- `ring_mcp/http_server.py` — FastAPI HTTP server on port 10729
- `run_server.py` — PyInstaller entry point
- `ring_mcp/server.py` — FastMCP tool definitions

## Key Files
- `.env.example` — Ring credentials template (copy to `.env`)
- `ring-mcp-backend.spec` — PyInstaller spec for Tauri build
- `native/` — Tauri 2.0 desktop shell (NSIS installer)
- `web_sota/` — Vite + React fleet UI on port 10728
- `docker-compose.yml` — Docker + monitoring stack
- `scripts/cua-smoke.py` — CUA-NSIS smoke test

## Commands
```powershell
just serve       # Start HTTP server on port 10729
just dev         # Start web_sota + backend
just test        # Run pytest suite
just lint        # ruff + biome
just fix         # ruff format + biome check --write
just build-native # PyInstaller -> Tauri -> NSIS
```

## Ports
- Frontend: 10728
- Backend API: 10729

## Standards
- FastMCP >=3.4.2,<4
- Ruff lint + format
- prefab-ui for Prefab cards
- Tauri 2.0 embedded backend (PyInstaller onefile)
