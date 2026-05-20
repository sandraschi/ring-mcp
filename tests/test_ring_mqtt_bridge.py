"""Unit tests for ring-mqtt MQTT topic parsing (Ring Alarm bridge)."""

import json

from ring_mcp.ring_mqtt_bridge import RingMqttBridge, _ATTR_TOPIC_RE, _STATE_TOPIC_RE, _STATUS_TOPIC_RE


def test_state_topic_regex_matches_ring_mqtt_layout():
    t = "ring/abc123-loc/alarm/device-uuid-99/alarm/state"
    assert _STATE_TOPIC_RE.match(t)
    m = _STATE_TOPIC_RE.match(t)
    assert m is not None
    assert m.groups() == ("ring", "abc123-loc", "device-uuid-99")


def test_attributes_topic_regex():
    t = "ring/loc1/alarm/dev1/alarm/attributes"
    assert _ATTR_TOPIC_RE.match(t)


def test_status_topic_regex():
    t = "ring/loc1/alarm/dev1/status"
    assert _STATUS_TOPIC_RE.match(t)


def test_handle_message_populates_panel():
    b = RingMqttBridge.__new__(RingMqttBridge)
    b._prefix = "ring"
    b._panels = {}
    b._lock = __import__("threading").Lock()

    b._handle_message("ring/my-loc/alarm/panel-1/alarm/state", "armed_home")
    with b._lock:
        st = b._panels.get("panel-1")
    assert st is not None
    assert st.state == "armed_home"
    assert st.location_id == "my-loc"

    b._handle_message("ring/my-loc/alarm/panel-1/alarm/attributes", json.dumps({"targetState": "armed_away"}))
    with b._lock:
        st = b._panels["panel-1"]
    assert st.attributes.get("targetState") == "armed_away"

    b._handle_message("ring/my-loc/alarm/panel-1/status", "online")
    with b._lock:
        st = b._panels["panel-1"]
    assert st.availability == "online"
