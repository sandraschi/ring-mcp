# Event Handling Guide - Ring-MCP

## Ring Event Types

### Motion Events
```
Person Detected:
- Timestamp, duration
- Detection confidence
- Snapshot URL
- Video URL (if recorded)

Package Detected:
- Delivery timestamp
- Package location
- Image of package
- Carrier identification (AI)

Animal Detected:
- Pet vs wildlife
- Location
- Frequency (recurring visitor?)

Vehicle Detected:
- Entering/exiting driveway
- Parking nearby
- License plate (if visible)
```

### Doorbell Events
```
Ding (Button Pressed):
- Visitor timestamp
- Snapshot of visitor
- Two-way audio session
- Response (answered, ignored, quick reply)

Motion at Door:
- Approaching visitor (before ring)
- Package delivery (no ring)
- Departing visitor
```

### Alarm Events
```
Contact Sensor:
- Door/window opened
- Sensor ID and location
- Armed mode when triggered
- Authorization check

Motion Detector:
- Interior motion
- Zone triggered
- Time of detection
- Alarm mode

Panic Button:
- EMERGENCY activation
- User who pressed
- Location
- Immediate response required
```

## Event Processing

### Event Filtering
```python
# Get relevant events only
events = get_events(
    device_types=["doorbells", "cameras"],
    event_types=["motion", "ding"],
    min_confidence=0.7,  # Filter low-confidence AI
    time_range="last_2_hours"
)

Smart filtering:
- Ignore low-confidence detections
- Group rapid events (same incident)
- Filter animals (unless relevant)
- Focus on people/packages
```

### Event Correlation
```python
# Correlate events across devices
if doorbell_motion and front_yard_cam_motion:
    # Same person approaching
    incident = correlate_events([doorbell_event, cam_event])
    
    # Enhanced context:
    # - Person's path (yard → door)
    # - Better visual angles
    # - Timing of approach
    # - Behavior patterns
```

### Event Prioritization
```
Priority Levels:

CRITICAL (respond immediately):
- Alarm triggered
- Panic button pressed
- Forced entry detected
- Person at door (late night, armed mode)

HIGH (respond within minutes):
- Motion detected (armed mode)
- Unknown person loitering
- Package delivered
- Doorbell pressed

MEDIUM (review soon):
- Motion detected (disarmed)
- Expected visitor
- Delivery vehicle
- Known person

LOW (daily review):
- Animal detection
- Tree/shadow motion
- Weather-related triggers
- Test events
```

## Event Response Workflows

### Doorbell Press Response
```
Immediate actions:
1. View live video (who is it?)
2. Identify:
   - Known person: Answer, unlock, or quick reply
   - Delivery: Accept, provide instructions
   - Solicitor: Quick reply "Not interested"
   - Unknown: Assess, may answer or ignore
   - Suspicious: Do not answer, monitor, call authorities

Quick Reply options:
- "Leave package at door, thank you"
- "Not interested, please leave"
- "One moment, I'll be right there"
- "We're not home, please come back later"
- Custom messages
```

### Motion Alert Response
```
Assessment questions:
1. Expected or unexpected?
2. Time of day (day vs night matters)
3. Alarm mode (armed vs disarmed)
4. Person, animal, or vehicle?
5. On property or passing by?

Response matrix:
- Expected + Day + Disarmed = Low priority (log only)
- Unexpected + Day + Armed = Medium (investigate)
- Unknown + Night + Armed = High (immediate attention)
- Forced entry + Any + Any = CRITICAL (call 911)
```

### Package Delivery Response
```
Upon package detection:
1. Confirm delivery (check snapshot)
2. Identify carrier (USPS, UPS, FedEx, Amazon)
3. Note package location
4. Alert household members
5. Retrieve package promptly (theft prevention)
6. Monitor package location until retrieved
7. Disable enhanced monitoring after retrieval
```

### Alarm Trigger Response
```
CRITICAL - IMMEDIATE ACTIONS:

1. VERIFY:
   - Check all camera feeds
   - Confirm real threat vs false alarm
   - Identify trigger sensor

2. If FALSE ALARM:
   - Disarm quickly (prevent monitoring company call)
   - Identify cause (wind, pet, malfunction)
   - Adjust sensor/settings
   - Note for future prevention

3. If REAL INTRUSION:
   - DO NOT DISARM
   - Call 911 immediately
   - Provide address, situation
   - Stream video to authorities if possible
   - Stay safe (do not confront)
   - Wait for police

4. AFTER RESOLUTION:
   - Save all video evidence
   - Document incident
   - Review security gaps
   - Adjust system if needed
```

## Event History Analysis

### Daily Review
```python
# End-of-day event summary
summary = get_daily_summary()

Review:
- Total events (motion, doorbell, alarm)
- Unusual activity (unexpected visitors)
- Device performance (any offline?)
- Battery status (charging needed?)
- False alarm rate (adjust if high)

Time: 5-10 minutes daily
Value: Catch issues early, identify patterns
```

### Weekly Analysis
```python
# Weekly security report
report = get_weekly_report()

Trends:
- Event frequency (increasing/decreasing?)
- Time patterns (when are most events?)
- Device reliability (any consistently offline?)
- Battery drain rates (seasonal changes?)
- False alarm trends (adjust sensitivity)

Actions:
- Adjust motion zones if false alarms
- Recharge batteries if declining
- Investigate unusual patterns
- Update automation rules
```

### Incident Investigation
```python
# Investigate suspicious event
investigation = investigate_incident(
    timestamp="2025-10-25 02:30:00",
    include_before_seconds=300,  # 5 min before
    include_after_seconds=600,   # 10 min after
    devices=["all_cameras", "all_sensors"]
)

Compile:
- Timeline of all events
- All camera angles
- Sensor triggers
- Alarm status changes
- Entry/exit points
- Vehicle/person descriptions
```

---

## Event Storage and Retrieval

### Cloud Storage (Ring Protect)
```
Subscription tiers:
- Basic ($4/month per device): 180-day history
- Plus ($10/month all devices): 180-day + extended features
- Pro ($20/month): 180-day + professional monitoring

Without subscription:
- Live view only (no history)
- Real-time alerts
- No video storage
```

### Local Storage
```
Options:
- Download important videos (before expiry)
- External NVR (some models)
- Ring Alarm Pro (local video storage)
- Third-party integration (Home Assistant)

Best practices:
- Download critical evidence immediately
- Organize by date/incident
- Multiple backup copies
- Secure storage (encrypted)
```

### Event Retention Policy
```
Recommended:
- Critical events: Keep 1+ year
- Security incidents: Permanent
- Daily routine: 30-90 days
- False alarms: 7-14 days
- Test footage: Delete after verification

Legal considerations:
- Comply with local recording laws
- Provide to authorities when requested
- Delete when no longer needed
- Secure storage (prevent unauthorized access)
```

---

## Event API Usage

### Get Events
```python
# Recent events
events = get_events(limit=50, order="desc")

# Filtered events
motion_events = get_events(
    event_type="motion",
    start_date="2025-10-20",
    device_id="front_door"
)

# Search events
search_results = search_events(
    query="person detected",
    confidence_min=0.8
)
```

### Event Details
```python
# Get full event information
event_detail = get_event_details(event_id="evt_123")

Includes:
- Timestamp (creation, end)
- Device information
- Event type and confidence
- Recording URL
- Snapshot URL
- Detection metadata (person, package, etc.)
- User who viewed/handled
```

### Real-Time Event Stream
```python
# Subscribe to live events
event_stream = subscribe_to_events(
    device_ids=["all"],
    event_types=["motion", "ding", "alarm"]
)

# Handle events as they occur
for event in event_stream:
    handle_event(event)
    # Real-time response with minimal latency
```

---

## Best Practices

### Event Management:
- ✅ Review events daily
- ✅ Save important footage
- ✅ Delete unnecessary old events
- ✅ Adjust filters to reduce noise
- ✅ Document security incidents

### Privacy:
- ✅ Inform visitors of recording (signage)
- ✅ Respect neighbor privacy (zone placement)
- ✅ Secure access to footage
- ✅ Delete when no longer needed
- ✅ Comply with local laws

### Efficiency:
- ✅ Use AI filtering (Ring Protect)
- ✅ Customize motion zones
- ✅ Appropriate sensitivity levels
- ✅ Scheduled notification modes
- ✅ Batch review non-critical events

---

**Austrian Precision**: Every event logged, analyzed, and acted upon appropriately! 🇦🇹📊

