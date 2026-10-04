---
name: ring-mcp
description: Ring doorbells, cameras, and alarms via MCP - device inventory, live status, arm/disarm, events, automations. Use when the user asks about Ring security, cameras, doorbells, or alarm panels.
---

# Ring MCP Skill

FastMCP 3.4 server (29 tools) + FastAPI REST backend for Ring doorbells, security
cameras, and alarm panels. Transports: stdio (`python -m ring_mcp`), HTTP REST
(`:10729`), Tauri desktop shell.

## Agent vs human routing

- **Agent (this skill):** use MCP tools for reads and safe actions. Prefer
  `get_security_system_status()` first - it shows mode, devices, and alerts in one call.
- **Human in browser:** the `web_sota` dashboard (`:10728`) covers status, live view
  (WebRTC), alarms, chat, and logs. Doorbell live view ONLY works in the browser -
  MCP tools cannot perform the WebRTC SDP exchange.
- **Destructive actions** (`arm/disarm_security_system`, `trigger_emergency_protocol`,
  `ring_shutdown`) need explicit user confirmation first. Never arm/disarm speculatively.

## Tool catalog (served surface - these names are exact)

Security: `get_security_system_status`, `arm_security_system(mode, bypass_sensors?, delay_minutes?, device_id?)`,
`disarm_security_system(force_disarm?, disarm_code?, device_id?)`,
`get_security_history(hours?, event_types?, include_video?)`.
Doorbells: `get_doorbell_status`, `get_doorbell_live_stream` (returns WebRTC handoff, not a URL),
`answer_doorbell_call` (explicit unsupported), `get_visitor_history(hours?, include_snapshots?, motion_only?)`,
`configure_motion_detection` (explicit unsupported - use the Ring app).
Cameras: `get_camera_status`, `stream_all_cameras` (per-camera readiness, WebRTC handoff).
Fire: `get_fire_alarm_status`, `test_fire_safety_system`.
Monitoring: `monitor_system_health`, `get_real_time_activity`.
Automation: `create_security_automation`, `trigger_emergency_protocol` (DESTRUCTIVE),
`schedule_security_modes`.
System: `get_system_status`, `check_authentication_status`, `check_device_connectivity`,
`get_service_health`, `list_devices(device_type?)`, `show_devices_card`, `show_health_card`,
`ring_shutdown`.
Help: `list_available_tools`, `get_tool_help`, `search_tools`.
Prompts: `ring-security-check`, `ring-incident-triage`. Resources: `ring://devices`, `ring://health`.

## Workflows

Morning check:
`get_security_system_status()` -> `monitor_system_health()` -> report mode, offline
devices, low batteries, recent activity. Done.

Incident triage ("what happened last night"):
`get_security_history(hours=12)` + `get_visitor_history(hours=12)` -> correlate by
timestamp/device -> `get_doorbell_status()` + `get_camera_status()` for current state.
Call `trigger_emergency_protocol()` ONLY for genuine ongoing emergencies.

Arm/disarm safely:
`list_devices()` (find the panel id; auto-detected when exactly one panel is visible)
-> `arm_security_system(mode="away")` / `disarm_security_system()`. If the tool reports
no visible panel, ask for the panel id (MQTT-bridged panels) instead of guessing.
After any test arm, `disarm_security_system()` to restore state.

Visitor review:
`get_visitor_history(hours=24, motion_only=True)` for motion; snapshot stills live at
`GET /api/v1/snapshot/{device_id}` (REST); live video is browser-only via
`WS /api/v1/devices/{id}/stream/webrtc`.

Automation setup:
`create_security_automation(trigger_type="motion", trigger_conditions={...},
response_actions=[...], automation_name="...")` then `schedule_security_modes(...)`.
Validate `success` - the tools return `{"success": false, "error": ...}` on bad config.

## REST equivalents (when driving the webapp or scripts)

Health `GET /api/v1/health` (launcher probe) - Status `GET /api/v1/status` - Devices
`GET /api/v1/devices` - Events `GET /api/v1/devices/{id}/events`, recent across devices
`GET /api/v1/events/recent` - Arm `POST /api/v1/devices/{id}/arm` - Chime
`POST /api/v1/devices/{id}/chime` - LLM `GET /api/v1/llm/models|discover|providers|onboarding`,
`POST /api/v1/llm/chat` - Skills `GET /api/skills` - Diagnostics `GET /api/v1/diagnostics`,
`GET /api/v1/system/info` - Shutdown `POST /api/shutdown` - Docs `/docs`, `/redoc`.

## Troubleshooting

- `Authentication failed` / 401: `RING_USERNAME`/`RING_PASSWORD` missing or Ring wants a
  2FA code (no callback in MCP mode -> configure via Settings, which supports the OTP
  second submit). Check `check_authentication_status()`.
- No devices: account has none shared, or cache is stale (`list_devices()` reads live).
- WebRTC never connects: browser must reach the backend (`:10729`, Tauri CSP covers it);
  check `/api/v1/health` from the browser host, then keepalive traffic in Logger.
- Alarm panel missing from MCP: panels live behind `ring-mqtt` - pass its device id
  explicitly or enable the bridge (`RING_MQTT_*`).
- `get_live_stream_url`-style direct URLs, two-way audio, motion-zone writes, and video
  footage listings do not exist in the wrapper - the tools say so explicitly; use the
  Ring app or the documented WebRTC/REST paths above.

## Honest limits (do not work around these)

- Armed state is reported `unknown` unless a panel exposes it. Online does NOT mean armed.
- The legacy hardcoded-mock client (`core/ring_client.py`) was deleted; every tool now
  reads the real API or returns an explicit unsupported error.
- Chat answers through the local LLM proxy (`RING_LLM_BASE_URL`, default Ollama :11434);
  the model must be pulled before Chat works.

## Configuration

Env: `RING_USERNAME`, `RING_PASSWORD`, `RING_TOKEN`, `HOST` (0.0.0.0 intentional),
`PORT` (10729), `RING_LLM_BASE_URL`, `RING_LLM_MODEL`, `RING_MQTT_*`, `MCP_BRIDGE_URLS`.
Ports: frontend 10728, backend 10729. Entry points: `ring_mcp/__init__.py` + `__main__.py`
(stdio, same surface), `run_server.py` (dual transport), `http_server.py` (REST).
