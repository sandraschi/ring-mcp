# Ring MCP 

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>


> 📖 **[Installation Guide](INSTALL.md)** — quick start, manual setup, and troubleshooting

**Universal Ring Security Ecosystem Control** - FastMCP 3.2+ server for comprehensive Ring device management including doorbells, security cameras, and alarm systems. Supports sampling, agentic workflows, and MCP prompts/skills.

[![Version](https://img.shields.io/badge/version-1.0.3-blue.svg)](https://github.com/sandraschi/ring-mcp/releases)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![FastMCP 3.2](https://img.shields.io/badge/FastMCP-3.2-orange.svg)](https://gofastmcp.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-green)](https://github.com/sandraschi/ring-mcp)

> **Latest Version: 1.0.3** - [View Changelog](CHANGELOG.md)

**Keywords**: `ring`, `security`, `cameras`, `doorbells`, `mcp`, `fastmcp`, `monitoring`, `automation`, `home-security`, `iot`, `smart-home`

##  Documentation

- **[ Complete Setup Guide](docs/RING_MCP_SETUP_GUIDE.md)** - Device onboarding, API keys, 2FA, discovery & iOS app integration
- **[ API Reference](docs/RING_MCP_API_REFERENCE.md)** - Complete API documentation
- **[ Quick Reference](docs/RING_MCP_QUICK_REFERENCE.md)** - Tool summaries and examples
- **[ Ring MCP Architecture](docs/RING_MCP_ARCHITECTURE.md)** - Advanced architecture & advantages
- **[ PRD](docs/PRD.md)** - Product requirements, FastMCP 3.2+, sampling, agentic workflows
- **[ Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md)** - System design details
- **[ Logging & Monitoring](docs/RING_MCP_LOGGING_MONITORING.md)** - Complete observability guide
- **[ Multi-Server Monitoring](docs/RING_MCP_MULTISERVER_MONITORING.md)** - Cross-server analytics
- **[ FastMCP troubleshooting](docs/TROUBLESHOOTING_FASTMCP_2.12.md)** - Production debugging guide

## Features

- **Unified API**: Control all your Ring devices through a single, consistent interface
- **Real-time Events**: Subscribe to device events in real-time with WebSocket support
- **Secure**: Encrypted communication and secure token storage with automatic refresh
- **Extensible**: Built on FastMCP for easy integration with other services
- **Scalable**: Designed to handle multiple clients and devices efficiently
- **Containerized**: Easy deployment with Docker and Docker Compose
- **Advanced Monitoring**: Complete observability with Grafana dashboards and Loki logging
- **Multi-Server Support**: Monitor multiple MCP servers in a unified dashboard
- **Production Logging**: Structured JSON logging with automatic rotation and correlation
- **High Availability**: Support for Redis caching and session management

## Quick Start

```powershell
git clone https://github.com/sandraschi/ring-mcp
cd ring-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:
### Prerequisites
- Python 3.10+ (3.11+ recommended for optimal performance)
- Ring account with 2FA enabled (recommended)
- Docker and Docker Compose (for containerized deployment)
####  Ring Account Setup
- **Ring App**: Download from [App Store](https://apps.apple.com/app/ring/id926252661) or [Google Play](https://play.google.com/store/apps/details?id=com.ringapp)
- **2FA Required**: Enable two-factor authentication in Ring app for security
- **Supported Devices**: Video Doorbell, Spotlight Cam, Floodlight Cam, Indoor Cam, Alarm systems

##  Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

###  Quick Start
Run immediately via `uvx`:
```bash
uvx ring-mcp
```

###  Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "ring-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/ring-mcp", "run", "ring-mcp"]
  }
}
```
#### Using MCPB Package (Claude Desktop Integration)  **RECOMMENDED**

The easiest way to use Ring MCP with Claude Desktop is through our MCPB (MCP Bundle) package:

1. **Build the MCPB package**:
   ```bash
   # Option 1: PowerShell script (recommended)
   .\scripts\build-mcpb-package.ps1

   # Option 2: Manual build
   mcpb pack . dist/ring-mcp.mcpb --no-sign
   ```

2. **Install in Claude Desktop**:
   - Locate the built package: `dist/ring-mcp.mcpb`
   - Drag and drop the `.mcpb` file into Claude Desktop
   - Configure your Ring credentials when prompted
   - **Restart Claude Desktop completely** (important for MCP server to initialize)

3. **Start using Ring tools**:
   ```
   ring.get_devices        # List all devices
   ring.health_check       # Check system status
   ring.get_live_stream_url --device_id <camera_id>
   ```

> **Note**: The MCP server now uses lazy authentication - it starts successfully without Ring credentials and only authenticates when tools are actually called. If you encounter authentication issues when using tools, check the Claude Desktop logs at `C:\Users\<username>\AppData\Roaming\Claude\logs\mcp-server-ring-security.log`

#### Using Docker (Recommended for Server Deployment)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ring-mcp.git
   cd ring-mcp
   ```

2. Copy the example environment file and configure it:
   ```bash
   cp .env.example .env
   # Edit .env with your Ring credentials
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Access the API:
   - API: http://127.0.0.1:10729
   - Swagger UI: http://127.0.0.1:10729/docs
   - Prometheus: http://localhost:9002
   - Grafana: http://localhost:9001 (admin/admin)

#### From Source

1. Clone the repository and set up a virtual environment:
   ```bash
   git clone https://github.com/yourusername/ring-mcp.git
   cd ring-mcp
   uv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e ".[dev]"  # For development
   # or
   uv pip install -e .  # For production
   ```

3. Configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your Ring credentials
   ```

4. Start the server:
   ```bash
   ring-mcp
   ```

### React UI (web_sota)

Ring MCP ships a **Vite + React** fleet UI under `web_sota/` that talks to the **real Ring API** (no mocks). Configure Ring credentials in the UI and control devices from the browser.

#### Quick start

1. **Start backend and frontend** (from repo root):
   ```powershell
   cd web_sota
   .\start.ps1
   ```
   This starts the REST API on port **10729** and the Vite dev server on **10728**.

2. **Open the app**: [http://localhost:10728](http://localhost:10728)

3. **Configure Ring**: Go to **Settings**, enter your Ring email and password, click **Save Ring credentials**. Use **Test connection** to verify the backend.

4. **Use devices**: Open **Status** to see your real Ring devices, arm/disarm alarms, and trigger doorbell chime.
5. **Live video**: Open **Doorbell & Camera**, select a device, and click **Start live view**. The app uses WebRTC (WebSocket signaling at `/api/v1/devices/{id}/stream/webrtc`) to show the camera stream in the browser.

#### UI features
- **Settings**: Ring account (email/password) and API URL (default `http://127.0.0.1:10729`). Test connection hits `/api/v1/health`.
- **Status**: Real device list from the API; Arm/Disarm and Chime actions.
- **Doorbell & Camera**: Live video in browser via WebRTC (Start live view / Stop); two-way audio placeholder (Hold to talk).
- **Dashboard**: Backend health and device count from the API.

#### CLI device check (no browser)

From repo root, with Ring account env vars or interactive prompts: **`just devices`** prints each device’s **online** and **battery** via `RingClient` (the Ring HTTP API process does not need to be running). For scripts or CI, set `RING_USERNAME` and `RING_PASSWORD` and use **`just devices-env`** (non-interactive).

## Configuration

Edit the `.env` file to customize the server behavior:

```env
# Required
RING_USERNAME=your_ring_email@example.com
RING_PASSWORD=your_ring_password

# Optional (with defaults)
HOST=0.0.0.0
PORT=10729
LOG_LEVEL=INFO
CACHE_TTL=300  # 5 minutes
RATE_LIMIT=10  # Requests per minute per client

# Redis (for distributed caching)
REDIS_URL=redis://redis:6379/0

# Monitoring
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
```

## API Examples

### List All Devices

```python
import asyncio
from ring_mcp import RingClient

async def list_devices():
    async with RingClient() as client:
        devices = await client.get_devices()
        for device in devices:
            print(f"{device['name']} ({device['device_type']}): {device.get('battery_life', 'N/A')}%")

asyncio.run(list_devices())
```

### Get Device Details

```python
import asyncio
from ring_mcp import RingClient

async def get_device_details(device_id: str):
    async with RingClient() as client:
        device = await client.get_device(device_id)
        print(f"Device: {device['name']}")
        print(f"Type: {device['device_type']}")
        print(f"Battery: {device.get('battery_life', 'N/A')}%")
        print(f"Status: {device.get('status')}")

asyncio.run(get_device_details("your_device_id_here"))
```

### Live video (WebRTC)

Ring devices use WebRTC for streaming (no RTSP URL). For in-browser video, open **web_sota** (e.g. `just dev`), go to **Doorbell & Camera**, select a device, and click **Start live view**. The REST API exposes WebSocket signaling at `GET /api/v1/devices/{device_id}/stream/webrtc` (offer/answer and ICE). Programmatic access would require a WebRTC client that connects to this WebSocket and displays the remote stream.

### Arm/Disarm Alarm

```python
import asyncio
from ring_mcp import RingClient

async def set_alarm_status(device_id: str, arm: bool):
    action = "arm" if arm else "disarm"
    print(f"Attempting to {action} alarm...")
    
    async with RingClient() as client:
        result = await client.set_arm_status(device_id, arm)
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")

# Arm the alarm
asyncio.run(set_alarm_status("your_alarm_id_here", True))

# Disarm the alarm
# asyncio.run(set_alarm_status("your_alarm_id_here", False))
```

## Docker Deployment

### Development

```bash
docker-compose up --build
```

### Production

1. Create a `docker-compose.override.yml` for production settings:
   ```yaml
   version: '3.8'
   services:
     ring-mcp:
       restart: always
       environment:
         - NODE_ENV=production
         - LOG_LEVEL=WARNING
       ports:
         - "80:8000"
   ```

2. Start the services:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
   ```

##  Complete Observability Stack

Ring MCP includes a **production-ready monitoring system** that provides complete visibility into your security system:

### ** Monitoring Features**
- **Real-time log streaming** with structured JSON logging
- **Performance metrics** for API calls and tool execution
- **Security event tracking** with device status monitoring
- **Multi-server support** for monitoring multiple MCP servers
- **Pictorial dashboards** showing camera feeds and device status
- **Alert integration** with email, Slack, and webhook support

### ** Quick Monitoring Setup**

1. **Start the complete monitoring stack**:
   ```bash
   cd monitoring
   docker-compose up -d
   ```

2. **Access the dashboards**:
   - **Grafana**: http://localhost:3000 (admin/admin)
   - **Loki**: http://localhost:3100 (log queries)
   - **Prometheus**: http://localhost:9090 (metrics)

3. **Available Dashboards**:
   - **Logs & Analysis**: Real-time log streaming and error tracking
   - **Performance & Metrics**: API performance and tool usage analytics
   - **Security Overview**: Device status and security event monitoring
   - **Multi-Server View**: Cross-server monitoring and correlation
   - **Security Camera**: Live camera feeds and motion detection

### ** Advanced Features**

#### **Claude Desktop Logs Integration**
- **Location**: `C:\Users\sandr\AppData\Roaming\Claude\logs`
- **Mixed logs**: Server + Client logs in same files
- **Timeline analysis**: Track "what moved" by date/time
- **Debug correlation**: Match server errors with client-side issues

#### **Multi-Server Monitoring**
- **Universal stack**: Works for all 20+ MCP servers
- **Cross-service events**: Motion detection  light activation
- **Pictorial information**: Camera feeds and visual alerts
- **Production ready**: Used across all MCP projects

### ** Complete Documentation**
- **[ Logging & Monitoring Guide](docs/RING_MCP_LOGGING_MONITORING.md)** - Complete observability setup
- **[ Multi-Server Analytics](docs/RING_MCP_MULTISERVER_MONITORING.md)** - Cross-server monitoring
- **[ FastMCP Troubleshooting](docs/TROUBLESHOOTING_FASTMCP_2.12.md)** - Production debugging (3.2+)

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, or suggest enhancements.


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes (`just sync`, `just test`, `just test-real`, `just test-real-prompt`, `just devices`, `just devices-env`, `just dev`, `just dev-http`, `just docker-up`, `just lint`, `just fix`, `just check-sec`, `just audit-deps`).
- **Security**: `just check-sec` (Bandit on `ring_mcp` + `tests`) and `just audit-deps` (pip-audit via uv).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [python-ring-doorbell](https://github.com/tchellomello/python-ring-doorbell) - For the Ring API client implementation
- [FastAPI](https://fastapi.tiangolo.com/) - For the web framework
- [FastMCP](https://github.com/yourusername/fastmcp) - For the MCP protocol implementation
- [Prometheus](https://prometheus.io/) and [Grafana](https://grafana.com/) - For monitoring

## Security Features

- **Authentication** - Secure Ring account integration
- **Rate Limiting** - Respectful API usage
- **Privacy Focus** - Local processing where possible
- **Emergency Ready** - Fail-safe operation modes

##  Austrian Integration

- **Vienna Emergency Services** - Local emergency contact integration
- **European Privacy** - GDPR compliant data handling
- **Time Zone Support** - Central European Time scheduling
- **Local Standards** - Austrian fire safety compliance

##  Development

Built with **FastMCP 3.2+**: sampling, agentic workflows, and MCP prompts/skills per [gofastmcp.com](https://gofastmcp.com/). Tool responses are conversational and support agentic use.

### Project Structure
```
ring-mcp/
 ring_mcp/
    __init__.py          # FastMCP stdio server
    core/                # Ring API client & exceptions
    tools/               # Modular tool categories
        security_system_tools.py
        doorbell_tools.py
        fire_safety_tools.py
        camera_tools.py
        monitoring_tools.py
        automation_tools.py
```

### Austrian Dev Standards
- **Safety First** - Security operations with validation
- **Comprehensive Documentation** - Detailed tool descriptions
- **Error Resilience** - Graceful degradation
- **Performance Optimized** - Efficient API usage

##  MCPB Packaging

Ring MCP includes full MCPB (MCP Bundle) support for professional Claude Desktop integration.

### Building MCPB Packages

#### Prerequisites
- Python 3.12+
- FastMCP 3.2+
- MCPB CLI (`npm install -g @anthropic-ai/mcpb`)
- Git repository (for version control)

#### Build Commands

```bash
# Option 1: PowerShell script (recommended)
.\scripts\build-mcpb-package.ps1

# Option 2: Manual build (requires config files in mcpb/)
mcpb pack . dist/ring-mcp.mcpb --no-sign

# Option 3: With signing (production)
mcpb pack . dist/ring-mcp.mcpb
```

#### Package Contents
- **Source code**: All Python modules properly structured
- **Dependencies**: All runtime dependencies bundled
- **Manifest**: Complete MCPB configuration from `mcpb/manifest.json`
- **Build config**: MCPB build settings from `mcpb/mcpb.json`
- **Prompt templates**: 6 comprehensive AI prompt templates in `mcpb/prompts/`
- **User configuration**: Interactive setup prompts
- **Security**: Optional cryptographic signing

##  Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

###  Quick Start
Run immediately via `uvx`:
```bash
uvx ring-mcp
```

###  Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "ring-mcp": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/ring-mcp", "run", "ring-mcp"]
  }
}
```
### MCPB Configuration

The MCPB package includes:

- **10+ Ring tools** - Complete device management
- **6 AI prompt templates** - Advanced AI interaction templates
- **Real-time monitoring** - Live device status
- **Secure authentication** - Ring API integration with lazy loading
- **User configuration** - Interactive setup prompts for credentials
- **Error handling** - Graceful failure recovery
- **Cross-platform** - Windows, macOS, and Linux support

#### AI Prompt Templates

The package includes 6 comprehensive prompt templates for advanced AI interactions:

1. **Security System Analysis** - Comprehensive security assessment and recommendations
2. **Device Troubleshooting** - Step-by-step device issue diagnosis and resolution
3. **Morning Security Check** - Daily security briefing and status updates
4. **Emergency Response** - Critical incident response protocol activation
5. **Camera Management** - Camera system optimization and maintenance
6. **System Monitoring** - Continuous health monitoring and performance tracking

All templates follow MCPB standards with structured JSON format, parameter validation, and example usage patterns.

### CI/CD Integration

MCPB packaging is fully integrated into GitHub Actions:
- Automatic MCPB package building on version tags
- Dependency validation and testing
- Multi-platform compatibility
- Artifact upload and release creation
- PyPI publication for Python packages

##  Usage Examples

### Morning Security Check
```python
# Quick system overview
status = get_security_system_status()
health = monitor_system_health()

# Check overnight activity
history = get_security_history(hours=12)
visitors = get_visitor_history(hours=12)
```

### Leaving Home Automation
```python
# Secure departure routine
arm_security_system("away")
create_security_automation(
    trigger_type="motion",
    response_actions=["start_recording", "send_alert"]
)
```

### Emergency Response
```python
# Immediate emergency activation
emergency = trigger_emergency_protocol()
# Automatically: arms system, starts recording, notifies contacts
```

##  Configuration

### Environment Variables
```bash
RING_USERNAME=your_email@example.com
RING_PASSWORD=your_password
RING_TOKEN=optional_existing_token
```

### Austrian Settings
```python
# Vienna-specific configuration
schedule_security_modes({
    "timezone": "Europe/Vienna",
    "work_schedule": "weekdays_8_to_18",
    "vacation_mode": False
})
```

##  Emergency Features

- **Instant Activation** - Emergency protocol in seconds
- **Multi-device Response** - Coordinated security activation
- **Contact Integration** - Automatic emergency notifications
- **Audit Logging** - Complete incident documentation
- **Fail-safe Design** - Works even with partial connectivity

##  Integration Ready

Designed for **Home Dashboard MCP** integration:
- Standardized event formats
- Real-time streaming APIs  
- Unified alert management
- Cross-device automation support

##  Privacy & Security

- **Local Processing** - Minimize cloud dependencies
- **Encrypted Storage** - Secure credential management
- **Access Logging** - Complete security audit trails
- **Rate Limiting** - Responsible API usage
- **Emergency Protocols** - Always-available safety features

##  License

MIT License - See LICENSE file for details.

---

**Ring MCP: Because your family's security deserves Austrian engineering precision! **
