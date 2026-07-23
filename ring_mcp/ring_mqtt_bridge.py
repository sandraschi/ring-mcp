"""
Optional bridge to [ring-mqtt](https://github.com/tsightler/ring-mqtt) over MQTT.

ring-mqtt publishes Ring Alarm control panels under topics compatible with Home Assistant
discovery, for example::

    {prefix}/{location_id}/alarm/{device_id}/alarm/state
    {prefix}/{location_id}/alarm/{device_id}/alarm/command
    {prefix}/{location_id}/alarm/{device_id}/alarm/attributes
    {prefix}/{location_id}/alarm/{device_id}/status

Commands on ``.../alarm/command`` are plain text: ``disarm``, ``arm_home``, ``arm_away``
(see ring-mqtt ``devices/security-panel.js``).

Run ring-mqtt (Docker or HA add-on) pointed at the same broker, set ``RING_MQTT_ENABLED=1`` here,
and alarm panels appear in ``GET /api/v1/devices`` with ``source: ring_mqtt``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_STATE_TOPIC_RE = re.compile(
    r"^([^/]+)/([^/]+)/alarm/([^/]+)/alarm/state$",
)
_ATTR_TOPIC_RE = re.compile(
    r"^([^/]+)/([^/]+)/alarm/([^/]+)/alarm/attributes$",
)
_STATUS_TOPIC_RE = re.compile(
    r"^([^/]+)/([^/]+)/alarm/([^/]+)/status$",
)


def _truthy(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class _PanelState:
    location_id: str
    device_id: str
    state: str | None = None
    availability: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    last_state_monotonic: float = 0.0


class RingMqttBridge:
    """Subscribes to ring-mqtt alarm topics and publishes arm/disarm commands."""

    def __init__(self) -> None:
        self._enabled = _truthy("RING_MQTT_ENABLED", "0")
        self._url = os.getenv("RING_MQTT_URL", "mqtt://127.0.0.1:1883").strip()
        self._username = (os.getenv("RING_MQTT_USERNAME") or "").strip() or None
        self._password = (os.getenv("RING_MQTT_PASSWORD") or "").strip() or None
        self._prefix = (os.getenv("RING_MQTT_TOPIC_PREFIX", "ring") or "ring").strip().strip("/")
        self._panels: dict[str, _PanelState] = {}
        self._lock = threading.Lock()
        self._client: Any = None
        self._connected = False
        self._last_error: str | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def start(self) -> None:
        if not self._enabled:
            logger.info("ring-mqtt bridge disabled (set RING_MQTT_ENABLED=1 to enable)")
            return
        if self._client is not None:
            return
        try:
            import paho.mqtt.client as mqtt
        except ImportError as e:
            self._last_error = f"paho-mqtt not installed: {e}"
            logger.error(self._last_error)
            return

        parsed = urlparse(self._url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (8883 if parsed.scheme == "mqtts" else 1883)

        def on_connect(client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any) -> None:
            try:
                failed = getattr(reason_code, "is_failure", None)
                if failed is True:
                    self._last_error = f"MQTT connect failed: {reason_code!r}"
                    logger.error("%s", self._last_error)
                    self._connected = False
                    return
                code_val = getattr(reason_code, "value", reason_code)
                if isinstance(code_val, int) and code_val != 0:
                    self._last_error = f"MQTT connect failed: {reason_code!r}"
                    logger.error("%s", self._last_error)
                    self._connected = False
                    return
                self._connected = True
                self._last_error = None
                base = f"{self._prefix}/+/alarm/+"
                client.subscribe(f"{base}/alarm/state", qos=0)
                client.subscribe(f"{base}/alarm/attributes", qos=0)
                client.subscribe(f"{base}/status", qos=0)
                logger.info(
                    "ring-mqtt bridge subscribed prefix=%s host=%s port=%s",
                    self._prefix,
                    host,
                    port,
                )
            except Exception:
                self._last_error = "ring-mqtt bridge on_connect error"
                logger.exception("ring-mqtt bridge on_connect")

        def on_disconnect(client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any) -> None:
            self._connected = False

        def on_message(client: Any, userdata: Any, msg: Any) -> None:
            try:
                topic = msg.topic
                payload = msg.payload.decode("utf-8", errors="replace").strip()
                self._handle_message(topic, payload)
            except Exception:
                logger.exception("ring-mqtt bridge on_message failed")

        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=os.getenv("RING_MQTT_CLIENT_ID", "ring-mcp-bridge").strip() or "ring-mcp-bridge",
            protocol=mqtt.MQTTv311,
        )
        if self._username:
            client.username_pw_set(self._username, self._password or "")
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message
        try:
            if parsed.scheme == "mqtts":
                client.tls_set()
            client.connect(host, port, keepalive=60)
        except Exception as e:
            self._last_error = str(e)
            logger.error("ring-mqtt bridge connect failed: %s", e)
            return
        client.loop_start()
        self._client = client
        logger.info("ring-mqtt bridge loop started")

    def stop(self) -> None:
        if self._client is None:
            return
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception as e:
            logger.warning("ring-mqtt bridge stop: %s", e)
        finally:
            self._client = None
            self._connected = False

    def _handle_message(self, topic: str, payload: str) -> None:
        m = _STATE_TOPIC_RE.match(topic)
        if m:
            root, location_id, device_id = m.group(1), m.group(2), m.group(3)
            if root != self._prefix:
                return
            with self._lock:
                st = self._panels.setdefault(
                    device_id,
                    _PanelState(location_id=location_id, device_id=device_id),
                )
                st.location_id = location_id
                st.state = payload.lower() if payload else None
                st.last_state_monotonic = time.monotonic()
            return

        m = _ATTR_TOPIC_RE.match(topic)
        if m:
            root, location_id, device_id = m.group(1), m.group(2), m.group(3)
            if root != self._prefix:
                return
            try:
                data = json.loads(payload) if payload else {}
            except json.JSONDecodeError:
                data = {}
            with self._lock:
                st = self._panels.setdefault(
                    device_id,
                    _PanelState(location_id=location_id, device_id=device_id),
                )
                st.location_id = location_id
                if isinstance(data, dict):
                    st.attributes = data
            return

        m = _STATUS_TOPIC_RE.match(topic)
        if m:
            root, location_id, device_id = m.group(1), m.group(2), m.group(3)
            if root != self._prefix:
                return
            with self._lock:
                st = self._panels.setdefault(
                    device_id,
                    _PanelState(location_id=location_id, device_id=device_id),
                )
                st.location_id = location_id
                st.availability = payload.lower() if payload else None

    def is_alarm_panel(self, device_id: str) -> bool:
        with self._lock:
            return device_id in self._panels

    def get_device_dict(self, device_id: str) -> dict[str, Any] | None:
        with self._lock:
            st = self._panels.get(device_id)
        if not st:
            return None
        return self._panel_to_device(st)

    def list_alarm_devices(self) -> list[dict[str, Any]]:
        with self._lock:
            panels = list(self._panels.values())
        return [self._panel_to_device(p) for p in panels]

    def _panel_online(self, st: _PanelState) -> bool:
        if st.availability == "online":
            return True
        if st.availability == "offline":
            return False
        # No status topic yet: infer from recent state publishes (ring-mqtt sends state on change).
        age = time.monotonic() - st.last_state_monotonic
        return st.last_state_monotonic > 0 and age < 600

    def _panel_to_device(self, st: _PanelState) -> dict[str, Any]:
        now_iso = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        name = f"Ring Alarm ({st.location_id})"
        return {
            "id": st.device_id,
            "name": name,
            "type": "alarm",
            "family": "ring_mqtt",
            "source": "ring_mqtt",
            "model": "Ring Alarm (ring-mqtt)",
            "firmware": None,
            "battery_life": None,
            "alarm": None,
            "online": self._panel_online(st),
            "address": None,
            "timezone": None,
            "has_subscription": False,
            "last_update": now_iso,
            "mqtt_state": st.state,
            "mqtt_attributes": st.attributes if st.attributes else None,
        }

    def _command_topic(self, st: _PanelState) -> str:
        return f"{self._prefix}/{st.location_id}/alarm/{st.device_id}/alarm/command"

    async def publish_alarm_mode(self, device_id: str, mode: str) -> bool:
        """Publish disarm | arm_home | arm_away to ring-mqtt command topic."""
        if not self._enabled:
            raise RuntimeError("ring-mqtt bridge is disabled")
        mode_l = mode.strip().lower()
        if mode_l not in {"disarm", "arm_home", "arm_away"}:
            raise ValueError("mode must be disarm, arm_home, or arm_away")

        with self._lock:
            st = self._panels.get(device_id)
        if st is None:
            raise ValueError(f"Unknown alarm panel device_id: {device_id}")

        topic = self._command_topic(st)
        payload = mode_l

        def _pub() -> None:
            if self._client is None:
                raise RuntimeError("MQTT client is not running")
            info = self._client.publish(topic, payload, qos=0)
            info.wait_for_publish(timeout=10)

        await asyncio.to_thread(_pub)
        logger.info("ring-mqtt alarm command", topic=topic, mode=mode_l)
        return True


_bridge: RingMqttBridge | None = None


def get_ring_mqtt_bridge() -> RingMqttBridge:
    global _bridge
    if _bridge is None:
        _bridge = RingMqttBridge()
    return _bridge
