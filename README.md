# Ring MCP 🚨

**Universal Ring Security Ecosystem Control** - FastMCP 2.12 server for comprehensive Ring device management including doorbells, security cameras, and alarm systems.

## 📚 Documentation

- **[📖 API Reference](docs/RING_MCP_API_REFERENCE.md)** - Complete API documentation
- **[🚀 Quick Reference](docs/RING_MCP_QUICK_REFERENCE.md)** - Tool summaries and examples
- **[🏗️ Ring MCP Architecture](docs/RING_MCP_ARCHITECTURE.md)** - Advanced architecture & advantages
- **[🏗️ Technical Architecture](docs/TECHNICAL_ARCHITECTURE.md)** - System design details

## Features

- **Unified API**: Control all your Ring devices through a single, consistent interface
- **Real-time Events**: Subscribe to device events in real-time with WebSocket support
- **Secure**: Encrypted communication and secure token storage with automatic refresh
- **Extensible**: Built on FastMCP for easy integration with other services
- **Scalable**: Designed to handle multiple clients and devices efficiently
- **Containerized**: Easy deployment with Docker and Docker Compose
- **Monitoring**: Built-in support for Prometheus metrics and Grafana dashboards
- **High Availability**: Support for Redis caching and session management

## Quick Start

### Prerequisites

- Python 3.10+
- Ring account with 2FA enabled (recommended)
- Docker and Docker Compose (for containerized deployment)

### Installation

#### Using Docker (Recommended)

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
   - API: http://localhost:8123
   - Swagger UI: http://localhost:8123/docs
   - Prometheus: http://localhost:9002
   - Grafana: http://localhost:9001 (admin/admin)

#### From Source

1. Clone the repository and set up a virtual environment:
   ```bash
   git clone https://github.com/yourusername/ring-mcp.git
   cd ring-mcp
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -e ".[dev]"  # For development
   # or
   pip install -e .  # For production
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

## Configuration

Edit the `.env` file to customize the server behavior:

```env
# Required
RING_USERNAME=your_ring_email@example.com
RING_PASSWORD=your_ring_password

# Optional (with defaults)
HOST=0.0.0.0
PORT=8123
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
        print(f"Battery: {device.get('battery_life', 'N/A')}%"n        print(f"Status: {device.get('status')}")

asyncio.run(get_device_details("your_device_id_here"))
```

### Stream Camera Feed

```python
import asyncio
import webbrowser
from ring_mcp import RingClient

async def stream_camera(device_id: str):
    async with RingClient() as client:
        stream_info = await client.get_live_stream_url(device_id)
        print(f"Opening stream: {stream_info['url']}")
        webbrowser.open(stream_info['url'])

asyncio.run(stream_camera("your_camera_id_here"))
```

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

## Monitoring

The application exposes Prometheus metrics at `/metrics`. A sample Grafana dashboard is included in the `monitoring/` directory.

### Setting Up Monitoring

1. Start the monitoring stack:
   ```bash
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

2. Access the dashboards:
   - Grafana: http://localhost:9001 (admin/admin)
   - Prometheus: http://localhost:9002

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, or suggest enhancements.

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

## 🏠 Austrian Integration

- **Vienna Emergency Services** - Local emergency contact integration
- **European Privacy** - GDPR compliant data handling
- **Time Zone Support** - Central European Time scheduling
- **Local Standards** - Austrian fire safety compliance

## 🛠️ Development

Built with FastMCP 2.12 for maximum compatibility and performance.

### Project Structure
```
ring-mcp/
├── ring_mcp/
│   ├── __init__.py          # FastMCP stdio server
│   ├── core/                # Ring API client & exceptions
│   └── tools/               # Modular tool categories
│       ├── security_system_tools.py
│       ├── doorbell_tools.py
│       ├── fire_safety_tools.py
│       ├── camera_tools.py
│       ├── monitoring_tools.py
│       └── automation_tools.py
```

### Austrian Dev Standards
- **Safety First** - Security operations with validation
- **Comprehensive Documentation** - Detailed tool descriptions
- **Error Resilience** - Graceful degradation
- **Performance Optimized** - Efficient API usage

## 📊 Usage Examples

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

## 🔧 Configuration

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

## 🚨 Emergency Features

- **Instant Activation** - Emergency protocol in seconds
- **Multi-device Response** - Coordinated security activation
- **Contact Integration** - Automatic emergency notifications
- **Audit Logging** - Complete incident documentation
- **Fail-safe Design** - Works even with partial connectivity

## 📱 Integration Ready

Designed for **Home Dashboard MCP** integration:
- Standardized event formats
- Real-time streaming APIs  
- Unified alert management
- Cross-device automation support

## 🛡️ Privacy & Security

- **Local Processing** - Minimize cloud dependencies
- **Encrypted Storage** - Secure credential management
- **Access Logging** - Complete security audit trails
- **Rate Limiting** - Responsible API usage
- **Emergency Protocols** - Always-available safety features

## 📄 License

MIT License - See LICENSE file for details.

---

**Ring MCP: Because your family's security deserves Austrian engineering precision! 🇦🇹🔐**
