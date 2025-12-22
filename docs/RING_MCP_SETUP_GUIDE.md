# 🔐 Ring MCP Complete Setup Guide

**Comprehensive guide for Ring device onboarding, API key setup, 2FA configuration, device discovery, and iOS app integration**

**Last Updated**: December 21, 2025
**Version**: 1.0.2
**Framework**: FastMCP 2.13.0

---

## 📋 Table of Contents

1. [Ring Account Setup](#ring-account-setup)
2. [Device Onboarding](#device-onboarding)
3. [2FA Security Configuration](#2fa-security-configuration)
4. [API Key & Authentication](#api-key--authentication)
5. [Device Discovery Process](#device-discovery-process)
6. [iOS App Cooperation](#ios-app-cooperation)
7. [MCP Server Configuration](#mcp-server-configuration)
8. [Testing & Validation](#testing--validation)
9. [Troubleshooting](#troubleshooting)

---

## 🔑 Ring Account Setup

### Step 1: Create Ring Account

**Option A: iOS App (Recommended)**
1. Download **Ring App** from [App Store](https://apps.apple.com/app/ring/id926252661)
2. Open app and tap **"Create Account"**
3. Enter your email address and create password
4. Verify email with confirmation code
5. Complete account setup with personal information

**Option B: Android App**
1. Download **Ring App** from [Google Play](https://play.google.com/store/apps/details?id=com.ringapp)
2. Follow same process as iOS

**Option C: Web Browser**
1. Go to [Ring.com](https://ring.com)
2. Click **"Sign Up"** in top right
3. Complete registration process
4. Download mobile app for device setup

### Step 2: Account Verification

**Email Verification Required**
- Check your email for Ring verification
- Click verification link within 24 hours
- Account remains limited until verified

**Phone Number (Recommended)**
- Add phone number in app settings
- Used for additional security and notifications
- Required for some advanced features

---

## 🏠 Device Onboarding

### Supported Ring Devices

| Device Type | Setup Method | Power Requirements | Wi-Fi Required |
|-------------|--------------|-------------------|----------------|
| **Video Doorbell** | Wired/Wireless | Battery or Wired | Yes |
| **Spotlight Cam** | Wired/Wireless | Battery or Wired | Yes |
| **Floodlight Cam** | Wired/Wireless | Battery or Wired | Yes |
| **Indoor Cam** | Indoor only | USB Power | Yes |
| **Ring Alarm** | Base Station + Sensors | Battery + AC | Wi-Fi for base |

### Video Doorbell Setup

**Physical Installation**
1. **Power Requirements**:
   - **Wired**: Requires existing doorbell wiring (16-24V AC)
   - **Battery**: Uses rechargeable battery pack (included)

2. **Mounting**:
   - Position 4-5 feet above ground
   - Ensure clear view of entry area
   - Test motion detection angle

3. **Wiring (Wired Only)**:
   ```
   Existing Doorbell Wire → Ring Doorbell Terminal
   Transformer (16-24V) → Doorbell Wire → Ring Terminal
   ```
   - **Safety Warning**: Turn off power at breaker before wiring
   - **Professional Help**: Consider electrician for wired installation

**App Setup Process**
1. Open Ring app on phone
2. Tap **"+"** icon → **"Set up a device"**
3. Select **"Doorbells"** → Choose your model
4. Scan QR code on device or enter setup code
5. Follow voice prompts for Wi-Fi connection
6. Test doorbell and motion detection
7. Set up motion zones and alerts

### Security Camera Setup

**Spotlight Cam Installation**
1. **Power Options**:
   - **Wired**: Connect to existing outdoor outlet
   - **Battery**: Insert battery pack (Solar panel optional)

2. **Placement Guidelines**:
   - Mount 7-10 feet above ground
   - Point downward at 15-30 degree angle
   - Ensure 30+ feet of clear line-of-sight
   - Avoid pointing at busy streets or neighbors

3. **App Configuration**:
   - Follow same QR code setup as doorbell
   - Configure motion detection sensitivity
   - Set up spotlight activation (motion/sound)
   - Enable/disable night vision

### Ring Alarm Setup

**Base Station Installation**
1. **Location**: Central location in home
2. **Power**: Plugin to wall outlet
3. **Wi-Fi**: Must be on 2.4GHz network
4. **Ethernet**: Optional wired connection

**Sensor Installation**
- **Contact Sensor**: Door/window frames
- **Motion Sensor**: Hallways and main rooms
- **Range Extender**: Large homes or Wi-Fi dead zones
- **Keypad**: Easy arm/disarm access

**Professional Monitoring (Optional)**
- Ring offers professional monitoring service
- 24/7 monitoring with emergency dispatch
- Additional monthly fee applies

---

## 🔐 2FA Security Configuration

### Why 2FA is Critical

**Ring Security Importance**
- Controls access to your home security system
- Manages cameras with live video access
- Stores historical video footage
- Controls alarm system arm/disarm

**API Access Requirements**
- Ring API requires 2FA-enabled accounts
- MCP server cannot authenticate without 2FA
- Enhanced security for programmatic access

### Enabling 2FA

**Step 1: Access Security Settings**
1. Open Ring app
2. Tap menu (☰) → **"Settings"**
3. Tap **"Account"** → **"Security"**
4. Tap **"Two-Step Verification"**

**Step 2: Choose Verification Method**

**Option A: Authenticator App (Recommended)**
1. Install **Google Authenticator** or **Authy**
2. Tap **"Authenticator App"** in Ring app
3. Scan QR code with authenticator app
4. Enter 6-digit code to verify
5. Save backup codes securely

**Option B: SMS Verification**
1. Tap **"Text Message (SMS)"**
2. Enter phone number
3. Receive verification code via SMS
4. Enter code to complete setup

**Step 3: Recovery Setup**
- **Backup Codes**: Save printed codes in secure location
- **Recovery Email**: Optional secondary email for recovery
- **Trusted Devices**: Mark current device as trusted

### 2FA Best Practices

**Security Recommendations**
- Use authenticator app over SMS when possible
- Never share 2FA codes or backup codes
- Regularly rotate backup codes
- Enable biometric unlock on mobile app
- Use strong, unique passwords

**Account Recovery Planning**
- Store backup codes in secure password manager
- Keep recovery email up-to-date
- Have multiple trusted devices
- Document recovery process for family members

---

## 🔑 API Key & Authentication

### Ring API Access Setup

**Step 1: Verify Account Eligibility**
- Must have active Ring account
- 2FA must be enabled and working
- At least one Ring device registered
- Account in good standing

**Step 2: Prepare Credentials**
```bash
# Required environment variables
export RING_USERNAME="your-email@example.com"
export RING_PASSWORD="your-ring-password"
```

**Important**: Password is your Ring account password, not 2FA code.

**Step 3: Initial Authentication**
```python
# The MCP server handles authentication automatically
# First run will prompt for 2FA code
python -m ring_mcp

# Enter 2FA code when prompted
# Server saves refresh token for future use
```

### Authentication Flow Details

**OAuth 2.0 Implementation**
```
1. Username/Password Authentication
2. 2FA Challenge (if enabled)
3. Access Token + Refresh Token Issued
4. Automatic Token Refresh (server handles)
5. Secure Token Storage (encrypted)
```

**Token Management**
- **Access Token**: Valid 30 days, used for API calls
- **Refresh Token**: Valid 365 days, used to get new access tokens
- **Automatic Refresh**: Server handles token renewal transparently
- **Secure Storage**: Tokens encrypted and stored locally

### Troubleshooting Authentication

**"2FA Required" Error**
```
Error: Two-factor authentication is required for this account
```
**Solution**: Enable 2FA in Ring app before using MCP server

**"Invalid Credentials" Error**
```
Error: Authentication failed
```
**Solutions**:
1. Verify username/password are correct
2. Check if account is locked due to failed attempts
3. Reset password if necessary
4. Ensure account is in good standing

**"Token Expired" Error**
```
Error: Refresh token has expired
```
**Solution**: Re-run authentication process to get new tokens

---

## 🔍 Device Discovery Process

### How Ring MCP Discovers Devices

**Automatic Discovery Process**
1. **Authentication**: Server authenticates with Ring API
2. **Account Query**: Fetches all devices associated with account
3. **Device Enumeration**: Gets detailed information for each device
4. **Capability Assessment**: Determines device features and supported operations
5. **Status Check**: Verifies device connectivity and health
6. **Metadata Collection**: Gathers location, firmware, and configuration data

**Discovery Triggers**
- **Server Startup**: Automatic discovery on first run
- **Manual Refresh**: `ring.refresh_devices()` tool call
- **Device Addition**: New devices appear after account sync
- **Network Changes**: Re-discovery after connectivity issues

### Device Information Collected

**Basic Device Info**
```json
{
  "id": "device-unique-id",
  "name": "Front Door",
  "type": "doorbell",
  "model": "Ring Video Doorbell 4",
  "location": "Front Door"
}
```

**Connectivity Status**
```json
{
  "online": true,
  "wifi_strength": 85,
  "battery_level": 92,
  "firmware_version": "4.2.1",
  "last_connected": "2025-12-21T10:30:00Z"
}
```

**Capabilities**
```json
{
  "has_camera": true,
  "has_motion": true,
  "has_audio": true,
  "supports_live_view": true,
  "supports_snapshot": true,
  "has_siren": false,
  "has_light": false
}
```

### Device Categories

**Video Doorbells**
- Ring Video Doorbell (1-5)
- Ring Video Doorbell Pro
- Ring Video Doorbell Elite
- Ring Peephole Cam

**Security Cameras**
- Ring Spotlight Cam (Wired/Wire-Free/Pro)
- Ring Floodlight Cam (Wired/Wire-Free/Pro)
- Ring Indoor Cam
- Ring Stick Up Cam (Wired/Battery/Solar)

**Alarm System**
- Ring Alarm Base Station
- Contact Sensors
- Motion Sensors
- Range Extenders
- Keypads

**Smart Lighting**
- Ring Smart Lighting (Pathlight, Steplight)
- Ring Floodlight (with camera integration)

### Discovery Troubleshooting

**No Devices Found**
- Verify account has devices added
- Check device online status in Ring app
- Ensure proper account permissions
- Try manual device refresh

**Partial Discovery**
- Some devices offline but discoverable
- Network connectivity issues
- Device firmware outdated
- Account sharing permissions

**Discovery Timeout**
- Network connectivity problems
- Ring API service issues
- Large number of devices (rate limiting)
- Authentication token issues

---

## 📱 iOS App Cooperation

### Ring App Integration Features

**Device Management**
- **Central Hub**: All Ring devices managed from single app
- **Live View**: Real-time video streaming
- **Event History**: Access to motion and doorbell events
- **Device Settings**: Configure motion sensitivity, alerts, lighting

**MCP Server Cooperation**
- **Shared Account**: MCP uses same Ring account credentials
- **Data Synchronization**: Events and device status sync between app and MCP
- **Concurrent Access**: Both app and MCP can access devices simultaneously
- **Notification Integration**: App notifications work alongside MCP alerts

### iOS App Setup for MCP Integration

**Step 1: Enable Advanced Features**
1. Open Ring app on iOS
2. Go to **Device Settings** → **Device Health**
3. Enable **"Advanced Notifications"**
4. Enable **"Motion Verification"** for cameras
5. Enable **"Person Alerts"** for AI-powered detection

**Step 2: Configure Device Sharing (Optional)**
1. In Ring app: **Menu** → **Shared Users**
2. Add family members with appropriate permissions
3. MCP inherits same sharing permissions
4. Configure notification preferences per user

**Step 3: Optimize for Automation**
1. **Motion Settings**: Configure zones and sensitivity
2. **Alert Schedule**: Set quiet hours and active times
3. **Geofencing**: Enable location-based automation
4. **Integration Settings**: Enable IFTTT and other platforms

### App vs MCP Feature Comparison

| Feature | Ring App | MCP Server | Notes |
|---------|----------|------------|-------|
| **Live Video** | ✅ Full UI | ✅ API Access | App has richer interface |
| **Motion Alerts** | ✅ Push notifications | ✅ Event streaming | MCP enables automation |
| **Device Control** | ✅ Manual control | ✅ Programmatic | MCP for smart home integration |
| **Event History** | ✅ Timeline view | ✅ API access | App has better visualization |
| **Settings Config** | ✅ Full UI | ✅ API control | App has more options |
| **Multi-Device** | ✅ Dashboard | ✅ Batch operations | MCP for bulk management |

### iOS App Best Practices for MCP

**Notification Management**
- Use app for immediate alerts
- Configure MCP for automated responses
- Set up different notification levels

**Device Testing**
- Test devices first in Ring app
- Verify connectivity and camera angles
- Check motion detection sensitivity

**Account Security**
- Enable 2FA in both app and MCP
- Use strong, unique passwords
- Regularly review shared access

**Troubleshooting with App**
- Check device status in app first
- Compare MCP data with app display
- Use app diagnostics for connectivity issues
- Verify firmware updates through app

---

## ⚙️ MCP Server Configuration

### Environment Variables Setup

**Required Variables**
```bash
# Ring Account Credentials
RING_USERNAME="your-email@example.com"
RING_PASSWORD="your-ring-password"

# Optional: Server Configuration
HOST="0.0.0.0"
PORT="8000"
LOG_LEVEL="INFO"

# Optional: Advanced Features
ENABLE_WEBSOCKET="true"
CACHE_TTL="300"
REQUEST_TIMEOUT="30"
```

**Secure Storage Options**
- **Environment File** (`.env`): For development
- **System Environment**: For production servers
- **Docker Secrets**: For containerized deployments
- **Key Management**: For enterprise deployments

### Claude Desktop Integration

**MCPB Package Installation**
1. Download `ring-mcp-1.0.2.mcpb` from releases
2. Drag package into Claude Desktop settings
3. Configure Ring credentials when prompted
4. Restart Claude Desktop

**Manual Configuration** (Alternative)
```json
{
  "mcpServers": {
    "ring-security": {
      "command": "python",
      "args": ["-m", "ring_mcp"],
      "cwd": "/path/to/ring-mcp",
      "env": {
        "RING_USERNAME": "your-email@example.com",
        "RING_PASSWORD": "your-password"
      }
    }
  }
}
```

### Docker Configuration

**Docker Compose Setup**
```yaml
version: '3.8'
services:
  ring-mcp:
    image: ring-mcp:latest
    environment:
      - RING_USERNAME=${RING_USERNAME}
      - RING_PASSWORD=${RING_PASSWORD}
      - LOG_LEVEL=INFO
    ports:
      - "8123:8123"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
```

---

## 🧪 Testing & Validation

### Basic Connectivity Tests

**Device Discovery Test**
```bash
# Start server
python -m ring_mcp

# In Claude Desktop or API:
ring.list_devices()
# Expected: Array of device objects
```

**Device Status Test**
```bash
ring.get_device_status(device_id="your-device-id")
# Expected: Device health and connectivity info
```

**Live View Test**
```bash
ring.start_live_view(device_id="camera-id")
# Expected: Live stream URL or success confirmation
```

### Advanced Testing Scenarios

**Motion Detection Test**
1. Trigger motion in front of camera
2. Check Ring app for event notification
3. Query MCP for recent events
4. Verify event data consistency

**Doorbell Test**
1. Press doorbell button
2. Confirm Ring app notification
3. Check MCP event stream
4. Validate audio/video capture

**Multi-Device Test**
1. Test multiple cameras simultaneously
2. Verify concurrent access works
3. Check for rate limiting issues
4. Validate device isolation

### Performance Validation

**Response Time Benchmarks**
- Device list: <2 seconds
- Device status: <1 second
- Live view start: <3 seconds
- Event query: <2 seconds

**Reliability Tests**
- 24-hour continuous operation
- Network interruption recovery
- Token refresh handling
- Concurrent user access

---

## 🔧 Troubleshooting

### Authentication Issues

**"2FA Code Required"**
```
Error: Two-factor authentication code required
```
**Solutions**:
1. Check Ring app for 2FA notification
2. Enter code in MCP server prompt
3. Verify 2FA is properly configured
4. Try regenerating 2FA codes

**"Invalid Credentials"**
```
Error: Authentication failed
```
**Solutions**:
1. Verify username/password
2. Reset Ring password if needed
3. Check account lockout status
4. Contact Ring support if persistent

### Device Discovery Problems

**"No Devices Found"**
```
Warning: No Ring devices discovered
```
**Causes & Solutions**:
1. **Account Issue**: Verify devices added to account
2. **Permissions**: Check shared access settings
3. **Connectivity**: Ensure devices online in Ring app
4. **API Access**: Verify Ring API service status

**"Device Offline"**
```
Error: Device currently offline
```
**Solutions**:
1. Check device power and connectivity
2. Verify Wi-Fi signal strength
3. Test device in Ring app first
4. Consider device reset if persistent

### Network & Connectivity

**"Connection Timeout"**
```
Error: Request timed out
```
**Solutions**:
1. Check internet connectivity
2. Verify Ring API service status
3. Increase timeout settings
4. Implement retry logic

**"Rate Limited"**
```
Error: Too many requests
```
**Solutions**:
1. Implement request throttling
2. Add delays between API calls
3. Cache responses when possible
4. Upgrade to paid Ring API tier

### iOS App Integration Issues

**"App and MCP Data Mismatch"**
- Clear app cache and restart
- Force device refresh in app
- Check account sync status
- Verify both using same account

**"Push Notifications Not Working"**
- Verify iOS notification permissions
- Check Ring app notification settings
- Ensure device registered for alerts
- Test with different device

---

## 📞 Support & Resources

### Official Ring Resources
- **Ring Support**: [support.ring.com](https://support.ring.com)
- **Ring Community**: [community.ring.com](https://community.ring.com)
- **Ring Status**: [status.ring.com](https://status.ring.com)

### MCP Server Resources
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Complete API reference and guides
- **Community**: Join MCP developer discussions

### Getting Help
1. **Check Logs**: Review MCP server and Ring app logs
2. **Test with App**: Verify functionality in Ring app first
3. **API Status**: Check Ring API service status
4. **Community Support**: Search existing issues and solutions

---

*This comprehensive guide ensures successful Ring MCP setup with full device onboarding, secure authentication, and seamless iOS app integration.*
