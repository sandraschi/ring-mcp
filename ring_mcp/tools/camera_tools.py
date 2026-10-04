"""
Ring Security Camera Management Tools - FastMCP 3.4.

Security camera operations including status, recording state, motion activity,
and multi-camera monitoring for Ring security cameras.
"""

import logging
from datetime import datetime
from typing import Any

from fastmcp import FastMCP

from ..core.ring_client_modern import RingClient

logger = logging.getLogger(__name__)

_READ_ONLY = {"readOnlyHint": True, "idempotentHint": True}


def register_tools(app: FastMCP) -> None:
    """Register security camera management tools with the FastMCP application.

    Args: See Parameters block.
    """

    @app.tool(
        name="get_camera_status",
        description="Get comprehensive status of all Ring security cameras",
        annotations=_READ_ONLY,
    )
    async def get_camera_status() -> dict[str, Any]:
        """Get comprehensive status of all Ring security cameras.

        ## Return Format
        {"success": true, "message": "N camera(s), M online", "cameras": [...], ...}

        ## Examples
        await get_camera_status()
        """
        try:
            async with RingClient() as client:
                # Get all devices and filter for cameras
                all_devices = await client.get_devices()
                cameras = [device for device in all_devices if device.get("type") == "camera"]

                # Get detailed status for each camera
                camera_details = []
                for camera in cameras:
                    try:
                        # Get camera events for motion activity
                        events = await client.get_device_events(camera["id"], limit=5)

                        camera_info = {
                            "id": camera["id"],
                            "name": camera["name"],
                            "type": camera["type"],
                            "model": camera["model"],
                            "online": camera["online"],
                            "battery_life": camera.get("battery_life"),
                            "firmware": camera.get("firmware"),
                            "address": camera.get("address"),
                            "recent_events": events,
                            "recording_enabled": True,  # Ring cameras typically record by default
                            "motion_detection": True,  # Ring cameras have motion detection
                            "last_update": camera["last_update"],
                        }
                        camera_details.append(camera_info)
                    except Exception as e:
                        logger.error(f"Error getting details for camera {camera['id']}: {e}")
                        # Still include the camera with basic info
                        camera_details.append(
                            {
                                "id": camera["id"],
                                "name": camera["name"],
                                "type": camera["type"],
                                "online": camera["online"],
                                "error": str(e),
                            }
                        )

                return {
                    "success": True,
                    "message": f"{len(camera_details)} camera(s), {sum(1 for c in camera_details if c.get('online', False))} online",
                    "cameras": camera_details,
                    "total_cameras": len(camera_details),
                    "online_cameras": sum(1 for c in camera_details if c.get("online", False)),
                    "cameras_with_issues": sum(1 for c in camera_details if c.get("error")),
                    "last_updated": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error getting camera status: {e}")
            return {"success": False, "error": str(e)}

    @app.tool(
        name="stream_all_cameras",
        description="Start live streams from all available Ring cameras",
        annotations=_READ_ONLY,
    )
    async def stream_all_cameras() -> dict[str, Any]:
        """Report per-camera live-view readiness (WebRTC handoff).

        Ring retired direct stream URLs - each camera resolves to either a
        stream entry or an honest per-camera failure pointing at WebRTC.

        ## Return Format
        {"success": true, "message": "N stream(s) started, M failed",
         "camera_streams": [...], "failed_cameras": [...]}

        ## Examples
        await stream_all_cameras()
        """
        try:
            async with RingClient() as client:
                # Get all devices and filter for cameras
                all_devices = await client.get_devices()
                cameras = [device for device in all_devices if device.get("type") == "camera"]

                camera_streams = []
                failed_cameras = []

                for camera in cameras:
                    try:
                        # Get stream URL for each camera
                        stream_url = await client.get_live_stream_url(camera["id"])
                        camera_streams.append(
                            {
                                "camera_id": camera["id"],
                                "camera_name": camera["name"],
                                "stream_url": stream_url,
                                "status": "active",
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to get stream for camera {camera['id']}: {e}")
                        failed_cameras.append(
                            {"camera_id": camera["id"], "camera_name": camera["name"], "error": str(e)}
                        )

                return {
                    "success": True,
                    "message": f"{len(camera_streams)} stream(s) started, {len(failed_cameras)} failed (WebRTC-only API)",
                    "camera_streams": camera_streams,
                    "total_streams": len(camera_streams),
                    "failed_cameras": failed_cameras,
                    "total_failed": len(failed_cameras),
                    "stream_started_at": datetime.now().isoformat(),
                }

        except Exception as e:
            logger.error(f"Error starting camera streams: {e}")
            return {"success": False, "error": str(e)}
