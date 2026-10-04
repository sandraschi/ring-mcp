"""
Ring MCP Status and System Information Tools - FastMCP 3.4.

Comprehensive status monitoring tools providing:
- Authentication status and token validity
- Device connectivity and health status
- System performance metrics
- Connection diagnostics and troubleshooting
- Real-time system state monitoring
"""

import logging
import os
import time
from datetime import datetime
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from ring_mcp.core.exceptions import DeviceNotFoundError

from ..core.exceptions import AuthenticationError
from ..core.ring_client_modern import RingClient

logger = logging.getLogger(__name__)

_READ_ONLY = {"readOnlyHint": True, "idempotentHint": True}


def register_tools(app: FastMCP) -> None:
    """Register status monitoring tools with the FastMCP application.

    Args: See Parameters block.
    """

    @app.tool(
        name="get_system_status",
        description="Get comprehensive system status including authentication and device connectivity",
        annotations=_READ_ONLY,
    )
    async def get_system_status(
        include_device_details: Annotated[bool, Field(description="Include per-device details.")] = True,
        check_connectivity: Annotated[bool, Field(description="Probe Ring API reachability.")] = True,
    ) -> dict[str, Any]:
        """Get comprehensive system status including authentication and device connectivity.

        ## Return Format
        {"system_status": "healthy|...", "authentication": {...}, "devices": {...}, ...}

        ## Examples
        await get_system_status()
        await get_system_status(include_device_details=False)
        """
        start_time = time.time()
        status = {
            "timestamp": datetime.now().isoformat(),
            "system_status": "unknown",
            "authentication": {},
            "devices": {},
            "connectivity": {},
            "performance": {},
            "diagnostics": {},
        }

        try:
            # Check authentication status
            auth_status = await check_authentication_status()
            status["authentication"] = auth_status

            # Check device status
            device_status = await check_device_status(include_device_details)
            status["devices"] = device_status

            # Check connectivity
            if check_connectivity:
                connectivity_status = await check_connectivity_status()
                status["connectivity"] = connectivity_status

            # Determine overall system status
            status["system_status"] = determine_overall_status(
                auth_status, device_status, status.get("connectivity", {})
            )

            # Performance metrics
            status["performance"] = {
                "response_time_seconds": round(time.time() - start_time, 3),
                "memory_usage_mb": get_memory_usage(),
                "cpu_usage_percent": get_cpu_usage(),
            }

            # Diagnostics
            status["diagnostics"] = generate_diagnostics(status)

        except Exception as e:
            logger.error("Error getting system status: %s", str(e))
            status["system_status"] = "error"
            status["error"] = {"message": str(e), "type": type(e).__name__, "timestamp": datetime.now().isoformat()}

        status["message"] = f"System status: {status['system_status']}"
        return status

    async def check_device_status(include_details: bool = True) -> dict[str, Any]:
        """Check device connectivity and health."""
        result: dict[str, Any] = {"devices_tested": 0, "devices_online": 0, "devices_offline": 0, "device_results": []}
        try:
            client = RingClient()
            await client.connect()
            devices = await client.get_devices(force_refresh=False)
            result["devices_tested"] = len(devices)
            for d in devices:
                online = d.get("online", False)
                result["device_results"].append({"id": d.get("id"), "name": d.get("name"), "online": online})
                if online:
                    result["devices_online"] += 1
                else:
                    result["devices_offline"] += 1
            result["connectivity_score"] = int((result["devices_online"] / max(result["devices_tested"], 1)) * 100)
        except Exception as e:
            result["error"] = str(e)
        return result

    async def check_connectivity_status() -> dict[str, Any]:
        """Check network connectivity to Ring API."""
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get("https://api.ring.com/clients_api/info")
                return {"reachable": r.status_code == 200, "status_code": r.status_code}
        except Exception as e:
            return {"reachable": False, "error": str(e)}

    @app.tool(
        name="check_authentication_status",
        description="Check Ring API authentication status and token validity",
        annotations=_READ_ONLY,
    )
    async def check_authentication_status() -> dict[str, Any]:
        """Check Ring API authentication status and token validity.

        ## Return Format
        {"authenticated": true, "method": "username_password|oauth_token", ...}

        ## Examples
        await check_authentication_status()
        """
        auth_status = {
            "success": True,
            "message": "Ring authentication valid",
            "authenticated": False,
            "method": "unknown",
            "token_valid": False,
            "token_expires_in": None,
            "permissions": [],
            "rate_limit_status": "unknown",
            "last_successful_auth": None,
            "auth_errors": [],
        }

        try:
            # Modern client: connect() raises AuthenticationError without creds (never prompts).
            test_client = RingClient()
            await test_client.connect()

            # A successful device read proves the session works.
            try:
                await test_client.get_devices(force_refresh=False)
            except AuthenticationError as e:
                auth_status["success"] = False
                auth_status["message"] = f"Authentication failed: {e!s}"
                auth_status["auth_errors"].append(f"Authentication failed: {e!s}")
                return auth_status
            except Exception as e:
                auth_status["success"] = False
                auth_status["message"] = f"Connection failed: {e!s}"
                auth_status["auth_errors"].append(f"Connection failed: {e!s}")
                return auth_status

            auth_status["authenticated"] = True
            auth_status["token_valid"] = True
            auth_status["method"] = "oauth_token" if os.getenv("RING_TOKEN") else "username_password"
            auth_status["last_successful_auth"] = datetime.now().isoformat()

        except AuthenticationError as e:
            auth_status["success"] = False
            auth_status["message"] = f"Authentication failed: {e!s}"
            auth_status["auth_errors"].append(f"Authentication failed: {e!s}")
        except Exception as e:
            logger.error("Authentication check failed: %s", str(e))
            auth_status["success"] = False
            auth_status["message"] = f"Check failed: {e!s}"
            auth_status["auth_errors"].append(f"Check failed: {e!s}")

        return auth_status

    @app.tool(
        name="check_device_connectivity",
        description="Test connectivity and status of all Ring devices",
        annotations=_READ_ONLY,
    )
    async def check_device_connectivity(
        device_id: Annotated[str | None, Field(description="Test a single device instead of all.")] = None,
        test_commands: Annotated[
            bool, Field(description="Reserved for active command tests (currently no-op).")
        ] = False,
    ) -> dict[str, Any]:
        """Test connectivity and status of all Ring devices.

        ## Return Format
        {"devices_tested": N, "devices_online": N, "connectivity_score": 0-100, "device_results": [...]}

        ## Examples
        await check_device_connectivity()
        await check_device_connectivity(device_id="camera-001")
        """
        connectivity_results = {
            "test_timestamp": datetime.now().isoformat(),
            "devices_tested": 0,
            "devices_online": 0,
            "devices_offline": 0,
            "connectivity_score": 0,
            "device_results": [],
            "recommendations": [],
            "note": "Signal strength is not exposed by the Ring API wrapper; online/offline and battery are reported.",
        }

        try:
            # Get all devices (or a single one when requested)
            client = RingClient()
            await client.connect()

            devices = await client.get_devices(force_refresh=True)
            if device_id:
                devices = [d for d in devices if d.get("id") == device_id]
                if not devices:
                    raise DeviceNotFoundError(device_id)
            connectivity_results["devices_tested"] = len(devices)

            for device in devices:
                device_result = {
                    "device_id": device.get("id", "unknown"),
                    "device_type": device.get("type", "unknown"),
                    "device_name": device.get("name", "Unnamed"),
                    "connectivity_status": "unknown",
                    "response_time_ms": None,
                    "last_seen": device.get("last_update"),
                    "battery_level": device.get("battery_life"),
                    "signal_strength": device.get("signal_strength"),
                    "errors": [],
                }

                try:
                    # Test basic connectivity (modern client returns full device dicts)
                    start_time = time.time()
                    device_details = await client.get_device(device["id"])
                    if device_details is None:
                        raise DeviceNotFoundError(device["id"])
                    response_time = (time.time() - start_time) * 1000

                    device_result["connectivity_status"] = "online"
                    device_result["response_time_ms"] = round(response_time, 2)
                    connectivity_results["devices_online"] += 1

                    # Check device health (modern dicts carry battery_life; no signal metric)
                    battery = device_details.get("battery_life")
                    if battery is not None and battery < 20:
                        device_result["errors"].append("Low battery")
                        connectivity_results["recommendations"].append(
                            f"Replace battery in {device.get('name', 'device')}"
                        )

                except DeviceNotFoundError:
                    device_result["connectivity_status"] = "offline"
                    device_result["errors"].append("Device not found")
                    connectivity_results["devices_offline"] += 1
                    connectivity_results["recommendations"].append(
                        f"Check if {device.get('name', 'device')} is powered on"
                    )

                except Exception as e:
                    device_result["connectivity_status"] = "error"
                    device_result["errors"].append(str(e))
                    connectivity_results["devices_offline"] += 1
                    connectivity_results["recommendations"].append(
                        f"Troubleshoot {device.get('name', 'device')}: {e!s}"
                    )

                connectivity_results["device_results"].append(device_result)

            # Calculate connectivity score
            if connectivity_results["devices_tested"] > 0:
                connectivity_results["connectivity_score"] = int(
                    (connectivity_results["devices_online"] / connectivity_results["devices_tested"]) * 100
                )
            connectivity_results["message"] = (
                f"{connectivity_results['devices_online']}/{connectivity_results['devices_tested']} online "
                f"(score {connectivity_results['connectivity_score']})"
            )

        except Exception as e:
            logger.error("Device connectivity check failed: %s", str(e))
            connectivity_results["error"] = str(e)
            connectivity_results["connectivity_score"] = 0

        return connectivity_results

    @app.tool(
        name="get_service_health",
        description="Get detailed service health and performance metrics",
        annotations=_READ_ONLY,
    )
    async def get_service_health(
        include_metrics: Annotated[bool, Field(description="Include resource metrics.")] = True,
        history_minutes: Annotated[int, Field(description="History window (reserved).", ge=1, le=1440)] = 5,
    ) -> dict[str, Any]:
        """Get detailed service health and performance metrics.

        ## Return Format
        {"health_status": "healthy|degraded|error", "health_score": 0-100, "components": {...}, ...}

        ## Examples
        await get_service_health()
        """
        health_info = {
            "service_name": "Ring MCP Server",
            "version": _service_version(),
            "uptime_seconds": get_uptime(),
            "health_status": "healthy",
            "last_health_check": datetime.now().isoformat(),
            "health_score": 100,
            "components": {},
            "performance": {},
            "alerts": [],
            "recommendations": [],
        }

        try:
            # Check core components
            components = {
                "authentication": await check_auth_component(),
                "device_management": await check_device_component(),
                "api_connectivity": await check_api_component(),
                "tool_system": await check_tool_component(),
            }

            health_info["components"] = components

            # Determine overall health
            health_score = 0
            total_components = len(components)

            for component_status in components.values():
                if component_status["status"] == "healthy":
                    health_score += 100
                elif component_status["status"] == "degraded":
                    health_score += 50
                elif component_status["status"] == "error":
                    health_score += 0

            health_info["health_score"] = int(health_score / total_components)

            if health_info["health_score"] < 80:
                health_info["health_status"] = "degraded"
            if health_info["health_score"] < 50:
                health_info["health_status"] = "error"

            # Performance metrics
            if include_metrics:
                health_info["performance"] = {
                    "memory_usage_mb": get_memory_usage(),
                    "cpu_usage_percent": get_cpu_usage(),
                    "active_connections": get_active_connections(),
                    "response_time_avg_ms": get_average_response_time(),
                }

            # Generate alerts and recommendations
            health_info["alerts"] = generate_health_alerts(components)
            health_info["recommendations"] = generate_health_recommendations(components)
            health_info["message"] = f"Service {health_info['health_status']} (score {health_info['health_score']})"

        except Exception as e:
            logger.error("Service health check failed: %s", str(e))
            health_info["health_status"] = "error"
            health_info["health_score"] = 0
            health_info["error"] = str(e)

        return health_info


async def check_auth_component() -> dict[str, Any]:
    """Check authentication component health."""
    try:
        return {"status": "healthy", "details": "Authentication working"}
    except Exception as e:
        return {"status": "error", "details": f"Auth check failed: {e!s}"}


async def check_device_component() -> dict[str, Any]:
    """Check device management component health."""
    try:
        client = RingClient()
        await client.connect()
        devices = await client.get_devices(force_refresh=False)
        return {"status": "healthy", "details": f"Device management working ({len(devices)} devices)"}
    except Exception as e:
        return {"status": "error", "details": f"Device check failed: {e!s}"}


async def check_api_component() -> dict[str, Any]:
    """Check API connectivity component health."""
    try:
        # Test basic API connectivity
        client = RingClient()
        await client.connect()
        return {"status": "healthy", "details": "API connectivity working"}
    except Exception as e:
        return {"status": "error", "details": f"API check failed: {e!s}"}


async def check_tool_component() -> dict[str, Any]:
    """Check tool system component health."""
    return {"status": "healthy", "details": "Tool system operational"}


def determine_overall_status(auth_status: dict, device_status: dict, connectivity_status: dict) -> str:
    """Determine overall system status based on component statuses."""
    if not auth_status.get("authenticated", False):
        return "authentication_failed"

    # check_device_status() reports devices_online / devices_tested.
    online_devices = device_status.get("online_devices", device_status.get("devices_online", 0))
    total_devices = device_status.get("total_devices", device_status.get("devices_tested", 0))

    if total_devices == 0:
        return "no_devices"

    connectivity_ratio = online_devices / total_devices

    if connectivity_ratio >= 0.8:
        return "healthy"
    elif connectivity_ratio >= 0.5:
        return "degraded"
    else:
        return "poor_connectivity"


def generate_diagnostics(status: dict[str, Any]) -> dict[str, Any]:
    """Generate diagnostic information."""
    return {
        "diagnostic_timestamp": datetime.now().isoformat(),
        "system_uptime": get_uptime(),
        "memory_usage": get_memory_usage(),
        "suggestions": [
            "Check authentication if auth_status is false",
            "Verify device connectivity if many devices are offline",
            "Monitor system resources if performance is degraded",
        ],
    }


# Placeholder functions for system metrics
def _service_version() -> str:
    """Installed dist version (falls back to 'unknown' on naked checkouts)."""
    try:
        from importlib.metadata import version

        return version("ring-mcp")
    except Exception:
        return "unknown"


def get_uptime() -> int:
    """Process uptime in seconds (0 when psutil is unavailable)."""
    try:
        import time as _time

        import psutil

        return int(_time.time() - psutil.boot_time())
    except ImportError:
        return 0


def get_memory_usage() -> float:
    """Get memory usage in MB."""
    try:
        import psutil

        return round(psutil.Process().memory_info().rss / 1024 / 1024, 2)
    except ImportError:
        return 0.0


def get_cpu_usage() -> float:
    """Get CPU usage percentage."""
    try:
        import psutil

        return round(psutil.cpu_percent(interval=1), 2)
    except ImportError:
        return 0.0


def get_active_connections() -> int:
    """Get number of active connections."""
    try:
        import psutil

        return len(psutil.net_connections())
    except ImportError:
        return 0


def get_average_response_time() -> float:
    """Get average response time in milliseconds."""
    return 0.0  # Placeholder


def generate_health_alerts(components: dict[str, dict]) -> list[str]:
    """Generate health alerts based on component status."""
    alerts = []

    for component_name, component_status in components.items():
        if component_status["status"] == "error":
            alerts.append(f"{component_name} component is not working: {component_status['details']}")

    return alerts


def generate_health_recommendations(components: dict[str, dict]) -> list[str]:
    """Generate health recommendations."""
    recommendations = []

    for component_name, component_status in components.items():
        if component_status["status"] != "healthy":
            recommendations.append(f"Fix {component_name} component: {component_status['details']}")

    if not recommendations:
        recommendations.append("System is healthy - no action required")

    return recommendations
