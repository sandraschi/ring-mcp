# Ring MCP – Product Requirements (PRD)

**Version**: 1.0  
**Last updated**: March 2026  
**Framework**: FastMCP 3.2+

---

## 1. Overview

Ring MCP is an MCP server that exposes Ring security ecosystem (doorbells, cameras, alarms) as tools and resources for AI assistants and agents. It targets **FastMCP 3.2+** and supports **sampling**, **agentic workflows**, and **prompts/skills** as per the FastMCP 3.2+ release line.

## 2. Goals

- **Single control plane**: One MCP server for all Ring devices (doorbells, cameras, alarms, sensors).
- **Claude Desktop & agents**: Stdio transport for Claude Desktop; tool responses suitable for sampling and agentic use.
- **Web UI**: React webapp (web_sota) using the real Ring REST API (no mocks): configure credentials, list devices, arm/disarm, trigger chime. **In-browser live video** via WebRTC: Doorbell & Camera page connects to backend WebSocket for signaling and displays the Ring stream in a `<video>` element.
- **Observability**: Logging, metrics (Prometheus), and optional Grafana/Loki.

## 3. FastMCP 3.2+ alignment

| Area | Requirement |
|------|-------------|
| **Dependency** | `fastmcp>=3.2.0` in pyproject.toml. No 2.x-only usage. |
| **MCP server** | Stdio entrypoint via FastMCP 3.2+ `run(transport="stdio")`. Tool/resource registration and context follow 3.2+. |
| **HTTP/REST** | Custom REST API for the browser UI is a separate FastAPI app (`ring_mcp.http_server`). Optional: mount MCP HTTP app via `mcp.http_app()` for 3.2+ HTTP transport. |
| **Tool responses** | Conversational, structured responses compatible with **sampling** and **agentic workflows** (SEP-1577). Docstrings and return shapes document this. |
| **Prompts / skills** | MCPB prompt templates (e.g. in `mcpb/prompts/`) and tool descriptions align with FastMCP 3.2+ prompts and skill-style guidance for AI use. |
| **Docs** | README, CHANGELOG, ARCHITECTURE, and this PRD state FastMCP 3.2+; no 2.10/2.12/2.14 as target. |

## 4. User flows

### 4.1 Claude Desktop (stdio)

- User adds ring-mcp to `claude_desktop_config.json` (or installs MCPB package).
- Server starts without requiring Ring credentials (lazy auth).
- On first tool call that needs Ring API, server uses env or stored credentials.
- Tools return structured, conversational output for use in sampling and multi-step agentic flows.

### 4.2 Webapp (web_sota)

- User runs `web_sota\start.ps1`: REST API on 10729, Vite on 10728.
- User opens Settings, enters Ring email/password, saves credentials. Optional: change API URL and test connection.
- User opens Status: sees real devices from API; can Arm/Disarm alarms and trigger doorbell chime.
- User opens Doorbell & Camera: selects a doorbell/camera, clicks "Start live view"; browser establishes WebRTC via WebSocket signaling (`/api/v1/devices/{id}/stream/webrtc`); live video appears in the page. "Stop" ends the stream.
- Dashboard shows backend health and device count from `/api/v1/health`.

## 5. Non-goals (out of scope)

- Native Ring mobile app replacement.
- Multi-tenant or hosted SaaS; local / single-user deployment.

## 6. References

- [FastMCP 3.2+ (jlowin/fastmcp)](https://github.com/jlowin/fastmcp) / [gofastmcp.com](https://gofastmcp.com/)
- [MCP Central – FASTMCP_3.1_ALIGNMENT.md](https://github.com/sandraschi/mcp-central-docs/blob/main/docs/operations/FASTMCP_3.1_ALIGNMENT.md)
- Ring API: [python-ring-doorbell](https://github.com/tchellomello/python-ring-doorbell)
