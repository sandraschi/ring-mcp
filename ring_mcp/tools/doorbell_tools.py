"""
Ring Doorbell Management Tools - FastMCP 3.4.

Doorbell operations against the real Ring API (ring-doorbell via
ring_mcp.core.ring_client_modern): status, visitor history, and WebRTC
live-view handoff. Two endpoints Ring does not expose to wrappers
(direct stream URLs, two-way audio, motion configuration) return explicit
unsupported errors instead of fake data - see each tool's notes.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal

from fastmcp import FastMCP
from pydantic import Field

from ..core.exceptions import DeviceNotFoundError
from ..core.ring_client_modern import RingClient

logger = logging.getLogger(__name__)

_READ_ONLY = {"readOnlyHint": True, "idempotentHint": True}

_WEBRTC_HINT = (
    "Ring video is WebRTC-only. In a browser use the Doorbell page live view, "
    "or signal manually via WS /api/v1/devices/{id}/stream/webrtc "
    "(REST: POST /api/v1/webrtc/offer, /api/v1/webrtc/candidate)."
)


def register_tools(app: FastMCP) -> None:
    """Register doorbell management tools with the FastMCP application.

    Args: See Parameters block.
    """

    @app.tool(
        name="get_doorbell_status",
        description="Get comprehensive status of all Ring doorbells in the system",
        annotations=_READ_ONLY,
    )
    async def get_doorbell_status() -> dict[str, Any]:
        """Get comprehensive status of all Ring doorbells in the system.

        ## Return Format
        {"success": true, "message": "N doorbell(s) found", "doorbells": [...],
         "summary": {"total_doorbells": N, "online_doorbells": N, "offline_doorbells": N}}

        ## Examples
        await get_doorbell_status()
        """
        try:
            async with RingClient() as client:
                all_devices = await client.get_devices()
                doorbells = [d for d in all_devices if d.get("type") == "doorbell"]

                doorbell_status = []
                offline_count = 0
                for doorbell in doorbells:
                    details = await client.get_device(doorbell["id"]) or doorbell
                    if not details.get("online", False):
                        offline_count += 1
                    doorbell_status.append(
                        {
                            "device_id": details.get("id"),
                            "name": details.get("name", "Ring Doorbell"),
                            "model": details.get("model", "Unknown"),
                            "online": details.get("online", False),
                            "battery_life": details.get("battery_life"),
                            "firmware": details.get("firmware"),
                            "last_update": details.get("last_update"),
                        }
                    )

                return {
                    "success": True,
                    "message": f"{len(doorbell_status)} doorbell(s) found",
                    "doorbells": doorbell_status,
                    "summary": {
                        "total_doorbells": len(doorbell_status),
                        "online_doorbells": len(doorbell_status) - offline_count,
                        "offline_doorbells": offline_count,
                    },
                    "last_updated": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error("Error getting doorbell status: %s", str(e))
            return {"success": False, "error": str(e)}

    @app.tool(
        name="get_doorbell_live_stream",
        description="Get live video stream from Ring doorbell (WebRTC handoff)",
        annotations=_READ_ONLY,
    )
    async def get_doorbell_live_stream(
        doorbell_id: Annotated[
            str | None, Field(description="Specific doorbell ID (uses first doorbell if omitted).")
        ] = None,
        quality: Annotated[
            Literal["low", "medium", "high"], Field(description="Preferred quality (WebRTC negotiates actual).")
        ] = "high",
        duration_seconds: Annotated[int, Field(description="Intended watch duration in seconds.", ge=5, le=600)] = 30,
    ) -> dict[str, Any]:
        """Point the caller at the working WebRTC live-view flow.

        Ring retired direct stream URLs - video is WebRTC-only and needs an SDP
        exchange, which MCP tools cannot perform. This tool verifies the doorbell
        exists, then returns the exact signaling endpoints to use.

        ## Return Format
        {"success": false, "error": "Direct stream URLs are retired; ...",
         "doorbell_id": "...", "webrtc": {"websocket": "...", "rest_offer": "..."}}

        ## Examples
        await get_doorbell_live_stream()
        await get_doorbell_live_stream(doorbell_id="doorbell-001")
        """
        try:
            async with RingClient() as client:
                if doorbell_id:
                    doorbell = await client.get_device(doorbell_id)
                    if not doorbell or doorbell.get("type") != "doorbell":
                        return {"success": False, "error": f"Doorbell with ID {doorbell_id} not found"}
                else:
                    all_devices = await client.get_devices()
                    doorbells = [d for d in all_devices if d.get("type") == "doorbell"]
                    if not doorbells:
                        return {"success": False, "error": "No doorbells found in system"}
                    doorbell = doorbells[0]

                did = doorbell["id"]
                return {
                    "success": False,
                    "error": "Direct stream URLs are retired; Ring video is WebRTC-only.",
                    "doorbell_id": did,
                    "doorbell_name": doorbell.get("name"),
                    "requested_quality": quality,
                    "webrtc": {
                        "websocket": f"/api/v1/devices/{did}/stream/webrtc",
                        "rest_offer": "/api/v1/webrtc/offer",
                        "rest_candidate": "/api/v1/webrtc/candidate",
                    },
                    "hint": _WEBRTC_HINT.format(id=did),
                }

        except Exception as e:
            logger.error("Error starting live stream: %s", str(e))
            return {"success": False, "error": str(e)}

    @app.tool(
        name="answer_doorbell_call",
        description="Answer an active doorbell call with two-way audio communication",
        annotations={"readOnlyHint": False, "idempotentHint": False},
    )
    async def answer_doorbell_call(
        doorbell_id: Annotated[
            str | None, Field(description="Specific doorbell ID (uses first doorbell if omitted).")
        ] = None,
        enable_two_way_audio: Annotated[
            bool, Field(description="Kept for compatibility; two-way audio is unsupported.")
        ] = True,
        auto_record: Annotated[bool, Field(description="Kept for compatibility; recording is unsupported.")] = True,
    ) -> dict[str, Any]:
        """Two-way audio is not implemented in this backend (matches the REST
        intercom endpoints, which answer 501). Returns an explicit unsupported
        error - use the Ring app to talk to visitors.

        ## Return Format
        {"success": false, "error": "Two-way audio is not implemented ..."}

        ## Examples
        await answer_doorbell_call()
        """
        try:
            async with RingClient() as client:
                if doorbell_id:
                    doorbell = await client.get_device(doorbell_id)
                    if not doorbell:
                        return {"success": False, "error": f"Doorbell with ID {doorbell_id} not found"}
                else:
                    all_devices = await client.get_devices()
                    if not [d for d in all_devices if d.get("type") == "doorbell"]:
                        return {"success": False, "error": "No doorbells found in system"}
            return {
                "success": False,
                "error": "Two-way audio is not implemented in this backend. Use the Ring app for now.",
                "unsupported": True,
            }
        except Exception as e:
            logger.error("Error answering doorbell call: %s", str(e))
            return {"success": False, "error": str(e)}

    @app.tool(
        name="get_visitor_history",
        description="Get comprehensive visitor history with snapshots and event details",
        annotations=_READ_ONLY,
    )
    async def get_visitor_history(
        hours: Annotated[int, Field(description="Hours of history to retrieve.", ge=1, le=720)] = 24,
        include_snapshots: Annotated[bool, Field(description="Attach per-device snapshot endpoint hints.")] = True,
        motion_only: Annotated[bool, Field(description="Only motion-kind events.")] = False,
    ) -> dict[str, Any]:
        """Get visitor history from real device events.

        ## Return Format
        {"success": true, "message": "N event(s) ...", "visitor_events": [...], "summary": {...},
         "frequent_visitors": [...], "hourly_activity_pattern": [...]}

        ## Examples
        await get_visitor_history()
        await get_visitor_history(hours=6, motion_only=True)
        """
        try:
            async with RingClient() as client:
                all_devices = await client.get_devices()
                doorbells = [d for d in all_devices if d.get("type") == "doorbell"]
                if not doorbells:
                    return {"success": False, "error": "No doorbells found in system"}

                end_time = datetime.now(UTC)
                start_time = end_time - timedelta(hours=hours)

                all_events: list[dict[str, Any]] = []
                for doorbell in doorbells:
                    try:
                        events = await client.get_device_events(doorbell["id"], limit=min(max(hours * 2, 10), 100))
                    except DeviceNotFoundError:
                        continue
                    for event in events:
                        try:
                            created = datetime.fromisoformat(str(event.get("created_at", "")))
                        except ValueError:
                            continue
                        if created < start_time:
                            continue
                        if motion_only and event.get("kind") != "motion":
                            continue
                        entry: dict[str, Any] = {
                            "id": event.get("id"),
                            "timestamp": event.get("created_at"),
                            "event_type": event.get("kind", "unknown"),
                            "answered": event.get("answered", False),
                            "recording_status": event.get("recording_status"),
                            "doorbell_id": doorbell["id"],
                            "doorbell_name": doorbell.get("name"),
                        }
                        if include_snapshots:
                            entry["snapshot_endpoint"] = f"/api/v1/snapshot/{doorbell['id']}"
                        all_events.append(entry)

                all_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

                event_types: dict[str, int] = {}
                hourly_activity = [0] * 24
                for event in all_events:
                    event_types[event.get("event_type", "unknown")] = (
                        event_types.get(event.get("event_type", "unknown"), 0) + 1
                    )
                    try:
                        hourly_activity[datetime.fromisoformat(event["timestamp"]).hour] += 1
                    except (ValueError, TypeError, KeyError):
                        logger.debug("Skipping event without parseable timestamp")

                max_activity = max(hourly_activity) if hourly_activity else 0
                peak_hours = [f"{h:02d}:00" for h, a in enumerate(hourly_activity) if a == max_activity and a > 0]

                frequent_visitors = []
                if len(all_events) > 5:
                    time_clusters: dict[str, int] = {}
                    for event in all_events:
                        try:
                            et = datetime.fromisoformat(event["timestamp"])
                            slot = f"{et.hour:02d}:{et.minute // 15 * 15:02d}"
                            time_clusters[slot] = time_clusters.get(slot, 0) + 1
                        except (ValueError, TypeError, KeyError):
                            continue
                    for slot, count in time_clusters.items():
                        if count >= 3:
                            frequent_visitors.append(
                                {
                                    "time_pattern": f"Around {slot}",
                                    "visit_count": count,
                                    "pattern_type": "regular_timing",
                                }
                            )

                summary = {
                    "total_events": len(all_events),
                    "event_types": event_types,
                    "time_period_hours": hours,
                    "active_doorbells": len(doorbells),
                    "peak_activity_hours": peak_hours,
                    "busiest_hour": f"{hourly_activity.index(max_activity):02d}:00" if max_activity > 0 else None,
                    "average_events_per_hour": round(len(all_events) / hours, 1) if hours > 0 else 0,
                }

                return {
                    "success": True,
                    "message": f"{len(all_events)} event(s) in the last {hours}h",
                    "time_range": {"start": start_time.isoformat(), "end": end_time.isoformat(), "hours": hours},
                    "visitor_events": all_events,
                    "summary": summary,
                    "frequent_visitors": frequent_visitors,
                    "hourly_activity_pattern": hourly_activity,
                    "filters_applied": {"motion_only": motion_only, "include_snapshots": include_snapshots},
                }

        except Exception as e:
            logger.error("Error getting visitor history: %s", str(e))
            return {"success": False, "error": str(e)}

    @app.tool(
        name="configure_motion_detection",
        description="Configure motion detection settings for Ring doorbell with advanced options",
        annotations={"readOnlyHint": False, "idempotentHint": True},
    )
    async def configure_motion_detection(
        doorbell_id: Annotated[
            str | None, Field(description="Specific doorbell ID (uses first doorbell if omitted).")
        ] = None,
        sensitivity: Annotated[
            Literal["low", "medium", "high"], Field(description="Desired sensitivity level.")
        ] = "medium",
        motion_zones: Annotated[
            list[dict[str, Any]] | None, Field(description="Desired zones (name + coordinates each).")
        ] = None,
        smart_alerts: Annotated[bool, Field(description="Desired smart-alert state.")] = True,
        schedule_enabled: Annotated[bool, Field(description="Desired schedule state.")] = False,
    ) -> dict[str, Any]:
        """Motion configuration is not exposed by the Ring API wrapper - adjust
        sensitivity and zones in the Ring app. The tool verifies the doorbell
        exists and echoes the requested configuration for copy-paste.

        ## Return Format
        {"success": false, "error": "Motion configuration is not exposed ...",
         "requested_configuration": {...}}

        ## Examples
        await configure_motion_detection(sensitivity="low")
        """
        if motion_zones:
            for zone in motion_zones:
                if not all(key in zone for key in ["name", "coordinates"]):
                    return {"success": False, "error": f"Invalid motion zone (needs name + coordinates): {zone!r}"}
        try:
            async with RingClient() as client:
                if doorbell_id:
                    doorbell = await client.get_device(doorbell_id)
                    if not doorbell:
                        return {"success": False, "error": f"Doorbell with ID {doorbell_id} not found"}
                else:
                    all_devices = await client.get_devices()
                    matches = [d for d in all_devices if d.get("type") == "doorbell"]
                    if not matches:
                        return {"success": False, "error": "No doorbells found in system"}
                    doorbell = matches[0]
                return {
                    "success": False,
                    "error": "Motion configuration is not exposed by the Ring API wrapper; adjust it in the Ring app.",
                    "unsupported": True,
                    "doorbell_id": doorbell["id"],
                    "doorbell_name": doorbell.get("name"),
                    "requested_configuration": {
                        "sensitivity": sensitivity,
                        "smart_alerts": smart_alerts,
                        "schedule_enabled": schedule_enabled,
                        "motion_zones": motion_zones or [],
                    },
                }
        except Exception as e:
            logger.error("Error configuring motion detection: %s", str(e))
            return {"success": False, "error": str(e)}
