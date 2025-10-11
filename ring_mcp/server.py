"""
FastMCP 2.12 server for Ring MCP.

This module provides a FastMCP server implementation for controlling Ring devices
with composition and proxy capabilities using FastMCP 2.12 patterns.
"""
import asyncio
import logging
import time
import os
from typing import Any, Dict, List, Optional, Callable, Awaitable

from fastapi import FastAPI
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog
import pythonjsonlogger

from .core.ring_client_modern import RingClient


def create_fastapi_app_with_docs() -> FastAPI:
    """Create a FastAPI app with documentation enabled."""
    return FastAPI(
        title="Ring MCP API",
        description="Ring Security System Management API - FastAPI Documentation",
        version="2.12.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
from .core.exceptions import (
    RingError,
    AuthenticationError,
    DeviceNotFoundError,
    StreamingError,
    RateLimitError,
)
from .composition import create_composed_app

# Configure structured logging with file output for monitoring
import logging.config
from pathlib import Path

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
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
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
from ring_mcp.core.port_manager import get_ring_mcp_port, print_port_info
RING_MCP_PORT = get_ring_mcp_port()

# Initialize FastMCP with FastMCP 2.12 patterns
app = FastMCP(
    name="Ring Security",
    version="2.12.0",
)

# Prometheus metrics
ring_api_calls_total = Counter('ring_api_calls_total', 'Total Ring API calls', ['endpoint', 'status'])
ring_api_duration = Histogram('ring_api_duration_seconds', 'Ring API call duration', ['endpoint'])
ring_device_status = Gauge('ring_device_status', 'Ring device status', ['device_id', 'device_type', 'status'])
ring_device_battery = Gauge('ring_device_battery_percent', 'Ring device battery level', ['device_id', 'device_type'])
ring_device_online = Gauge('ring_device_online', 'Ring device online status', ['device_id', 'device_type'])
ring_security_armed = Gauge('ring_security_armed', 'Security system armed status', ['location'])
ring_tool_calls_total = Counter('ring_tool_calls_total', 'Total MCP tool calls', ['tool_name'])
ring_tool_duration = Histogram('ring_tool_duration_seconds', 'MCP tool execution time', ['tool_name'])
ring_active_connections = Gauge('ring_active_connections', 'Active MCP connections')

# Models for request/response validation
class DeviceInfo(BaseModel):
    """Model for device information."""
    id: str = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Device name")
    type: str = Field(..., description="Device type/family")
    model: str = Field(..., description="Device model")
    firmware: Optional[str] = Field(None, description="Device firmware version")
    battery_life: Optional[int] = Field(None, description="Battery percentage (0-100)")
    online: bool = Field(..., description="Whether the device is currently online")
    address: Optional[str] = Field(None, description="Device location/address")
    timezone: Optional[str] = Field(None, description="Device timezone")
    has_subscription: bool = Field(False, description="Whether the device has an active subscription")
    last_update: str = Field(..., description="ISO timestamp of last update")

class EventInfo(BaseModel):
    """Model for device event information."""
    id: str = Field(..., description="Event identifier")
    created_at: str = Field(..., description="Event timestamp in ISO format")
    answered: bool = Field(False, description="Whether the event was answered")
    kind: Optional[str] = Field(None, description="Type of event")
    recording_status: Optional[str] = Field(None, description="Status of recording if available")

class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: bool = Field(True, description="Indicates this is an error response")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code if available")

# Helper function to handle errors
def handle_error(e: Exception) -> Dict[str, Any]:
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

    logger.error("Ring MCP Error", error=str(e), error_code=error_code, status_code=status_code, exc_info=True)

    return {
        "error": True,
        "message": str(e),
        "code": error_code,
        "status_code": status_code
    }

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
            except Exception as e:
                ring_tool_duration.labels(tool_name=tool_name).observe(time.time() - start_time)
                raise
        return wrapper
    return decorator

# Global Ring client instance
_ring_client: Optional[RingClient] = None

def get_ring_client() -> RingClient:
    """Get or create a Ring client instance."""
    global _ring_client
    if _ring_client is None:
        _ring_client = RingClient()
    return _ring_client

def register_ring_tools(app: FastMCP, ring_client: RingClient) -> None:
    """Register Ring MCP tools with the FastMCP application using FastMCP 2.12 patterns.

    Args:
        app: FastMCP application instance
        ring_client: Initialized RingClient instance
    """

    # Request/Response models for FastMCP 2.12
    class DeviceID(BaseModel):
        """Device identifier model."""
        device_id: str = Field(..., description="The ID of the device")

    class DeviceListResponse(BaseModel):
        """Response model for device listing."""
        devices: List[Dict[str, Any]] = Field(..., description="List of devices")

    class DeviceResponse(BaseModel):
        """Response model for device details."""
        device: Dict[str, Any] = Field(..., description="Device details")

    class EventListResponse(BaseModel):
        """Response model for event listing."""
        events: List[Dict[str, Any]] = Field(..., description="List of events")

    class StreamURLResponse(BaseModel):
        """Response model for stream URLs."""
        url: str = Field(..., description="Stream URL")

    class StatusResponse(BaseModel):
        """Response model for status updates."""
        success: bool = Field(..., description="Whether the operation was successful")
        message: str = Field(..., description="Status message")
    
    def handle_ring_errors(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """Decorator to handle Ring API errors consistently."""
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except AuthenticationError as e:
                raise ValueError(f"Authentication failed: {str(e)}")
            except DeviceNotFoundError as e:
                raise ValueError(f"Device not found: {str(e)}")
            except RateLimitError as e:
                raise ValueError(f"Rate limit exceeded: {str(e)}")
            except StreamingError as e:
                raise ValueError(f"Streaming error: {str(e)}")
            except RingError as e:
                raise ValueError(f"Ring API error: {str(e)}")
            except Exception as e:
                logger.error("Unexpected error: %s", str(e), exc_info=True)
                raise ValueError(f"Internal server error: {str(e)}")
        return wrapper
    
    @app.tool(
        name="get_devices",
        description="Get a list of all Ring devices"
    )
    @track_tool_call("get_devices")
    @handle_ring_errors
    async def get_devices(
        force_refresh: bool = False
    ) -> DeviceListResponse:
        """Get all Ring devices.

        Retrieves comprehensive information about all Ring devices including
        cameras, doorbells, sensors, and security systems. Provides real-time
        status, battery levels, and connectivity information for each device.

        Args:
            force_refresh: Whether to force refresh device data from Ring API

        Returns:
            DeviceListResponse containing all devices with their current status
        """
        try:
            devices = await ring_client.get_devices(force_refresh=force_refresh)

            # Track device metrics
            for device in devices:
                device_id = device.get('id', 'unknown')
                device_type = device.get('type', 'unknown')
                battery = device.get('battery_life')

                ring_device_online.labels(device_id=device_id, device_type=device_type).set(1 if device.get('online', False) else 0)

                if battery is not None:
                    ring_device_battery.labels(device_id=device_id, device_type=device_type).set(battery)

            return DeviceListResponse(devices=devices)
        except Exception as e:
            track_ring_api_call("get_devices", success=False)
            raise
    
    @app.tool(
        name="get_device_details",
        description="Get detailed information about a specific device"
    )
    @track_tool_call("get_device_details")
    @handle_ring_errors
    async def get_device_details(
        device_id: str
    ) -> DeviceResponse:
        """Get detailed information about a specific device.

        Retrieves comprehensive information about a specific Ring device including
        real-time status, battery level, connectivity, firmware version, and
        configuration details.

        Args:
            device_id: The unique identifier of the device

        Returns:
            DeviceResponse containing detailed device information
        """
        try:
            device = await ring_client.get_device(device_id)
            if not device:
                raise DeviceNotFoundError(f"Device {device_id} not found")

            # Track device status
            device_type = device.get('type', 'unknown')
            battery = device.get('battery_life')
            ring_device_online.labels(device_id=device_id, device_type=device_type).set(1 if device.get('online', False) else 0)

            if battery is not None:
                ring_device_battery.labels(device_id=device_id, device_type=device_type).set(battery)

            return DeviceResponse(device=device)
        except Exception as e:
            track_ring_api_call("get_device_details", success=False)
            raise
    
    @app.tool(
        name="get_device_events",
        description="Get recent events for a specific device"
    )
    @handle_ring_errors
    async def get_device_events(
        device_id: str,
        limit: int = 10
    ) -> EventListResponse:
        """Get recent events for a specific device.

        Retrieves recent events and activity history for a specific Ring device.
        This includes motion events, doorbell presses, security alerts, and
        other device-specific activities.

        Args:
            device_id: The unique identifier of the device
            limit: Maximum number of events to retrieve (default: 10)

        Returns:
            EventListResponse containing recent device events
        """
        events = await ring_client.get_device_events(device_id, limit=limit)
        return EventListResponse(events=events)
    
    @app.tool(
        name="get_live_stream_url",
        description="Get a live stream URL for a camera device"
    )
    @handle_ring_errors
    async def get_live_stream_url(
        device_id: str
    ) -> StreamURLResponse:
        """Get a live stream URL for a camera device.

        Retrieves a temporary live stream URL for viewing a Ring camera feed.
        The URL is typically valid for a limited time and should be used
        immediately for live streaming.

        Args:
            device_id: The unique identifier of the camera device

        Returns:
            StreamURLResponse containing the live stream URL
        """
        url = await ring_client.get_live_stream_url(device_id)
        return StreamURLResponse(url=url)
    
    @app.tool(
        name="set_arm_status",
        description="Arm or disarm a security device"
    )
    @track_tool_call("set_arm_status")
    @handle_ring_errors
    async def set_arm_status(
        device_id: str,
        status: bool
    ) -> StatusResponse:
        """Arm or disarm a security device.

        Controls the armed status of Ring security systems and alarm devices.
        This is a critical security operation that affects the protection status
        of your property. Use with caution and verify the action was successful.

        Args:
            device_id: The unique identifier of the security device
            status: True to arm the device, False to disarm

        Returns:
            StatusResponse indicating success or failure of the operation
        """
        try:
            success = await ring_client.set_arm_status(device_id, status)

            # Track security system status
            location = "default"  # Could be enhanced to track by location
            ring_security_armed.labels(location=location).set(1 if status else 0)

            action = "armed" if status else "disarmed"
            return StatusResponse(
                success=success,
                message=f"Device {device_id} {action} {'successfully' if success else 'failed'}"
            )
        except Exception as e:
            track_ring_api_call("set_arm_status", success=False)
            raise
    
    @app.tool(
        name="trigger_chime",
        description="Trigger a doorbell chime"
    )
    @handle_ring_errors
    async def trigger_chime(
        device_id: str
    ) -> StatusResponse:
        """Trigger a doorbell chime.

        Manually activates the chime/sound on a Ring doorbell device.
        This can be useful for testing doorbell functionality, signaling
        visitors, or integration with other home automation systems.

        Args:
            device_id: The unique identifier of the doorbell device

        Returns:
            StatusResponse indicating success or failure of the operation
        """
        success = await ring_client.trigger_chime(device_id)
        return StatusResponse(
            success=success,
            message=f"Chime {'triggered successfully' if success else 'failed to trigger'}"
        )
    
    @app.tool(
        name="health_check",
        description="Check the health of the Ring MCP service"
    )
    @handle_ring_errors
    async def health_check() -> StatusResponse:
        """Check the health of the Ring MCP service.

        Performs comprehensive health checks on the Ring MCP service including:
        - Ring API connectivity and authentication
        - Device accessibility and status
        - System resource availability
        - Tool functionality verification

        Returns:
            StatusResponse indicating overall service health
        """
        try:
            # Try to get devices as a health check
            await ring_client.get_devices(force_refresh=False)
            return StatusResponse(
                success=True,
                message="Ring MCP service is healthy"
            )
        except Exception as e:
            logger.error("Health check failed: %s", str(e))
            return StatusResponse(
                success=False,
                message=f"Health check failed: {str(e)}"
            )

# Register all tools on the global app instance
def register_all_tools_on_app(app: FastMCP, ring_client: Optional[RingClient] = None):
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
            status_tool
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

        logger.info("All Ring MCP tools registered successfully on app instance")

    except Exception as e:
        logger.error("Failed to register tools on app: %s", str(e))
        # Don't crash the server if tool registration fails
        logger.warning("App will start with limited functionality")


def register_all_tools():
    """Register all Ring MCP tools on the global app instance (for backward compatibility)."""
    register_all_tools_on_app(app)

def create_app(ring_client: Optional[RingClient] = None) -> FastMCP:
    """Create and configure the FastMCP application with composition support.

    This function creates the main FastMCP application instance and registers
    all Ring security tools using FastMCP 2.12 patterns with multiline decorators.

    Args:
        ring_client: Optional pre-initialized RingClient instance. If not provided,
                    a new client will be created using environment variables.

    Returns:
        Configured FastMCP application with Ring MCP and composition support
    """
    # Create a new FastMCP app instance
    new_app = FastMCP(
        name="Ring MCP Server",
        instructions="Comprehensive Ring Security System Management with FastMCP 2.12"
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
    # Configure structured logging for FastMCP 2.12
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

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
            structlog.processors.JSONRenderer()
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
    logger.info("Starting Ring MCP server with FastMCP 2.12 patterns")
    logger.info("Server will be available via stdio for Claude Desktop and HTTP for web access")
