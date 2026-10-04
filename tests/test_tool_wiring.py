"""
Tool wiring tests: invoke every served MCP tool through a FastMCP client with a
modern-spec mock client. No Ring credentials needed.

Purpose: prove the tool modules are wired to the REAL client API
(ring_mcp.core.ring_client_modern) - every body runs without AttributeError /
TypeError and returns its documented shape. ring_shutdown is excluded on
purpose (it calls os._exit).
"""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import Client

from ring_mcp.core.exceptions import StreamingError
from ring_mcp.server import create_app

APP = create_app()

MODULES_WITH_CLIENT = [
    "ring_mcp.tools.monitoring_tools",
    "ring_mcp.tools.camera_tools",
    "ring_mcp.tools.fire_safety_tools",
    "ring_mcp.tools.automation_tools",
    "ring_mcp.tools.doorbell_tools",
    "ring_mcp.tools.security_system_tools",
    "ring_mcp.tools.status_tool",
    "ring_mcp.server",
]


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_devices():
    return [
        {
            "id": "doorbell-001",
            "name": "Front Door",
            "type": "doorbell",
            "family": "doorbell",
            "model": "Ring Video Doorbell Pro",
            "firmware": "4.2.1",
            "battery_life": 85,
            "online": True,
            "address": "123 Main St",
            "timezone": "America/New_York",
            "has_subscription": True,
            "last_update": _now_iso(),
        },
        {
            "id": "camera-001",
            "name": "Backyard Cam",
            "type": "camera",
            "family": "camera",
            "model": "Ring Spotlight Cam Pro",
            "firmware": "3.1.0",
            "battery_life": 92,
            "online": True,
            "address": "123 Main St",
            "timezone": "America/New_York",
            "has_subscription": True,
            "last_update": _now_iso(),
        },
        {
            "id": "alarm-001",
            "name": "Home Security System",
            "type": "alarm",
            "family": "alarm",
            "model": "Ring Alarm Pro",
            "firmware": "2.8.3",
            "battery_life": None,
            "online": True,
            "address": "123 Main St",
            "timezone": "America/New_York",
            "has_subscription": True,
            "last_update": _now_iso(),
        },
    ]


def fresh_events():
    return [
        {"id": "event-001", "created_at": _now_iso(), "answered": False, "kind": "motion", "recording_status": "ready"},
        {
            "id": "event-002",
            "created_at": _now_iso(),
            "answered": True,
            "kind": "doorbell",
            "recording_status": "ready",
        },
    ]


def make_client(devices=None, events=None):
    """Modern-spec mock that also works as an async context manager."""
    from ring_mcp.core.ring_client_modern import RingClient

    mock_client = MagicMock(spec=RingClient)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.connect = AsyncMock(return_value=None)
    mock_client.get_devices = AsyncMock(return_value=devices if devices is not None else make_devices())
    by_id = {d["id"]: d for d in (devices if devices is not None else make_devices())}
    mock_client.get_device = AsyncMock(side_effect=lambda device_id: by_id.get(device_id))
    mock_client.get_device_events = AsyncMock(return_value=events if events is not None else fresh_events())
    mock_client.set_arm_status = AsyncMock(return_value=True)
    mock_client.trigger_chime = AsyncMock(return_value=True)
    mock_client.get_live_stream_url = AsyncMock(
        side_effect=StreamingError("Use WebRTC streaming: connect to /api/v1/devices/{id}/stream/webrtc")
    )
    return mock_client


def patch_all_clients(mock_client):
    """Patch the RingClient name in every module that instantiates it."""
    return [patch(f"{module}.RingClient", return_value=mock_client) for module in MODULES_WITH_CLIENT]


def _stack(patches):
    for p in patches:
        p.start()


def _unstack(patches):
    for p in reversed(patches):
        p.stop()


async def _call(name, args=None):
    async with Client(APP) as client:
        result = await client.call_tool(name, args or {})
    if result.data is not None:
        return result.data
    return json.loads(result.content[0].text)


@pytest.fixture
def wired():
    """All module RingClient names patched to a modern-spec mock."""
    mock_client = make_client()
    patches = patch_all_clients(mock_client)
    _stack(patches)
    yield mock_client
    _unstack(patches)


async def test_wiring_monitoring(wired):
    health = await _call("monitor_system_health")
    assert health["success"] is True
    assert health["overall_health_score"] == 100
    activity = await _call("get_real_time_activity")
    assert activity["success"] is True
    assert activity["activity_count"] == 6  # 3 devices x 2 events


async def test_wiring_cameras(wired):
    status = await _call("get_camera_status")
    assert status["success"] is True
    assert status["total_cameras"] == 1
    streams = await _call("stream_all_cameras")
    # Stream URLs are retired: honest per-camera failures, still a shaped payload.
    assert streams["success"] is True
    assert streams["total_streams"] == 0
    assert len(streams["failed_cameras"]) == 1


async def test_wiring_fire(wired):
    status = await _call("get_fire_alarm_status")
    assert status["success"] is True
    assert status["system_health"] == "no_devices"  # mock set has no smoke/fire type
    test = await _call("test_fire_safety_system")
    assert test["success"] is True


async def test_wiring_doorbell_status(wired):
    status = await _call("get_doorbell_status")
    assert status["success"] is True
    assert status["summary"]["total_doorbells"] == 1
    assert status["summary"]["online_doorbells"] == 1


async def test_wiring_doorbell_honest_unsupported(wired):
    stream = await _call("get_doorbell_live_stream")
    assert stream["success"] is False
    assert "webrtc" in stream
    answer = await _call("answer_doorbell_call")
    assert answer["success"] is False
    assert answer["unsupported"] is True
    motion = await _call("configure_motion_detection", {"sensitivity": "low"})
    assert motion["success"] is False
    assert motion["requested_configuration"]["sensitivity"] == "low"


async def test_wiring_visitor_history(wired):
    history = await _call("get_visitor_history", {"hours": 24})
    assert history["success"] is True
    assert history["summary"]["total_events"] == 2
    assert history["summary"]["active_doorbells"] == 1


async def test_wiring_security_status(wired):
    status = await _call("get_security_system_status")
    assert status["success"] is True
    # Armed state must never be fabricated from online-ness.
    assert status["system_status"]["mode"] == "unknown"
    assert status["system_status"]["armed"] is False
    assert status["device_count"] == 3


async def test_wiring_arm_disarm(wired):
    armed = await _call("arm_security_system", {"mode": "away"})
    assert armed["success"] is True
    assert armed["panel_id"] == "alarm-001"
    wired.set_arm_status.assert_any_call("alarm-001", True)
    disarmed = await _call("disarm_security_system", {})
    assert disarmed["success"] is True
    assert disarmed["current_mode"] == "disarmed"
    bad = None
    try:
        # Invalid Literal is rejected by FastMCP validation before the body runs.
        await _call("arm_security_system", {"mode": "nope"})
    except Exception as e:
        bad = e
    assert bad is not None


async def test_wiring_security_history(wired):
    history = await _call("get_security_history", {"hours": 24})
    assert history["success"] is True
    assert history["summary"]["total_events"] == 6
    video = await _call("get_security_history", {"hours": 24, "include_video": True})
    assert video["events"][0]["recording_status"] == "ready"


async def test_wiring_status_tools(wired):
    system = await _call("get_system_status")
    assert system["system_status"] == "healthy"
    auth = await _call("check_authentication_status")
    assert auth["authenticated"] is True
    conn = await _call("check_device_connectivity")
    assert conn["devices_tested"] == 3
    assert conn["devices_online"] == 3
    health = await _call("get_service_health")
    assert health["health_score"] == 100


async def test_wiring_help_tools():
    tools = await _call("list_available_tools")
    assert tools["total_count"] > 20
    detail = await _call("get_tool_help", {"tool_name": "list_devices"})
    assert detail["success"] is True
    assert detail["tool_name"] == "list_devices"
    found = await _call("search_tools", {"query": "camera"})
    assert found["success"] is True
    assert found["total_matches"] >= 1


async def test_wiring_list_and_cards(wired):
    listed = await _call("list_devices")
    assert listed["success"] is True
    assert listed["count"] == 3
    cameras = await _call("list_devices", {"device_type": "camera"})
    assert cameras["count"] == 1
    devices_card = await _call("show_devices_card")
    assert "3 devices" in devices_card["content"]
    health_card = await _call("show_health_card")
    assert "content" in health_card


async def test_wiring_automation(wired):
    created = await _call(
        "create_security_automation",
        {
            "trigger_type": "motion",
            "trigger_conditions": {"device_id": "camera-001"},
            "response_actions": [{"action": "notify"}],
            "automation_name": "Night watch",
        },
    )
    assert created["success"] is True
    assert created["status"] == "created"
    emergency = await _call("trigger_emergency_protocol")
    assert emergency["success"] is True
    assert emergency["protocol_activated"] is True
    scheduled = await _call(
        "schedule_security_modes",
        {"schedule_config": {"modes": ["armed", "disarmed"], "timeframes": []}},
    )
    assert scheduled["success"] is True
    assert scheduled["schedule_active"] is True
