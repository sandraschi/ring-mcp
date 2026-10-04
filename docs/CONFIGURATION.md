# Configuration — ring-mcp

Single source of truth for every knob. `start.ps1` / `fleet-start.config.ps1` own ports;
everything else is env vars (see also `.env.example` — never commit `.env`).

## Ports (fleet registry `mcp-central-docs/operations/WEBAPP_PORTS.md`)

| Service | Port | Source |
|---------|------|--------|
| Webapp frontend (Vite) | 10728 | `fleet-start.config.ps1` FrontendPort |
| Backend REST (FastAPI) | 10729 | `fleet-start.config.ps1` BackendPort, `PORT` |
| MCP stdio | — | stdin/stdout (`python -m ring_mcp`) |
| Prometheus metrics | 8001 | `METRICS_PORT` (server `__main__` path) |

`HOST` defaults to `0.0.0.0` (LAN/Tailscale intentional; CORS still restricts origins).

## Environment variables

| Variable | Required | Default | Used by |
|----------|----------|---------|---------|
| `RING_USERNAME` | Yes (or token) | — | Ring auth (client, Settings save) |
| `RING_PASSWORD` | Yes (or token) | — | Ring auth (supports OTP second submit) |
| `RING_TOKEN` | No | — | OAuth token alternative |
| `HOST` / `PORT` | No | `0.0.0.0` / `10729` | HTTP server bind |
| `LOG_LEVEL` | No | `INFO` | stdlib + structlog levels |
| `RING_HTTP_API_ORIGIN` | No | `http://127.0.0.1:10729` | Docs/tooling base URL |
| `RING_LLM_BASE_URL` | No | `http://127.0.0.1:11434` | Local LLM endpoint |
| `RING_LLM_MODEL` | No | first listed | Default chat model |
| `RING_LLM_API_KEY` | No | — | LLM bearer (if endpoint needs one) |
| `RING_LLM_SYSTEM` | No | built-in | Chat system prompt |
| `RING_MCP_LLM_GLOM` | No | `1` | Startup LLM probe (`0` disables) |
| `RING_MQTT_ENABLED` | No | — | Alarm panels via ring-mqtt |
| `RING_MQTT_URL` / `RING_MQTT_USERNAME` / `RING_MQTT_PASSWORD` | No | `mqtt://127.0.0.1:1883` | Broker |
| `RING_MQTT_TOPIC_PREFIX` / `RING_MQTT_CLIENT_ID` | No | `ring` / `ring-mcp-bridge` | Topics/identity |
| `MCP_BRIDGE_URLS` | No | — | Extra MCP servers to proxy (composition) |
| `MCP_PORT` / `MCP_HOST` | No | — | `run_server.py`: set port → HTTP, else stdio |
| `METRICS_PORT` | No | `8001` | Prometheus exporter |
| `FLEET_REPOS_ROOT` | No | `D:\Dev\repos` | Launcher engine lookup |

## Files that configure behavior

- `fleet-start.config.ps1` — ports, health path, uvicorn target, frontend kind.
- `web_sota/vite.config.ts` — dev proxy (`/api`, `/docs`, `/openapi.json`, `/redoc` → `:10729`).
- `native/tauri.conf.json` — window, bundle, CSP (allows `:10728` + `:10729`).
- `pyproject.toml` — deps, ruff, pytest (`--cov-fail-under=30`).
- `pytest.ini` — asyncio auto mode, markers, coverage gate.

## Health contract (what "configured" means)

`GET /api/v1/health` → `health_status.authentication_valid: true` +
`devices_accessible > 0`. The Dashboard onboarding cue and all MOCK content clear
exactly when this holds. No separate flag file, no toggle.
