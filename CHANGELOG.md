# Ring MCP Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
