# Troubleshooting Guide - Ring-MCP

## Connection Issues

### Problem: Device Shows Offline

**Common Causes:**
- Wi-Fi connectivity lost
- Power issue (battery dead, power out)
- Router reboot/configuration change
- Distance from router (weak signal)
- Interference (2.4GHz crowded)

**Solutions:**
1. ✅ Check Wi-Fi router is online
2. ✅ Check device battery/power
3. ✅ Move closer to router or add Chime Pro (extender)
4. ✅ Reboot device (remove battery 30 sec, or power cycle)
5. ✅ Check Ring app for service outage
6. ✅ Reconnect device to Wi-Fi (Setup mode)

### Problem: Ring App Won't Connect

**Solutions:**
- Check internet connection
- Update Ring app (latest version)
- Clear app cache (Settings → Apps → Ring → Clear Cache)
- Log out and back in
- Reinstall app if persistent
- Verify Ring account active

### Problem: MCP Server Can't Authenticate

**Solutions:**
- Verify Ring credentials correct
- Check 2FA code if enabled
- Refresh authentication token
- Clear stored tokens and re-authenticate
- Check Ring account not locked
- Verify API access not blocked

---

## Device-Specific Issues

### Doorbell Issues

**Problem: Doorbell Not Ringing**
```
Mechanical chime:
- Check chime kit installed correctly
- Verify transformer voltage (16-24V AC)
- Test doorbell button manually

Digital notifications:
- Check app notification permissions
- Verify sound enabled in app
- Check phone not in Do Not Disturb
- Test notification (Ring app → Device → Test Notification)
```

**Problem: Poor Video Quality**
```
Solutions:
- Improve Wi-Fi signal (closer to router, extender)
- Change video quality setting (Ring app)
- Clean camera lens
- Check upload bandwidth (4 Mbps minimum)
- Reduce other network activity
```

**Problem: Motion Detection Not Working**
```
Checklist:
- Motion detection enabled (not paused)
- Motion sensitivity appropriate (not too low)
- Motion zones configured correctly
- Firmware up-to-date
- Device has power/battery
- Not in "Disarmed" mode (if linked to alarm)
```

### Camera Issues

**Problem: Night Vision Not Working**
```
Solutions:
- Clean camera lens (dirt reduces IR effectiveness)
- Check night vision setting (auto, on, off)
- Verify infrared LEDs functioning (dim red glow)
- Update firmware
- Contact Ring support if hardware failure
```

**Problem: False Motion Alerts**
```
Common causes:
- Trees/bushes moving in wind
- Sunlight/shadows changing
- Reflections (windows, water)
- Insects near camera (especially at night)
- Weather (rain, snow)

Solutions:
- Reduce motion sensitivity
- Adjust motion zones (exclude problem areas)
- Enable People Only Mode (Ring Protect)
- Adjust camera angle
- Consider different mounting location
```

**Problem: Battery Drains Quickly**
```
Causes & solutions:
- High motion area: Reduce sensitivity or zones
- Cold weather: Bring inside to charge, consider hardwiring
- Weak Wi-Fi: Add extender, move router closer
- Many live views: Limit usage
- Firmware issue: Update or contact support

Expected battery life:
- Normal: 6-12 months (varies widely)
- High activity: 3-6 months
- Cold weather: Significantly reduced
```

---

## Alarm System Issues

### Problem: Sensors Not Reporting

**Solutions:**
- Check battery (sensor and base station)
- Verify within Z-Wave range (< 250 ft from base)
- Add Range Extender if needed
- Re-pair sensor with base station
- Check sensor physically attached correctly

### Problem: False Alarms

**Causes:**
- Pets triggering motion detectors
- Contact sensors misaligned
- Door/window movement (wind)
- Low battery causing erratic behavior

**Solutions:**
- Pet-immune motion detectors (ceiling-mounted)
- Adjust contact sensor alignment
- Increase alarm delay (time to disarm)
- Replace low batteries promptly
- Disable problematic sensors temporarily

### Problem: Base Station Offline

**Critical Issue:**
- No alarm protection!
- No sensor monitoring
- Cellular backup (if equipped) may still work

**Solutions:**
1. Check power connection
2. Check ethernet connection (if wired)
3. Reboot base station (unplug 30 sec)
4. Check for service outage
5. Contact Ring support (24/7 available)

---

## Ring-MCP Server Issues

### Problem: MCP Server Won't Start

**Checklist:**
1. Python 3.10+ installed
2. Dependencies: `pip install -r requirements.txt`
3. Ring credentials configured
4. Ports not in use
5. Check server logs

### Problem: Authentication Keeps Failing

**Debug:**
```python
# Test authentication manually
from ring_doorbell import Ring

ring = Ring(username, password)
ring.update_data()  # Should succeed if credentials correct

# If 2FA:
# Follow prompts for 2FA code
```

**Solutions:**
- Verify username/password correct
- Complete 2FA process
- Check Ring account not locked (too many login attempts)
- Wait 15 minutes if rate-limited
- Use app to verify account active

### Problem: Events Not Updating

**Solutions:**
- Check WebSocket connection (may have dropped)
- Restart MCP server
- Verify Ring API not rate-limiting
- Check internet connection stability
- Review MCP server logs for errors

---

## Video Streaming Issues

### Problem: Live View Won't Load

**Solutions:**
- Check device online
- Verify upload bandwidth (device side)
- Check download bandwidth (client side)
- Try lower quality setting
- Close other video streams
- Reboot device
- Check Ring service status

### Problem: Video Lag/Buffering

**Causes:**
- Slow internet connection
- Network congestion
- Device battery low (reduced performance)
- Too many simultaneous streams
- Distance from router

**Solutions:**
- Reduce video quality
- Improve Wi-Fi signal
- Close other streams/apps
- Charge battery if low
- Upgrade internet plan if consistently slow

---

## Advanced Troubleshooting

### Diagnostic Commands
```python
# Comprehensive health check
health = get_system_health()

# Device diagnostics
diag = run_device_diagnostics(device_id="abc123")

# Network test
network = test_network_quality(device_id="abc123")

# Event log
events_log = get_error_events(hours=24)
```

### Logs and Debugging
```
Ring-MCP logs location:
- Application logs: logs/ring-mcp.log
- Error logs: logs/errors.log
- Event logs: logs/events.log

Check for:
- Authentication errors
- API rate limit messages
- Device communication failures
- WebSocket disconnections
- Timeout errors

Enable debug logging:
- Set LOG_LEVEL=DEBUG in environment
- Restart server
- Reproduce issue
- Review debug logs
```

### Factory Reset (Last Resort)
```
When to factory reset:
- Device consistently malfunctions
- Can't reconnect to Wi-Fi
- Firmware update failed
- Unresponsive to all commands

Process:
1. Hold setup button 20 seconds
2. Light flashes (reset in progress)
3. Set up as new device
4. Reconfigure all settings
5. Test functionality

⚠️ NOTE: Loses all device settings!
```

---

## Common Error Messages

### "Device is Busy"
- Device handling another request
- Wait 30 seconds, retry
- Close other apps accessing device
- Reboot device if persistent

### "Request Timed Out"
- Network connectivity issue
- Ring service slow
- Increase timeout setting
- Check internet connection
- Retry in a few minutes

### "Rate Limit Exceeded"
- Too many API requests
- Wait 1-5 minutes
- Reduce polling frequency
- Implement caching
- Contact Ring if legitimate high usage

### "Invalid Token"
- Authentication expired
- Re-authenticate with credentials
- Check if password changed
- Verify 2FA still active
- May need to reauthorize MCP server

---

## Emergency Procedures

### If Ring System Completely Down
```
Backup security:
1. Check physical locks (all doors/windows)
2. Use alternative security (other cameras, alarm)
3. Manually monitor (periodically check outside)
4. Contact Ring support (troubleshoot)
5. Consider temporary security measures

Communication:
- Ring support: 24/7 available
- Ring Neighbors: Community awareness
- Local authorities: If active threat
```

### If Device Damaged/Stolen
```
Immediate actions:
1. Report to Ring (may get replacement)
2. Remove device from account (prevent unauthorized access)
3. File police report (theft)
4. Review footage before incident (evidence)
5. Check homeowner's insurance (may cover)
6. Replace device
7. Improve security (better mounting, additional cameras)
```

---

## Getting Help

### Support Resources (In Order):

1. **This troubleshooting guide** - Common Ring issues
2. **Ring-MCP Documentation** - README, docs/
3. **Ring Support** - 24/7 support (1-800-656-1918)
4. **Ring Community** - Forums, user experiences
5. **GitHub Issues** - Ring-MCP specific problems

### When Contacting Support

**Have ready:**
- Device model and serial number
- Ring account email
- Description of issue
- When issue started
- Troubleshooting steps tried
- Error messages (exact text)
- Event IDs (if applicable)

---

## Prevention Best Practices

### Proactive Maintenance:
- ✅ Monthly device health checks
- ✅ Quarterly battery charging (even if not low)
- ✅ Clean camera lenses seasonally
- ✅ Test alarm system monthly
- ✅ Update firmware promptly
- ✅ Review and adjust settings regularly

### Monitoring Best Practices:
- ✅ Daily event review (5-10 min)
- ✅ Weekly trend analysis
- ✅ Regular testing (motion, doorbell, alarm)
- ✅ Document all incidents
- ✅ Maintain redundant security (don't rely only on Ring)

### Security Hygiene:
- ✅ Strong Ring account password
- ✅ 2FA enabled (always!)
- ✅ Unique password (not reused)
- ✅ Regular password changes
- ✅ Authorized users only
- ✅ Revoke access for old users/devices

---

**Austrian Reliability**: Prevent problems, solve issues methodically, maintain constant security! 🇦🇹🔧

