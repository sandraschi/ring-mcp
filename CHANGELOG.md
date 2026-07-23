
## [Unreleased] — 2026-06-14

### Added
- Tauri 2.0 native wrapper with `bundle.resources` + `std::process::Command`
- PyInstaller frozen backend embedded in NSIS installer
- CUA-NSIS smoke test (`scripts/cua-smoke.py`, `scripts/cua-nsis-config.json`)
- `just cua-nsis-test` recipe
- Tauri CORS: `tauri://localhost` origins for WebView API access
- `GET /api/v1/diagnostics` endpoint for CUA verification
# Ring MCP Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed
- **Next.js `webapp/`**: Removed the legacy Next.js UI; the only supported browser UI is **`web_sota`** (`just dev`, `web_sota/start.ps1`). Dropped `just dev-webapp`.

### Added
- **CLI device status**: `scripts/ring_device_status.py` with `just devices` (env or prompt for Ring creds) and `just devices-env` (`--no-prompt`, requires `RING_USERNAME` / `RING_PASSWORD`). Prints **online** and **battery** per device via `RingClient` (no HTTP API process required).
- **FastMCP 3.2+**: Upgraded dependency to `fastmcp>=3.2.0` (resolved to 3.2.x). Explicit `fastapi` dependency for `http_server` and composition. Server and tool docstrings aligned to 3.2+.
- **web_sota real API**: Fleet UI now uses the live REST API (no mocks). Settings: Ring credentials (email/password) and API URL; Test connection calls `/api/v1/health`. Status: real device list from `/api/v1/devices` and `/api/v1/status`; Arm/Disarm and Chime actions. Dashboard: backend health and device count from API.
- **In-browser live video (WebRTC)**: Ring uses WebRTC (not RTSP). Backend WebSocket at `GET /api/v1/devices/{id}/stream/webrtc` relays SDP offer/answer and ICE between browser and Ring. Doorbell & Camera page: "Start live view" opens WebSocket, creates RTCPeerConnection, sends offer, applies Ring answer and ICE, and displays stream in a `<video>` element. "Stop" closes stream and WebSocket. `RingClient`: `webrtc_start`, `webrtc_ice`, `webrtc_close`; `get_live_stream_url` now raises and directs callers to WebRTC.
- **API client**: `web_sota/src/lib/api.ts` with `configureAuth`, `getHealth`, `getDevices`, `getStatus`, `setArmStatus`, `triggerChime`, `getWebRtcWsUrl`. Base URL from localStorage or `VITE_API_URL` (default `http://127.0.0.1:10729`).
- **Start script**: `web_sota/start.ps1` now runs `ring_mcp.http_server:app` (REST API) on port 10729; frontend on 10728. CORS updated for 10728 and 10706.

### Changed
- **Fleet ports**: Default Ring HTTP REST API port is **10729** (matches `web_sota/start.ps1`); conflict fallback range **10720–10800**. Default `RING_HTTP_API_ORIGIN` for tooling/docs is `http://127.0.0.1:10729`. Docker Compose uses `ring-mcp-http` entrypoint, port **10729**, and health check on `/api/v1/health`.
- **Docs**: README, architecture, PRD, and code comments now state FastMCP 3.2+ and WebRTC in-browser video; removed 2.10/2.12/2.13 version references. README describes **web_sota**, Doorbell & Camera live view, and real API flow.
- **PRD**: `docs/PRD.md` updated: in-scope WebRTC live video in **web_sota**; non-goals no longer exclude in-browser streaming.

### Fixed
- **web_sota** was mock-only and did not show or control real Ring devices; backend started wrong process (MCP server instead of REST API). Fixed by starting `http_server:app` and wiring the UI to REST endpoints with Ring auth in Settings.

---

## [1.0.3] - 2026-01-17

### 🛠️ **Test Framework Fixes**

#### **Fixed Broken Test Suite**
- **Test Framework**: Fixed broken test framework that was using non-existent `Client.connect()` method
- **FastMCP Testing**: Updated tests to follow proper FastMCP 2.13 testing patterns
- **Mock Setup**: Improved mock client setup and test fixtures
- **Error Handling**: Enhanced error handling tests for authentication and device not found scenarios
- **Test Coverage**: All 10 tests now pass successfully

#### **Technical Improvements**
- **Import Optimization**: Cleaned up test imports and removed unused dependencies
- **Test Structure**: Reorganized test fixtures and assertions for better maintainability
- **Documentation**: Updated test documentation to reflect current testing approach

---

## [1.0.2] - 2025-12-21

### 🔥 **SOTA Upgrade - FastMCP 2.13.0 & Modern Standards**

#### **Framework Modernization**
- **FastMCP 2.13.0**: Upgraded from 2.12.0 to latest MCP specification
- **Python 3.10+ Baseline**: Modern requirements replacing 3.9+ with enhanced security
- **MCPB 0.2 Manifest**: Complete modernization to Claude Desktop optimized packaging
- **Dependencies Update**: All dependencies upgraded to latest stable versions

#### **Code Quality & Standards**
- **Ruff Linting**: Added comprehensive Ruff configuration for code quality
- **Type Safety**: Enhanced mypy configuration with stricter type checking
- **Black Formatting**: Updated target version to Python 3.10
- **Import Optimization**: Cleaner dependency management with version constraints

#### **Security & Performance**
- **Enhanced WebSocket Support**: Added websockets>=11.0.0 for real-time events
- **Modern Async Utilities**: Added anyio>=4.5.0 for better async compatibility
- **Security Dependencies**: Updated cryptography and JWT handling libraries
- **Performance Optimization**: Improved caching and connection pooling

#### **Documentation & Packaging**
- **MCPB Package**: Updated to manifest v0.2 with comprehensive tool definitions
- **README Updates**: Modern badges, version references, and installation guides
- **Configuration Schema**: Detailed user configuration with validation
- **Production Standards**: Enhanced deployment and monitoring documentation

## [1.0.1] - 2025-10-10

### Fixed
- **Critical Dependency Fixes**: Added missing dependencies to requirements.txt:
  - `python-json-logger>=2.0.0` for JSON logging support
  - `aiocache>=0.12.0` for async caching functionality
  - `asyncio-throttle>=1.0.0` for rate limiting
- **Package Name Correction**: Fixed `python-ring-doorbell` to correct package name `ring-doorbell>=0.8.0`
- **Claude Desktop Configuration**: Added proper `cwd` and `PYTHONPATH` settings for MCP server startup
- **Ring API Compatibility**: Updated authentication code to work with ring-doorbell v0.9.13 API changes:
  - Replaced deprecated `Auth.new_auth_for_user()` with `Auth.async_fetch_token()`
  - Updated `Auth` constructor calls to match new signature
  - Fixed token handling to work with dict-based tokens
  - Updated token updater callbacks to match new API
- **Lazy Authentication**: Changed server initialization to use lazy authentication instead of eager authentication during startup
- **MCP Server Stability**: ✅ Server now starts successfully without Ring credentials, authenticating only when tools are called
- **Import Error Resolution**: Resolved multiple `ModuleNotFoundError` exceptions on server startup

### Technical Details
- Updated requirements.txt with missing logging dependency
- Corrected Ring doorbell package name from `python-ring-doorbell` to `ring-doorbell`
- Enhanced Claude Desktop MCP configuration with working directory and Python path settings
- Verified successful module imports and server initialization

## [1.0.0] - 2025-10-09

### Added
- **Complete Ring Security Ecosystem**: Full integration with Ring doorbells, cameras, security systems, and fire safety devices
- **FastMCP 2.12 Support**: Latest MCP protocol implementation for Claude Desktop compatibility
- **Real-time Device Monitoring**: Live status updates and event streaming
- **Comprehensive Tool Suite**: 20+ specialized tools for device management
- **Advanced Monitoring Stack**: Grafana dashboards, Loki logging, and Prometheus metrics
- **DXT Extension Packaging**: One-click installation for Claude Desktop
- **Containerized Deployment**: Docker and Docker Compose support
- **Multi-Server Monitoring**: Cross-server analytics and correlation
- **Austrian Integration**: Vienna emergency services and GDPR compliance
- **Production Logging**: Structured JSON logging with correlation IDs
- **Security Features**: Encrypted communication and secure token management

### Features
- **Unified API**: Single interface for all Ring device types
- **WebSocket Support**: Real-time event subscriptions
- **Rate Limiting**: Respectful API usage with configurable limits
- **Caching Layer**: Redis support for distributed caching
- **Emergency Protocols**: Instant activation and fail-safe operation
- **Privacy Focus**: Local processing with minimal cloud dependencies

### Documentation
- **Complete API Reference**: Detailed tool documentation
- **Architecture Guides**: System design and integration patterns
- **Monitoring Setup**: Complete observability configuration
- **Troubleshooting Guide**: FastMCP 2.12 debugging and production deployment
- **Quick Reference**: Tool summaries and usage examples

### Infrastructure
- **Docker Deployment**: Production-ready containerization
- **Monitoring Stack**: Grafana, Loki, and Prometheus integration
- **CI/CD Pipeline**: Automated building and testing
- **Multi-platform Support**: Windows, macOS, and Linux compatibility

---

**Legend:**
- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** in case of vulnerabilities

