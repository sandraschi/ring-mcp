## Session Context (Ring MCP)

You have access to Ring doorbells, security cameras, burglar alarms, and fire safety devices through the Ring API.

**Before starting work:**
1. Check system health: `health_check()` - verifies API connectivity
2. List your devices: `get_devices()` - discover what's available

**At end of work, save insights:**
- Arm alarms if the user requested security changes
- Document any device status changes or motion events detected
