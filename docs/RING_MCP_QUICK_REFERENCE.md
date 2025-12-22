# 🏠 Ring MCP Server - Quick Reference

**Version**: 2.13.0 | **Updated**: December 21, 2025

---

## 🚀 Quick Start

```bash
# Set credentials
export RING_USERNAME=your_email@example.com
export RING_PASSWORD=your_password

# Start server
python -m ring_mcp.server
```

---

## 📋 Core Tools by Category

### 📹 Camera Tools
- `get_camera_status` - Get all camera status
- `stream_all_cameras` - Start live streams

### 🔔 Doorbell Tools
- `get_doorbell_live_stream` - Live video stream
- `answer_doorbell_call` - Two-way audio
- `get_visitor_history` - Event history
- `configure_motion_detection` - Motion settings

### 🔒 Security Tools
- `get_security_system_status` - System status
- `arm_security_system` - Arm system
- `disarm_security_system` - Disarm system
- `get_security_history` - Event history

### 🚨 Fire Safety Tools
- `get_fire_alarm_status` - Alarm status
- `test_fire_safety_system` - System test

### 📊 Monitoring Tools
- `monitor_system_health` - Health check
- `get_real_time_activity` - Live activity

### 🤖 Automation Tools
- `create_security_automation` - Custom rules
- `trigger_emergency_protocol` - Emergency mode
- `schedule_security_modes` - Time scheduling

---

## 🔑 Authentication

```bash
# Method 1: Username/Password
export RING_USERNAME=email@example.com
export RING_PASSWORD=password

# Method 2: OAuth Token
export RING_TOKEN=oauth_token_here
```

---

## 📡 HTTP API

```bash
# Health check
curl http://localhost:8000/health

# List tools
curl http://localhost:8000/tools

# Call tool
curl -X POST http://localhost:8000/tools/get_camera_status \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## ⚠️ Security Modes

| Mode | Description |
|------|-------------|
| `home` | Perimeter protection only |
| `away` | Full perimeter + interior |
| `disarmed` | All protection disabled |

---

## 📊 Common Commands

```python
# System status
status = await get_security_system_status()

# Arm system
await arm_security_system("away")

# Check health
health = await monitor_system_health()

# Get activity
activity = await get_real_time_activity()

# Emergency mode
await trigger_emergency_protocol()
```

---

## 🔧 Environment Variables

| Variable | Default | Required |
|----------|---------|----------|
| `RING_USERNAME` | - | Yes* |
| `RING_PASSWORD` | - | Yes* |
| `RING_TOKEN` | - | Yes* |
| `HOST` | `0.0.0.0` | No |
| `PORT` | `8123` | No |

*One of: USERNAME/PASSWORD or TOKEN

---

## 🐛 Troubleshooting

### Authentication Issues
```bash
# Verify credentials in Ring app
# Check 2FA settings
# Use correct email format
```

### Device Not Found
```bash
# Check device connectivity
# Verify Ring app shows device online
# Ensure proper account permissions
```

### Rate Limiting
```bash
# Implement backoff logic
# Monitor API call frequency
# Use caching for repeated requests
```

---

## 📈 Metrics

| Metric | Description |
|--------|-------------|
| `ring_device_online` | Device connectivity |
| `ring_device_battery` | Battery levels |
| `ring_security_armed` | System armed status |
| `ring_api_calls_total` | API call count |
| `ring_tool_calls_total` | Tool usage count |

---

## 🚨 Emergency Commands

```python
# Activate emergency protocol
emergency = await trigger_emergency_protocol()
print(f"Emergency activated: {emergency['success']}")

# Arm all security systems
await arm_security_system("away", force_arm=True)

# Get all camera streams
streams = await stream_all_cameras()
```

---

*Quick Reference - For detailed documentation see [API_REFERENCE.md](RING_MCP_API_REFERENCE.md)*
