# Ring MCP Server - DXT Extension

This directory contains the DXT (Deployment eXtension Toolkit) packaging configuration for the Ring MCP Server.

## 📦 What is DXT?

DXT is Anthropic's packaging system for MCP (Model Control Protocol) servers, allowing one-click installation in Claude Desktop.

## 🏗️ Quick Start

### Building the DXT Package

#### Option 1: Python Script (Recommended)
```bash
cd dxt
python dxt_build.py
```

#### Option 2: PowerShell Script (Windows)
```powershell
.\scripts\build-dxt.ps1
```

#### Option 3: Bash Script (Cross-platform)
```bash
./scripts/build-dxt.sh
```

### Installing in Claude Desktop

1. **Locate the built package**: `dist/ring-mcp-server.dxt`
2. **Drag and drop** the `.dxt` file into Claude Desktop
3. **Follow the configuration prompts** for Ring credentials
4. **Restart Claude Desktop** to complete installation

## 📁 Directory Structure

```
dxt/
├── manifest.json      # Runtime configuration
├── dxt.json          # Build configuration
├── requirements.txt   # Runtime dependencies
├── dxt_build.py      # Build script
├── src/              # Python source code
│   └── ring_mcp/     # Main package
└── README.md         # This file
```

## ⚙️ Configuration

### User Configuration Prompts

The extension will prompt for:

- **Ring Username** (required) - Your Ring account email
- **Ring Password** (required) - Your Ring account password
- **Ring API Token** (optional) - Pre-existing token to skip 2FA
- **Enable Monitoring** (optional) - Enable Prometheus metrics
- **Metrics Port** (optional) - Port for metrics server (default: 8001)

### Environment Variables

The extension supports these environment variables:

- `PYTHONPATH` - Set to include `src` and `lib` directories
- `PYTHONUNBUFFERED` - Set to `1` for better logging
- `RING_USERNAME` - Override username prompt
- `RING_PASSWORD` - Override password prompt (not recommended)
- `RING_TOKEN` - Override API token prompt

## 🛠️ Development

### Prerequisites

- Python 3.9+
- FastMCP 2.12.0+
- All dependencies in `requirements.txt`

### Building for Development

```bash
# Clean build
python dxt_build.py --clean

# Build without signing (faster for testing)
python dxt_build.py --no-sign

# Custom output directory
python dxt_build.py --output-dir ./build
```

### Testing the Extension

1. **Build the package**: `python dxt_build.py`
2. **Install in Claude Desktop**: Drag `dist/ring-mcp-server.dxt` to Claude Desktop
3. **Test basic functionality**:
   - List devices: `ring.get_devices`
   - Check health: `ring.health_check`
   - View available tools: `ring.list_available_tools`

### Debugging Extension Issues

If the extension fails to load:

1. **Check Claude Desktop logs**:
   - Windows: `%APPDATA%\Claude\logs\mcp-server-ring-mcp-server.log`
   - macOS: `~/Library/Logs/Claude/mcp-server-ring-mcp-server.log`

2. **Common issues**:
   - Missing dependencies in `lib/` directory
   - Incorrect PYTHONPATH configuration
   - FastMCP version incompatibility

3. **Manual configuration workaround** (if needed):
   ```json
   {
     "mcpServers": {
       "ring-mcp-manual": {
         "command": "python",
         "args": ["-m", "ring_mcp"],
         "cwd": "/path/to/extension/src",
         "env": {
           "PYTHONPATH": "/path/to/extension/src;/path/to/extension/lib",
           "PYTHONUNBUFFERED": "1"
         }
       }
     }
   }
   ```

## 📋 Available Tools

### Core Ring Tools
- `get_devices` - List all Ring devices
- `get_device_details` - Get device information
- `get_device_events` - Get device event history
- `get_live_stream_url` - Get camera live stream
- `set_arm_status` - Arm/disarm security system
- `trigger_chime` - Trigger doorbell chime
- `health_check` - System health check

### Composition Tools
- `list_connected_servers` - Show connected MCP servers
- `connect_server` - Connect to external MCP servers
- `disconnect_server` - Disconnect from servers
- `call_namespaced_tool` - Call tools from connected servers

### Monitoring Tools
- `get_system_status` - Overall system status
- `monitor_system_health` - Comprehensive health check
- `get_camera_status` - Camera system status
- `get_doorbell_status` - Doorbell system status
- `get_security_system_status` - Security system status

## 🔧 Troubleshooting

### Extension Won't Load
1. Check that `lib/` directory contains all dependencies
2. Verify FastMCP version >= 2.12.0
3. Check Python path configuration in manifest.json
4. Review Claude Desktop logs for specific errors

### Tools Not Working
1. Verify Ring API credentials are correct
2. Check device connectivity and permissions
3. Review Ring API rate limits
4. Test with `health_check` tool first

### Build Issues
1. Ensure all dependencies install correctly to `lib/`
2. Check that `src/` directory contains valid Python modules
3. Verify manifest.json has correct paths
4. Run `python -c "import ring_mcp"` to test imports

## 📊 Performance

- **Package Size**: ~5-10MB (with bundled dependencies)
- **Startup Time**: < 3 seconds
- **Memory Usage**: ~100MB base + ~50MB per active device
- **API Response Time**: < 500ms for most operations

## 🔐 Security

- All Ring API credentials stored securely by Claude Desktop
- No credentials stored in extension files
- HTTPS-only communication with Ring API
- No external network access without user approval

## 📝 Version History

### v2.12.0
- ✅ FastMCP 2.12.0 compatibility
- ✅ Asyncio double loop fix
- ✅ Proper dependency bundling
- ✅ Comprehensive tool set
- ✅ Production-ready packaging

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-tool`
3. **Test your changes**: `./scripts/build-dxt.sh --no-sign`
4. **Update documentation**: Update this README and manifest.json
5. **Submit a pull request**

## 📄 License

MIT License - see main repository for details.

---

**Built with ❤️ for the Ring MCP community**

For issues and questions, please visit: https://github.com/ring-mcp/ring-mcp
