# Troubleshooting — ring-mcp

## Auth / credentials

**`Authentication failed` / 401 everywhere**
→ `RING_USERNAME`/`RING_PASSWORD` missing, wrong, or Ring demands 2FA. Onboard via
Settings (OTP round-trip supported); env-only login cannot answer 2FA.
Verify: `check_authentication_status()` / `GET /api/v1/health`.

**Token expired mid-session**
→ The modern client refreshes automatically; a 401 storm means the refresh token is
dead — re-save credentials in Settings.

## Devices / data

**No devices listed**
→ Devices must be claimed to the same Ring account. Shared-invite accounts may see
nothing. `list_devices()` reads live (no stale cache excuse past TTL).

**Armed state `unknown`**
→ Deliberate: only explicit panel state counts. Online ≠ armed.

**No alarm panel for arm/disarm**
→ Auto-detection needs exactly one panel-shaped device. MQTT-bridged panels: pass
`device_id` explicitly and check `RING_MQTT_*`.

**Empty events**
→ `get_device_events` queries recent history; new/quiet devices legitimately return
`[]`. Burst polling trips Ring 429s — the client raises `RateLimitError`, back off.

## Video / audio

**No playable stream URL from tools**
→ By design (retired by Ring). Browser live view uses WebRTC signaling
(`WS /api/v1/devices/{id}/stream/webrtc`); tools return those endpoints.

**WebRTC never connects**
→ Browser must reach `:10729` (Tauri CSP covers it; LAN needs firewall). Check
`/api/v1/health` from the browser host, then keepalive traffic in Logger.

**Two-way audio / motion zones / footage listing**
→ Not exposed by the wrapper. Tools answer explicit-unsupported; use the Ring app.

## Chat / LLM

**Chat fails / no models**
→ Ollama must run on `RING_LLM_BASE_URL` with a pulled model. `GET /api/v1/llm/discover`
reports reachability; the startup probe logs it (`RING_MCP_LLM_GLOM=0` disables).

## Launcher / ports

**Port taken (10728/10729)**
→ A killed launcher often leaves `uvicorn` alive (it outlives the `uv` parent).
Find it: `Get-NetTCPConnection -LocalPort 10729 | Select OwningProcess`, verify the
command line is `ring_mcp.http_server`, `Stop-Process` it. Always launch the real
`uvicorn.exe` for probes so the PID you hold is the server.

**Health 404s but server is up**
→ You hit a stale pre-endpoint server, or the wrong port. `fleet-start.config.ps1`
owns the ports; HealthPath is `/api/v1/health` (not `/health`).

**`.venv` broken (`No pyvenv.cfg file`)**
→ Delete `.venv` and `uv sync --extra dev` (recreate, never hand-repair).

## Build / gates

**`bun run build` fails** → read the tsc errors; common: unused imports, nullable
narrowing on `setModel`, widened ChatTurn literals (use `as const`).
**`biome:ci` fails** → warnings fail `ci`; fix (buttons need `type`, no index keys,
no `any`, exhaustive deps) — do not weaken `biome.json`.
**Coverage gate** → `--cov-fail-under=30`; mock-first tests in `test_tool_wiring.py`
carry the tools surface.
