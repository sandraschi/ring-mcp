"""
Ring Security System Management Tools - FastMCP 3.4.

Burglar-alarm arming, status, and history against the real Ring API
(ring_mcp.core.ring_client_modern). Arming targets alarm panels by device id
(auto-detected when exactly one panel-shaped device is visible); without any
visible panel the tools say so instead of pretending.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from ..core.exceptions import AuthenticationError, DeviceNotFoundError, RingError
from ..core.ring_client_modern import RingClient

logger = logging.getLogger(__name__)

_READ_ONLY = {"readOnlyHint": True, "idempotentHint": True}
_MUTATING = {"readOnlyHint": False, "idempotentHint": False}


def _is_alarm_panel(device: dict[str, Any]) -> bool:
    """Panel-shaped devices: explicit alarm type/family (never guess from online state)."""
    return "alarm" in str(device.get("type", "")).lower() or "alarm" in str(device.get("family", "")).lower()


async def _resolve_panel_id(client: RingClient, device_id: str | None) -> tuple[str, list[dict[str, Any]]]:
    """Return (panel id, all devices) or raise DeviceNotFoundError with an honest message."""
    devices = await client.get_devices()
    if device_id:
        match = next((d for d in devices if d.get("id") == device_id), None)
        if match is None:
            raise DeviceNotFoundError(f"Device {device_id} not found")
        return device_id, devices
    panels = [d for d in devices if _is_alarm_panel(d)]
    if len(panels) == 1:
        return panels[0]["id"], devices
    if not panels:
        raise DeviceNotFoundError(
            "No alarm panel visible via the Ring API "
            f"({len(devices)} device(s) seen). Pass device_id explicitly "
            "(e.g. an MQTT-bridged panel id) or enable ring-mqtt."
        )
    raise DeviceNotFoundError(
        f"{len(panels)} alarm panels visible - pass device_id explicitly: "
        + ", ".join(f"{d.get('id')} ({d.get('name')})" for d in panels)
    )


def register_tools(app: FastMCP) -> None:
    """Register security system management tools with the FastMCP application.

    Args: See Parameters block.
    """

    @app.tool(
        name="get_security_system_status",
        description="Get comprehensive status of the entire Ring security system",
        annotations=_READ_ONLY,
    )
    async def get_security_system_status() -> dict[str, Any]:
        """Get comprehensive status of the entire Ring security system.

        Armed state is reported as "unknown" unless a panel exposes it -
        online state is NOT treated as armed (that reading would be fabricated).

        ## Return Format
        {"success": true, "message": "...", "system_status": {"mode": ...},
         "devices": {...}, "active_alerts": [...], ...}

        ## Examples
        await get_security_system_status()
        """
        try:
            async with RingClient() as client:
                all_devices = await client.get_devices()

                security_devices = []
                cameras = []
                doorbells = []
                sensors = []
                other_devices = []

                for device in all_devices:
                    device_type = str(device.get("type", "")).lower()
                    device_info = {
                        "device_id": device["id"],
                        "name": device["name"],
                        "type": device["type"],
                        "model": device.get("model"),
                        "online": device.get("online", False),
                        "battery_life": device.get("battery_life"),
                        "firmware": device.get("firmware"),
                        "address": device.get("address"),
                        "last_update": device.get("last_update"),
                        "alarm": device.get("alarm"),
                    }

                    if _is_alarm_panel(device) or "security" in device_type:
                        security_devices.append(device_info)
                    elif "camera" in device_type:
                        cameras.append(device_info)
                    elif "doorbell" in device_type:
                        doorbells.append(device_info)
                    elif "sensor" in device_type:
                        sensors.append(device_info)
                    else:
                        other_devices.append(device_info)

                # Armed state: only trust an explicit panel reading, never online-ness.
                system_status = "unknown"
                armed_flags = [d.get("alarm") for d in security_devices if isinstance(d.get("alarm"), str)]
                if armed_flags:
                    lowered = [str(a).lower() for a in armed_flags]
                    if all("disarm" in a for a in lowered):
                        system_status = "disarmed"
                    elif any("arm" in a for a in lowered):
                        system_status = "armed" if all("arm" in a for a in lowered) else "partial"

                all_events: list[dict[str, Any]] = []
                for device in all_devices:
                    try:
                        events = await client.get_device_events(device["id"], limit=2)
                        all_events.extend(events)
                    except Exception as e:
                        logger.debug("Could not get events for %s: %s", device["id"], e)

                active_alerts = []
                recent_events = sorted(
                    [e for e in all_events if e.get("created_at")],
                    key=lambda x: x.get("created_at", ""),
                    reverse=True,
                )
                recent_security_events = [
                    e for e in recent_events[:5] if e.get("kind") in ["motion", "alarm", "doorbell"]
                ]
                if recent_security_events:
                    active_alerts.append(
                        {
                            "type": "activity",
                            "severity": "info",
                            "message": f"Recent security activity: {len(recent_security_events)} events",
                            "events": recent_security_events,
                        }
                    )

                offline_devices = [d for d in all_devices if not d.get("online", False)]
                if offline_devices:
                    active_alerts.append(
                        {
                            "type": "connectivity",
                            "severity": "warning",
                            "message": f"{len(offline_devices)} devices are offline",
                            "devices": [d["name"] for d in offline_devices],
                        }
                    )

                return {
                    "success": True,
                    "message": f"{len(all_devices)} device(s), system mode: {system_status}",
                    "system_status": {
                        "mode": system_status,
                        "armed": system_status == "armed",
                        "countdown_active": False,
                        "entry_delay": 0,
                    },
                    "devices": {
                        "security": security_devices,
                        "cameras": cameras,
                        "doorbells": doorbells,
                        "sensors": sensors,
                        "other": other_devices,
                    },
                    "device_count": len(all_devices),
                    "online_devices": len([d for d in all_devices if d.get("online", False)]),
                    "active_alerts": active_alerts,
                    "alert_count": len(active_alerts),
                    "last_updated": datetime.now().isoformat(),
                    "emergency_mode": False,
                }

        except AuthenticationError:
            logger.error("Authentication failed checking security status")
            return {
                "success": False,
                "error": "Ring authentication failed. Please check credentials.",
                "error_type": "authentication",
            }
        except Exception as e:
            logger.error("Error getting security status: %s", str(e))
            return {"success": False, "error": str(e), "error_type": "system"}

    @app.tool(
        name="arm_security_system",
        description="Arm the Ring security system with specified mode and options",
        annotations=_MUTATING,
    )
    async def arm_security_system(
        mode: Annotated[Literal["home", "away", "disarmed"], Field(description="Target panel mode.")] = "away",
        bypass_sensors: Annotated[
            list[str] | None, Field(description="Sensor IDs to bypass (panel permitting).")
        ] = None,
        delay_minutes: Annotated[
            int | None, Field(description="Requested entry delay; panel defaults apply.", ge=0, le=30)
        ] = None,
        device_id: Annotated[str | None, Field(description="Alarm panel id (auto-detected when unambiguous).")] = None,
    ) -> dict[str, Any]:
        """Arm the Ring alarm panel (real set_arm_status call).

        ## Return Format
        {"success": true, "message": "Panel ... armed ...", "system_mode": "away", ...}

        ## Examples
        await arm_security_system("away")
        await arm_security_system("home", device_id="alarm-001")
        """
        try:
            valid_modes = ["home", "away", "disarmed"]
            if mode not in valid_modes:
                return {"success": False, "error": f"Invalid mode '{mode}'. Must be one of: {valid_modes}"}

            async with RingClient() as client:
                try:
                    panel_id, devices = await _resolve_panel_id(client, device_id)
                except DeviceNotFoundError as e:
                    return {"success": False, "error": str(e), "error_type": "device_not_found"}

                low_battery = [
                    {"id": d.get("id"), "name": d.get("name"), "battery_life": d.get("battery_life")}
                    for d in devices
                    if isinstance(d.get("battery_life"), (int, float)) and d["battery_life"] < 15
                ]
                warnings = []
                if low_battery:
                    warnings.append(
                        {
                            "type": "low_battery",
                            "message": f"{len(low_battery)} devices have low battery",
                            "devices": [d["name"] for d in low_battery],
                        }
                    )

                armed = await client.set_arm_status(panel_id, mode != "disarmed")

                return {
                    "success": bool(armed),
                    "message": f"Panel {panel_id} {'armed' if armed else 'NOT armed'} ({mode})",
                    "system_mode": mode,
                    "panel_id": panel_id,
                    "bypass_sensors": bypass_sensors or [],
                    "requested_delay_minutes": delay_minutes,
                    "note": "Entry/exit delays and bypass handling follow the panel's own configuration.",
                    "warnings": warnings,
                    "arm_timestamp": datetime.now().isoformat(),
                }

        except DeviceNotFoundError as e:
            logger.error("Device not found during arming: %s", str(e))
            return {"success": False, "error": f"Device not found: {e!s}", "error_type": "device_not_found"}
        except RingError as e:
            logger.error("Ring API error during arming: %s", str(e))
            return {"success": False, "error": f"Ring system error: {e!s}", "error_type": "ring_api"}
        except Exception as e:
            logger.error("Unexpected error during arming: %s", str(e))
            return {"success": False, "error": str(e), "error_type": "unexpected"}

    @app.tool(
        name="disarm_security_system",
        description="Disarm the Ring security system safely with authentication",
        annotations=_MUTATING,
    )
    async def disarm_security_system(
        force_disarm: Annotated[bool, Field(description="Disarm even with recent security activity.")] = False,
        disarm_code: Annotated[
            str | None, Field(description="Accepted for compatibility; the Ring API call needs no code.")
        ] = None,
        device_id: Annotated[str | None, Field(description="Alarm panel id (auto-detected when unambiguous).")] = None,
    ) -> dict[str, Any]:
        """Disarm the Ring alarm panel (real set_arm_status call).

        ## Return Format
        {"success": true, "message": "Panel ... disarmed", "current_mode": "disarmed", ...}

        ## Examples
        await disarm_security_system()
        await disarm_security_system(force_disarm=True)
        """
        try:
            async with RingClient() as client:
                try:
                    panel_id, devices = await _resolve_panel_id(client, device_id)
                except DeviceNotFoundError as e:
                    return {"success": False, "error": str(e), "error_type": "device_not_found"}

                recent_events: list[dict[str, Any]] = []
                for device in devices:
                    try:
                        recent_events.extend(await client.get_device_events(device["id"], limit=5))
                    except Exception as e:
                        logger.debug("Could not get events for %s: %s", device["id"], e)
                security_events = [e for e in recent_events if e.get("kind") in ["motion", "contact", "alarm"]]

                warnings = []
                if security_events and not force_disarm:
                    warnings.append(
                        {
                            "type": "recent_activity",
                            "message": f"Recent security activity detected ({len(security_events)} events)",
                            "events": security_events[:3],
                        }
                    )

                disarmed = await client.set_arm_status(panel_id, False)

                log_entry = {
                    "action": "disarm",
                    "timestamp": datetime.now().isoformat(),
                    "force_disarm": force_disarm,
                    "recent_events_count": len(security_events),
                }

                return {
                    "success": bool(disarmed),
                    "message": f"Panel {panel_id} {'disarmed' if disarmed else 'NOT disarmed'}",
                    "current_mode": "disarmed" if disarmed else "unknown",
                    "panel_id": panel_id,
                    "disarm_timestamp": datetime.now().isoformat(),
                    "force_disarm_used": force_disarm,
                    "recent_activity": security_events,
                    "warnings": warnings,
                    "security_log_entry": log_entry,
                }

        except AuthenticationError:
            logger.error("Authentication failed during disarm")
            return {
                "success": False,
                "error": "Authentication failed. Cannot disarm system.",
                "error_type": "authentication",
                "security_implication": "System remains armed for protection",
            }
        except RingError as e:
            logger.error("Ring API error during disarm: %s", str(e))
            return {"success": False, "error": f"Ring system error: {e!s}", "error_type": "ring_api"}
        except Exception as e:
            logger.error("Unexpected error during disarm: %s", str(e))
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected",
                "security_implication": "System status unknown - manual verification recommended",
            }

    @app.tool(
        name="get_security_history",
        description="Get comprehensive security system history and event timeline",
        annotations=_READ_ONLY,
    )
    async def get_security_history(
        hours: Annotated[int, Field(description="Hours of history to retrieve.", ge=1, le=720)] = 24,
        event_types: Annotated[list[str] | None, Field(description="Filter by event kind strings.")] = None,
        include_video: Annotated[
            bool, Field(description="Attach per-event recording status (no footage listing API exists).")
        ] = False,
    ) -> dict[str, Any]:
        """Get security history from real per-device events.

        ## Return Format
        {"success": true, "message": "N event(s) ...", "events": [...], "summary": {...}, ...}

        ## Examples
        await get_security_history()
        await get_security_history(hours=6, event_types=["motion"])
        """
        try:
            async with RingClient() as client:
                end_time = datetime.now(UTC)
                start_time = end_time - timedelta(hours=hours)
                devices = await client.get_devices()
                name_by_id = {d.get("id"): d.get("name", "Unknown") for d in devices}

                all_events: list[dict[str, Any]] = []
                for device in devices:
                    try:
                        events = await client.get_device_events(device["id"], limit=20)
                    except Exception as e:
                        logger.debug("Could not get events for %s: %s", device["id"], e)
                        continue
                    for event in events:
                        try:
                            created = datetime.fromisoformat(str(event.get("created_at", "")))
                        except ValueError:
                            continue
                        if created < start_time:
                            continue
                        kind = event.get("kind", "unknown")
                        if event_types and kind not in event_types:
                            continue
                        entry: dict[str, Any] = {
                            "timestamp": event.get("created_at"),
                            "event_type": kind,
                            "device_id": device["id"],
                            "device_name": name_by_id.get(device["id"], "Unknown"),
                            "answered": event.get("answered", False),
                        }
                        if include_video:
                            entry["recording_status"] = event.get("recording_status")
                        all_events.append(entry)

                all_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

                arm_events = [e for e in all_events if e["event_type"] in ["arm", "armed"]]
                disarm_events = [e for e in all_events if e["event_type"] in ["disarm", "disarmed"]]
                sensor_events = [e for e in all_events if e["event_type"] in ["motion", "contact", "sensor"]]
                alarm_events = [e for e in all_events if e["event_type"] == "alarm"]

                device_activity: dict[str, dict[str, Any]] = {}
                for event in all_events:
                    name = event["device_name"]
                    slot = device_activity.setdefault(
                        name, {"event_count": 0, "last_activity": None, "event_types": []}
                    )
                    slot["event_count"] += 1
                    slot["last_activity"] = event.get("timestamp")
                    if event["event_type"] not in slot["event_types"]:
                        slot["event_types"].append(event["event_type"])

                arm_disarm_timeline = [
                    {"timestamp": e.get("timestamp"), "action": e.get("event_type")}
                    for e in sorted(arm_events + disarm_events, key=lambda x: x.get("timestamp", ""))
                ]

                summary = {
                    "total_events": len(all_events),
                    "arm_events": len(arm_events),
                    "disarm_events": len(disarm_events),
                    "sensor_triggers": len(sensor_events),
                    "alarm_events": len(alarm_events),
                    "active_devices": len(device_activity),
                    "time_period_hours": hours,
                    "most_active_device": max(device_activity.items(), key=lambda x: x[1]["event_count"])[0]
                    if device_activity
                    else None,
                }

                return {
                    "success": True,
                    "message": f"{len(all_events)} event(s) in the last {hours}h",
                    "time_range": {"start": start_time.isoformat(), "end": end_time.isoformat(), "hours": hours},
                    "events": all_events,
                    "summary": summary,
                    "device_activity": device_activity,
                    "arm_disarm_timeline": arm_disarm_timeline,
                    "categorized_events": {
                        "arm_events": arm_events,
                        "disarm_events": disarm_events,
                        "sensor_events": sensor_events,
                        "alarm_events": alarm_events,
                    },
                }

        except Exception as e:
            logger.error("Error retrieving security history: %s", str(e))
            return {"success": False, "error": str(e), "time_range_requested": f"{hours} hours"}
