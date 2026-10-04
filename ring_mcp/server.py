"""
FastMCP 3.4+ server for Ring MCP.

This module provides a FastMCP server implementation for controlling Ring devices
with composition and proxy capabilities. Aligned to FastMCP 3.4+ (sampling,
agentic workflows, prompts).
"""

import logging
import os
import time
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.server import create_proxy
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from pydantic import BaseModel, Field

from .core.ring_client_modern import RingClient


def create_fastapi_app_with_docs() -> FastAPI:
    """Create a FastAPI app with documentation enabled."""
    return FastAPI(
        title="Ring MCP API",
        description="Ring Security System Management API - FastAPI Documentation",
        version="1.0.4",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )


# Configure structured logging with file output for monitoring
import logging.config
from pathlib import Path

from .core.exceptions import (
    AuthenticationError,
    DeviceNotFoundError,
    StreamingError,
)

# Create log directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Logging configuration for file output
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
        "detailed": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "file_info": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": log_dir / "ring_mcp_info.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
        "file_error": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": log_dir / "ring_mcp_error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "detailed",
            "stream": "ext://sys.stderr",  # Use stderr for console output
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["file_info", "file_error", "console"],
    },
    "loggers": {
        "ring_mcp": {
            "level": "INFO",
            "handlers": ["file_info", "file_error", "console"],
            "propagate": False,
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["file_info", "console"],
            "propagate": False,
        },
    },
}

# Apply logging configuration
logging.config.dictConfig(LOGGING_CONFIG)

# Configure structlog to use the configured loggers
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Port management with graceful termination of previous instances
from ring_mcp.core.port_manager import get_ring_mcp_port

RING_MCP_PORT = get_ring_mcp_port()

# Initialize FastMCP 3.4+
app = FastMCP(
    name="Ring Security",
    version="1.0.4",
)

_bridge_proxies: list[str] = []
bridge_urls = os.getenv("MCP_BRIDGE_URLS", "")
if bridge_urls:
    for url in bridge_urls.split(","):
        url = url.strip()
        if url:
            try:
                app.add_provider(create_proxy(url))
                _bridge_proxies.append(url)
            except Exception as bridge_err:
                logger.warning("Skipping unreachable bridge %s: %s", url, bridge_err)

# Prometheus metrics
ring_api_calls_total = Counter("ring_api_calls_total", "Total Ring API calls", ["endpoint", "status"])
ring_api_duration = Histogram("ring_api_duration_seconds", "Ring API call duration", ["endpoint"])
ring_device_status = Gauge("ring_device_status", "Ring device status", ["device_id", "device_type", "status"])
ring_device_battery = Gauge("ring_device_battery_percent", "Ring device battery level", ["device_id", "device_type"])
ring_device_online = Gauge("ring_device_online", "Ring device online status", ["device_id", "device_type"])
ring_security_armed = Gauge("ring_security_armed", "Security system armed status", ["location"])
ring_tool_calls_total = Counter("ring_tool_calls_total", "Total MCP tool calls", ["tool_name"])
ring_tool_duration = Histogram("ring_tool_duration_seconds", "MCP tool execution time", ["tool_name"])
ring_active_connections = Gauge("ring_active_connections", "Active MCP connections")


# Models for request/response validation
class DeviceInfo(BaseModel):
    """Model for device information."""

    id: str = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Device name")
    type: str = Field(..., description="Device type/family")
    model: str = Field(..., description="Device model")
    firmware: str | None = Field(None, description="Device firmware version")
    battery_life: int | None = Field(None, description="Battery percentage (0-100)")
    online: bool = Field(..., description="Whether the device is currently online")
    address: str | None = Field(None, description="Device location/address")
    timezone: str | None = Field(None, description="Device timezone")
    has_subscription: bool = Field(False, description="Whether the device has an active subscription")
    last_update: str = Field(..., description="ISO timestamp of last update")


class EventInfo(BaseModel):
    """Model for device event information."""

    id: str = Field(..., description="Event identifier")
    created_at: str = Field(..., description="Event timestamp in ISO format")
    answered: bool = Field(False, description="Whether the event was answered")
    kind: str | None = Field(None, description="Type of event")
    recording_status: str | None = Field(None, description="Status of recording if available")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: bool = Field(True, description="Indicates this is an error response")
    message: str = Field(..., description="Error message")
    code: str | None = Field(None, description="Error code if available")


# Helper function to handle errors
def handle_error(e: Exception) -> dict[str, Any]:
    """Convert exceptions to error responses."""
    if isinstance(e, AuthenticationError):
        status_code = 401
        error_code = "authentication_error"
    elif isinstance(e, DeviceNotFoundError):
        status_code = 404
        error_code = "device_not_found"
    elif isinstance(e, StreamingError):
        status_code = 503
        error_code = "streaming_error"
    else:
        status_code = 500
        error_code = "internal_error"

    logger.exception("Ring MCP Error: %s [%s]", str(e), error_code)

    return {"error": True, "message": str(e), "code": error_code, "status_code": status_code}


def track_ring_api_call(endpoint: str, success: bool = True):
    """Track Ring API calls for metrics."""
    status = "success" if success else "error"
    ring_api_calls_total.labels(endpoint=endpoint, status=status).inc()
    ring_api_duration.labels(endpoint=endpoint).observe(time.time())


def track_tool_call(tool_name: str):
    """Decorator to track MCP tool calls."""

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        async def wrapper(*args, **kwargs):
            ring_tool_calls_total.labels(tool_name=tool_name).inc()
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                ring_tool_duration.labels(tool_name=tool_name).observe(time.time() - start_time)
                return result
            except Exception:
                ring_tool_duration.labels(tool_name=tool_name).observe(time.time() - start_time)
                raise

        return wrapper

    return decorator


# Global Ring client instance
_ring_client: RingClient | None = None


def get_ring_client() -> RingClient:
    """Get or create a Ring client instance."""
    global _ring_client
    if _ring_client is None:
        _ring_client = RingClient()
    return _ring_client


def register_ring_tools(app: FastMCP, ring_client: RingClient | None = None) -> None:
    """Register Ring MCP tools (composition/legacy entry point).

    Single-surface rule: this delegates to register_all_tools_on_app() so every
    transport serves the same tools. Legacy names previously defined here map to:
    get_devices -> list_devices; get_device_details/get_device_events ->
    get_security_system_status and device tools; get_live_stream_url ->
    get_doorbell_live_stream (WebRTC handoff); set_arm_status ->
    arm_security_system/disarm_security_system; trigger_chime -> device chime
    via REST; health_check -> get_service_health/monitor_system_health.
    See docs/TOOLS.md for the served surface.
    """
    register_all_tools_on_app(app, ring_client)


def register_all_tools_on_app(app: FastMCP, ring_client: RingClient | None = None):
    """Register all Ring MCP tools on a specific app instance."""
    try:
        from .tools import (
            automation_tools,
            camera_tools,
            doorbell_tools,
            fire_safety_tools,
            help_tool,
            monitoring_tools,
            security_system_tools,
            status_tool,
        )

        # Register tools from each module
        automation_tools.register_tools(app)
        camera_tools.register_tools(app)
        doorbell_tools.register_tools(app)
        fire_safety_tools.register_tools(app)
        help_tool.register_tools(app)
        monitoring_tools.register_tools(app)
        security_system_tools.register_tools(app)
        status_tool.register_tools(app)

        # Register shutdown tool
        @app.tool(
            name="ring_shutdown",
            description="Gracefully shut down the Ring MCP server",
            annotations={"readOnlyHint": False, "idempotentHint": False, "destructiveHint": True},
            output_schema={
                "type": "object",
                "required": ["success"],
                "properties": {"success": {"type": "boolean"}, "message": {"type": "string"}},
            },
        )
        async def ring_shutdown() -> dict:
            """Gracefully shut down the Ring MCP server.

            ## Return Format
            {"success": true, "message": "Server shutting down..."}

            ## Examples
            await ring_shutdown()
            """
            import asyncio
            import os

            logger.warning("Ring MCP server shutdown requested via tool")
            asyncio.get_event_loop().call_later(1, os._exit, 0)
            return {"success": True, "message": "Server shutting down..."}

        # Device inventory - MCP surface for what REST exposes at GET /api/v1/devices.
        # (NOTE: register_ring_tools() below defines a get_devices variant on the
        # legacy global app; this is the served create_app() surface.)
        @app.tool(
            name="list_devices",
            description="List all Ring devices with online status and battery",
            annotations={"readOnlyHint": True, "idempotentHint": True},
            output_schema={
                "type": "object",
                "required": ["success"],
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "error": {"type": "string"},
                    "count": {"type": "integer"},
                    "devices": {"type": "array"},
                },
            },
        )
        async def list_devices(device_type: str = "all") -> dict[str, Any]:
            """List all Ring devices with online status and battery.

            ## Return Format
            {"success": true, "message": "Found N device(s)", "count": N, "devices": [...]}

            ## Examples
            await list_devices()
            await list_devices(device_type="camera")
            """
            try:
                async with RingClient() as client:
                    devices = await client.get_devices()
                if device_type != "all":
                    needle = device_type.lower()
                    devices = [d for d in devices if needle in str(d.get("type", "")).lower()]
                return {
                    "success": True,
                    "message": f"Found {len(devices)} device(s)",
                    "count": len(devices),
                    "devices": devices,
                }
            except Exception as e:
                logger.error("list_devices failed: %s", str(e))
                return {"success": False, "error": str(e)}

        @app.tool(
            app=True,
            name="show_devices_card",
            description="Show all Ring devices as a rich card",
            annotations={"readOnlyHint": True, "idempotentHint": True},
            output_schema={
                "type": "object",
                "required": ["content"],
                "properties": {"content": {"type": "string"}},
            },
        )
        async def show_devices_card() -> dict:
            """Show all Ring devices as a rich in-chat Prefab card.

            ## Return Format
            {"content": "...", "structured_content": {"prefab": true, "title": "...", "sections": [...]}}

            ## Examples
            await show_devices_card()
            """
            try:
                from prefab_ui import PrefabApp
                from prefab_ui.components import Badge, Div, Heading, Row, Text

                async with RingClient() as client:
                    devices = await client.get_devices()
                with PrefabApp(title="Ring Devices") as app_card:
                    Heading(f"{len(devices)} Devices")
                    for d in devices:
                        online = d.get("online", False)
                        bat = d.get("battery_life")
                        status = "Online" if online else "Offline"
                        if bat is not None:
                            status += f" | Battery: {bat}%"
                        with Div():
                            with Row(gap=2, align="center", justify="between"):
                                Text(d.get("name", "?"))
                                Badge(status, variant="success" if online else "destructive")
                return {"content": f"Found {len(devices)} devices", "structured_content": app_card}
            except Exception as e:
                return {"content": f"Error: {e!s}"}

        @app.tool(
            app=True,
            name="show_health_card",
            description="Show Ring MCP health as a rich card",
            annotations={"readOnlyHint": True, "idempotentHint": True},
            output_schema={
                "type": "object",
                "required": ["content"],
                "properties": {"content": {"type": "string"}},
            },
        )
        async def show_health_card() -> dict:
            """Show Ring MCP service health as a rich in-chat Prefab card.

            ## Return Format
            {"content": "...", "structured_content": {"prefab": true, "title": "...", "sections": [...]}}

            ## Examples
            await show_health_card()
            """
            try:
                from prefab_ui import PrefabApp
                from prefab_ui.components import Badge, Div, Heading, Row, Text

                with PrefabApp(title="Ring MCP Health") as app_card:
                    Heading("System Health")
                    try:
                        async with RingClient() as client:
                            await client.get_devices()
                        connected = True
                    except Exception:
                        connected = False
                    with Div():
                        with Row(gap=2, align="center", justify="between"):
                            Text("API Connectivity")
                            Badge(
                                "Connected" if connected else "Disconnected",
                                variant="success" if connected else "destructive",
                            )
                return {"content": "Ring MCP health check", "structured_content": app_card}
            except Exception as e:
                return {"content": f"Error: {e!s}"}

        # Prompts: guided workflows over real tool names (served surface only).
        @app.prompt(
            name="ring-security-check",
            description="Guided daily Ring security review (status, alerts, batteries).",
        )
        async def ring_security_check() -> str:
            """Daily Ring security review workflow."""
            return (
                "Run a daily Ring security review:\n"
                "1. Call get_security_system_status() for mode, devices, and active alerts.\n"
                "2. If devices are offline, call check_device_connectivity() for details.\n"
                "3. If batteries are low, note replacements from monitor_system_health().\n"
                "4. Summarize: mode, offline devices, low batteries, recent activity."
            )

        @app.prompt(
            name="ring-incident-triage",
            description="Triage a Ring security event (history, devices, emergency).",
        )
        async def ring_incident_triage() -> str:
            """Security incident triage workflow."""
            return (
                "Triage a Ring security event:\n"
                "1. Call get_security_history(hours=6) and get_visitor_history(hours=6).\n"
                "2. Call get_doorbell_status() and get_camera_status() for device state.\n"
                "3. For genuine emergencies only, call trigger_emergency_protocol().\n"
                "4. Report what happened, which devices saw it, and what was armed."
            )

        # Resources: live data snapshots by URI.
        @app.resource("ring://devices", description="Live Ring device inventory as JSON.")
        async def ring_devices_resource() -> str:
            """Live Ring device inventory."""
            import json

            async with RingClient() as client:
                devices = await client.get_devices()
            return json.dumps(devices)

        @app.resource("ring://health", description="Ring MCP service health as JSON.")
        async def ring_health_resource() -> str:
            """Service health snapshot (no credentials required for the shape)."""
            import json

            try:
                async with RingClient() as client:
                    devices = await client.get_devices()
                return json.dumps({"api_connected": True, "devices_accessible": len(devices)})
            except Exception as e:
                return json.dumps({"api_connected": False, "error": str(e)})

        logger.info("All Ring MCP tools registered successfully on app instance")

    except Exception as e:
        logger.error("Failed to register tools on app: %s", str(e))
        # Don't crash the server if tool registration fails
        logger.warning("App will start with limited functionality")


def register_all_tools():
    """Register all Ring MCP tools on the global app instance (for backward compatibility)."""
    register_all_tools_on_app(app)


def create_app(ring_client: RingClient | None = None) -> FastMCP:
    """Create and configure the FastMCP application with composition support.

    This function creates the main FastMCP application instance and registers
    all Ring security tools (FastMCP 3.4+: sampling, agentic workflows).

    Args:
        ring_client: Optional pre-initialized RingClient instance. If not provided,
                    a new client will be created using environment variables.

    Returns:
        Configured FastMCP application with Ring MCP and composition support
    """
    # Create a new FastMCP app instance
    new_app = FastMCP(
        name="Ring MCP Server", instructions="Comprehensive Ring Security System Management with FastMCP 3.4"
    )

    # Register all tools on the new app instance
    try:
        register_all_tools_on_app(new_app, ring_client)
        logger.info("All Ring MCP tools registered successfully on new app instance")
    except Exception as e:
        logger.error("Failed to register tools on new app: %s", str(e))
        logger.warning("New app will start with limited functionality")

    return new_app


if __name__ == "__main__":
    # Configure structured logging for FastMCP 3.4
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Configure structlog for JSON logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Start Prometheus metrics server for monitoring
    metrics_port = int(os.getenv("METRICS_PORT", "8001"))
    start_http_server(metrics_port)
    logger.info("Prometheus metrics server started", port=metrics_port)

    # Create and run the FastMCP server with stdio transport for Claude Desktop
    # The app is already configured with both stdio and HTTP transports
    logger.info("Starting Ring MCP server with FastMCP 3.4+")
    logger.info("Server will be available via stdio for Claude Desktop and HTTP for web access")
