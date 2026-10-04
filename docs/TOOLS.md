# Tools — ring-mcp

Served surface: **29 tools + 2 prompts + 4 resources** (`create_app()` — stdio entries,
composition path, and the wiring tests all share it). Every tool returns
`{success, message?, ...}` (Prefab cards: `{content, structured_content}`) and carries
`output_schema` with `required: ["success"]` (or the honest discriminator noted below).

## Security (alarm panel via device id; auto-detected when exactly one panel is visible)

| Tool | Purpose | Notes |
|------|---------|-------|
| `get_security_system_status()` | Mode, devices, alerts | Mode is `unknown` unless a panel reports state |
| `arm_security_system(mode, bypass_sensors?, delay_minutes?, device_id?)` | Real panel arm | Delays/bypass follow panel config |
| `disarm_security_system(force_disarm?, disarm_code?, device_id?)` | Real panel disarm | Recent-activity warnings unless forced |
| `get_security_history(hours?, event_types?, include_video?)` | Real per-device events | `include_video` attaches recording status (no footage listing exists) |

## Doorbells

| Tool | Purpose | Notes |
|------|---------|-------|
| `get_doorbell_status()` | Inventory + online/battery/firmware | — |
| `get_doorbell_live_stream(doorbell_id?, quality?, duration_seconds?)` | WebRTC handoff | Direct URLs retired; returns signaling endpoints |
| `answer_doorbell_call(...)` | — | Explicit unsupported (no two-way audio primitive) |
| `get_visitor_history(hours?, include_snapshots?, motion_only?)` | Real events + patterns | Snapshots via `GET /api/v1/snapshot/{id}` |
| `configure_motion_detection(...)` | — | Explicit unsupported (wrapper exposes no motion API) |

## Cameras / Fire / Monitoring / Automation

| Tool | Purpose | Notes |
|------|---------|-------|
| `get_camera_status()` | Inventory + recent events | — |
| `stream_all_cameras()` | Per-camera readiness | Failures are honest per-camera WebRTC pointers |
| `get_fire_alarm_status()` | Smoke/fire devices, battery warnings | Matches type smoke/fire |
| `test_fire_safety_system()` | pass/warn/fail from live state | — |
| `monitor_system_health()` | 0–100 score + recommendations | — |
| `get_real_time_activity()` | Cross-device event feed | — |
| `create_security_automation(...)` | Validated rule draft (accepts `ctx`) | Conceptual store; validation is real |
| `trigger_emergency_protocol()` | Arms online panels, incident id (**DESTRUCTIVE**, accepts `ctx`, reports progress) | Confirm first |
| `schedule_security_modes(...)` | Validated schedule draft (accepts `ctx`) | Conceptual store |

## System / Help

| Tool | Purpose |
|------|---------|
| `get_system_status()` | Auth + devices + connectivity (discriminator: `system_status`) |
| `check_authentication_status()` | Real connect + device-read proof |
| `check_device_connectivity(device_id?)` | Latency + score (discriminator: `devices_tested`) |
| `get_service_health()` | Component scores, alerts (discriminator: `health_status`) |
| `list_devices(device_type?)` | MCP mirror of `GET /api/v1/devices` |
| `show_devices_card()` / `show_health_card()` | Prefab cards (discriminator: `content`) |
| `ring_shutdown()` | Graceful shutdown (**DESTRUCTIVE**) |
| `list_available_tools(category?)` / `get_tool_help(tool_name)` / `search_tools(query)` | 29-entry catalog (single source for all three) |

## Prompts / Resources

Prompts: `ring-security-check` (daily review), `ring-incident-triage`.
Resources: `ring://devices`, `ring://health`, `skill://ring-mcp/SKILL.md` (+ manifest).

## Composition (peer proxy)

`list_connected_servers`, `connect_server(namespace, server_url, api_key?)`,
`disconnect_server(namespace)`, `call_namespaced_tool(tool_name, arguments?)` —
short-lived 3.4 clients per call, routing table probed at connect, dict returns
(no exceptions across the boundary).

## REST (served, contract)

Health `GET /api/v1/health` · Status `GET /api/v1/status` · Devices
`GET /api/v1/devices{,/{id},/{id}/events}` · Recent `GET /api/v1/events/recent` ·
WebRTC `WS /api/v1/devices/{id}/stream/webrtc` + `POST /api/v1/webrtc/{offer,candidate,keepalive/{id},close/{id}}` ·
Snapshot `GET /api/v1/snapshot/{id}` · Arm `POST /api/v1/devices/{id}/arm` · Chime
`POST /api/v1/devices/{id}/chime` · Intercom `POST .../intercom/{start,stop}` (501,
honest) · Auth `POST /api/v1/auth/configure` · LLM `GET /api/v1/llm/{models,discover,providers,onboarding}`,
`POST /api/v1/llm/chat` · Skills `GET /api/skills` · Capabilities `GET /api/capabilities` ·
System `GET /api/v1/system/info` · Diagnostics `GET /api/v1/diagnostics` · Shutdown
`POST /api/shutdown` · Docs `/docs`, `/redoc`, `/openapi.json`.
