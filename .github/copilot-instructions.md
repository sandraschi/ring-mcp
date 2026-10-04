## Session Context (Ring MCP)

You have access to Ring doorbells, security cameras, burglar alarms, and fire safety devices through the Ring API.

**Before starting work:**
1. Check system status: `get_system_status()` - auth, devices, connectivity
2. List devices: `list_devices()` - discover what is available

**At end of work, save insights:**
- Disarm any panel you armed for testing (see `disarm_security_system()`)
- Document any device status changes or motion events detected
