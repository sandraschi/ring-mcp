# Onboarding — ring-mcp

## What this is for

ring-mcp connects Claude Desktop (via MCP stdio), a local web dashboard, and automation
scripts to your **Ring doorbells, security cameras, and alarm system**. It reads device
status, motion/doorbell events, and battery levels, arms/disarms alarm panels, captures
snapshots, and relays browser live video over WebRTC. It does **not** replace the Ring
app or Ring Protect subscription features: no cloud video history browsing, no two-way
talk, no motion-zone editing — those stay in Ring's own apps.

## Cost and accounts (money / CC)

| Question | Answer |
|----------|--------|
| Do I need an account? | Yes — a Ring account (ring.com) with your devices claimed in the Ring app |
| Free tier? | Ring account and live view are free; video history needs Ring Protect |
| Credit card required? | No for this repo; Ring Protect (optional) is paid via Ring |
| Ongoing cost? | Free unless you buy Ring Protect from Ring |
| Who bills? | Ring (Amazon) for Protect; nobody for ring-mcp itself |

Local LLM chat (Ollama default) is free and runs on your machine.

## Prerequisites outside this repo

- Ring account + Ring app with at least one doorbell, camera, or alarm claimed
- For alarm panels over MQTT: `ring-mqtt` running against your broker (optional)
- For Chat: Ollama on `http://127.0.0.1:11434` with a pulled model (e.g. `ollama pull llama3.2:3b`)
- Ports 10728 (UI) + 10729 (API) reachable on loopback/LAN

## First-timer setup steps

1. Clone + deps (Windows PowerShell):
   ```powershell
   git clone https://github.com/sandraschi/ring-mcp
   cd ring-mcp
   .\start.bat
   ```
   This installs uv-managed Python deps and starts the API (`:10729`) + UI (`:10728`).
2. Open `http://127.0.0.1:10728` → **Settings**. Enter your Ring email + password,
   Save, then **Test connection**. If Ring asks for a 2FA code, submit it in the
   second step (Settings supports the OTP round-trip).
3. Dashboard should show your devices (or an honest empty state). The big red
   **Complete onboarding** cue disappears once credentials verify.
4. Optional: start Ollama, pull a model, then use **Chat**.
5. Optional (Claude Desktop): point your MCP config at `uv run python -m ring_mcp`
   (stdio) — same 29 tools as the dashboard's backend.

## Pitfalls

- **2FA required, no callback in MCP mode**: password-only login fails when Ring demands
  verification. Always onboard through Settings (OTP supported), not env vars alone.
- **No devices listed**: devices must be claimed to the SAME Ring account; shared-user
  invites with limited scope may show nothing.
- **Armed state `unknown`**: the tools report armed only from explicit panel state —
  online does NOT mean armed. This is deliberate, not a bug.
- **Live view needs the browser**: MCP tools return WebRTC signaling endpoints, never
  playable URLs (Ring retired direct streams).
- **Alarm panels need device ids**: auto-detection works with exactly one visible panel;
  MQTT-bridged panels need their id passed explicitly.
- **Port taken**: `fleet-start.config.ps1` owns 10728/10729; a stale `uvicorn` from a
  killed launcher still holds the port — stop it before restarting.

## Sanity check

- `GET http://127.0.0.1:10729/api/v1/health` returns `"success": true` with
  `"authentication_valid": true` and your device count.
- Settings shows a green connection badge; the Dashboard red cue is gone.
- MCP probe: `list_devices()` returns your devices (not an error payload).

## Declared doubles

- Until credentials verify, the Dashboard shows **MOCK**-badged sample cards (actors
  Joe Mocky / Sandra Mockinger, dashed rose borders, `mock-data-banner`). They clear
  automatically once health reports configured — there is no keep-mocks toggle.
- `tests/` run fully mocked by default (no credentials needed); `test-real*` and
  `test_integration_real.py` skip without `RING_USERNAME`/`RING_PASSWORD`.
- Settings LLM provider falls back to a local `llama3.2:3b` entry when no backend
  provider answers (clearly a fallback, replaced by live data on success).
