"""
HTTP Server for Ring MCP - Web API Access

This module provides an HTTP REST API server for the Ring MCP functionality,
allowing web applications and other HTTP clients to access Ring device controls.

The server runs alongside the stdio MCP server, providing dual transport support.
"""
import asyncio
import json
import logging
import os
import shutil
import sys
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Awaitable, Callable, Dict, Optional


def _utc_iso() -> str:
    """RFC 3339 UTC timestamp for JSON (no fake static dates)."""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import structlog

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ring_mcp.api_log_buffer import append_log, attach_ring_mcp_loggers, get_logs
from ring_mcp.core.ring_client_modern import RingClient
from ring_mcp.ring_mqtt_bridge import get_ring_mqtt_bridge
from ring_mcp.local_llm import (
    chat_completion,
    default_model_env,
    list_model_ids,
    llm_base_url,
    probe_startup_log,
)
from ring_mcp.core.port_manager import FLEET_RING_HTTP_API_PORT
from ring_mcp.core.exceptions import (
    AuthenticationError,
    DeviceNotFoundError,
    StreamingError,
)

# Configure structured logging
logger = structlog.get_logger(__name__)

# Global Ring client instance (lazy initialization)
ring_client: Optional[RingClient] = None
auth_credentials: Optional[Dict[str, str]] = None


def _has_ring_credentials() -> bool:
    if auth_credentials and auth_credentials.get("username") and auth_credentials.get("password"):
        return True
    if os.getenv("RING_USERNAME") and os.getenv("RING_PASSWORD"):
        return True
    if os.getenv("RING_TOKEN"):
        return True
    return False


@asynccontextmanager
async def _app_lifespan(_app: FastAPI):
    attach_ring_mcp_loggers()
    append_log("INFO", "Ring MCP HTTP API started (in-memory log buffer active)")
    mqtt_bridge = get_ring_mqtt_bridge()
    mqtt_bridge.start()
    try:
        await probe_startup_log(append_log)
    except Exception:
        logger.debug("LLM startup probe skipped", exc_info=True)
    yield
    mqtt_bridge.stop()


def get_ring_client() -> RingClient:
    """Get or create the global Ring client instance."""
    global ring_client
    if ring_client is None:
        logger.info("Initializing Ring client for HTTP server")
        if auth_credentials:
            ring_client = RingClient(
                username=auth_credentials.get('username'),
                password=auth_credentials.get('password')
            )
            logger.info("Ring client initialized with provided credentials")
        else:
            ring_client = RingClient()
            logger.info("Ring client initialized without credentials")
    return ring_client

# Create FastAPI application
app = FastAPI(
    title="Ring MCP HTTP API",
    description="REST API for Ring MCP - Smart home security controls",
    version="1.0.3",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=_app_lifespan,
)

# Add CORS middleware for web app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://localhost:11110",
        "http://127.0.0.1:3000", "http://127.0.0.1:11110",
        "http://localhost:10728", "http://127.0.0.1:10728",
        "http://localhost:10706", "http://127.0.0.1:10706",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _request_log_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Any]]
):
    t0 = time.perf_counter()
    response = await call_next(request)
    # Avoid feeding the log viewer poll back into the buffer (noise + recursion vibe).
    if request.url.path == "/api/v1/logs" and response.status_code < 400:
        return response
    ms = (time.perf_counter() - t0) * 1000
    host = request.client.host if request.client else "?"
    append_log(
        "INFO",
        f"{host} {request.method} {request.url.path} {response.status_code} {ms:.0f}ms",
    )
    return response


# Error handler for API exceptions
@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401,
        content={
            "error": True,
            "message": "Authentication failed - please check your Ring credentials",
            "code": "AUTHENTICATION_ERROR"
        }
    )

@app.exception_handler(DeviceNotFoundError)
async def device_not_found_handler(request: Request, exc: DeviceNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error": True,
            "message": f"Device not found: {str(exc)}",
            "code": "DEVICE_NOT_FOUND"
        }
    )

@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    logger.error("API Error", error=str(exc), path=request.url.path, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "code": "INTERNAL_ERROR"
        }
    )

# API Routes
class RingAuthConfigureBody(BaseModel):
    """JSON body for POST /api/v1/auth/configure (matches web_sota Settings form)."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    two_factor_code: Optional[str] = Field(
        default=None,
        description="SMS/email verification code when Ring requires 2FA",
    )


class ArmRequestBody(BaseModel):
    """JSON body for POST /api/v1/devices/{id}/arm — Ring API or ring-mqtt alarm panel."""

    model_config = {"extra": "ignore"}

    status: Optional[bool] = Field(
        default=None,
        description="Legacy: True = arm away, False = disarm (ring-mqtt panels); Ring python client path",
    )
    mode: Optional[str] = Field(
        default=None,
        description="ring-mqtt: disarm | arm_home | arm_away",
    )


def _ring_response_indicates_two_factor_needed(message: str) -> bool:
    m = message.lower()
    return (
        "2fa" in m
        or "requires2fa" in m
        or "two-factor" in m
        or "verification code" in m
        or "no callback provided" in m
        or "code is required" in m
    )


def _ring_response_invalid_verification_code(message: str) -> bool:
    """True when Ring rejected an SMS/email OTP (user can try a newly sent code)."""
    m = message.lower().replace("_", " ")
    if "invalid or expired token" in m and "re-authenticate" in m:
        return False
    return (
        "invalid grant" in m
        or "invalid code" in m
        or "incorrect code" in m
        or "wrong code" in m
        or "code expired" in m
        or "expired code" in m
        or ("invalid" in m and "verification" in m)
        or ("invalid" in m and "otp" in m)
        or ("incorrect" in m and "verification" in m)
    )


@app.post("/api/v1/auth/configure")
async def configure_auth(credentials: RingAuthConfigureBody):
    """Configure authentication credentials for Ring API."""
    global ring_client, auth_credentials

    username = credentials.username
    password = credentials.password
    otp = (credentials.two_factor_code or "").strip() or None

    ring_client = None

    try:
        test_client = RingClient(
            username=username,
            password=password,
            two_factor_code=otp,
            force_password_login=True,
        )
        try:
            await test_client.connect()
            await test_client.get_devices(force_refresh=True)
        finally:
            await test_client.close()

        auth_credentials = {
            "username": username,
            "password": password,
        }

        logger.info(f"Authentication configured successfully for user: {username}")

        return {
            "success": True,
            "message": "Authentication configured successfully",
            "user": username,
            "requires_two_factor": False,
        }

    except AuthenticationError as e:
        auth_credentials = None
        ring_client = None
        msg = str(e)
        logger.warning(f"Authentication failed for user {username}: {msg}")
        if _ring_response_indicates_two_factor_needed(msg) and otp is None:
            return {
                "success": False,
                "requires_two_factor": True,
                "message": (
                    "Ring sent a security code. Enter that code in the Security code field "
                    "on Settings (same email and password) and save again."
                ),
            }
        if otp is not None and _ring_response_invalid_verification_code(msg):
            return {
                "success": False,
                "requires_two_factor": True,
                "message": (
                    "That security code was not accepted (wrong or expired). "
                    "Request a new code from Ring, enter it under Security code, and save again."
                ),
            }
        raise HTTPException(status_code=401, detail=f"Authentication failed: {msg}") from e
    except Exception as e:
        auth_credentials = None
        ring_client = None
        logger.error(f"Failed to configure authentication: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to configure authentication: {str(e)}"
        ) from e

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint for the Ring MCP server."""
    if not _has_ring_credentials():
        bridge = get_ring_mqtt_bridge()
        return {
            "success": True,
            "message": "Ring MCP HTTP server running — configure Ring credentials in Settings",
            "health_status": {
                "api_connected": False,
                "devices_accessible": len(bridge.list_alarm_devices()) if bridge.enabled else 0,
                "authentication_valid": False,
                "last_check": _utc_iso(),
                "ring_mqtt": {
                    "enabled": bridge.enabled,
                    "connected": bridge.connected,
                    "alarm_panels_seen": len(bridge.list_alarm_devices()) if bridge.enabled else 0,
                    "last_error": bridge.last_error,
                },
            },
        }
    try:
        client = get_ring_client()
        # Try to get devices to test API connectivity
        devices = await client.get_devices(force_refresh=False)
        device_count = len(devices)

        bridge = get_ring_mqtt_bridge()
        mqtt_alarms = bridge.list_alarm_devices() if bridge.enabled else []
        total = device_count + len(mqtt_alarms)
        return {
            "success": True,
            "message": f"Ring MCP server healthy - {total} devices accessible",
            "health_status": {
                "api_connected": True,
                "devices_accessible": total,
                "authentication_valid": True,
                "last_check": _utc_iso(),
                "ring_mqtt": {
                    "enabled": bridge.enabled,
                    "connected": bridge.connected,
                    "alarm_panels_seen": len(mqtt_alarms),
                    "last_error": bridge.last_error,
                },
            }
        }
    except AuthenticationError:
        bridge = get_ring_mqtt_bridge()
        return {
            "success": False,
            "message": "Ring authentication failed",
            "health_status": {
                "api_connected": False,
                "devices_accessible": len(bridge.list_alarm_devices()) if bridge.enabled else 0,
                "authentication_valid": False,
                "last_check": _utc_iso(),
                "ring_mqtt": {
                    "enabled": bridge.enabled,
                    "connected": bridge.connected,
                    "alarm_panels_seen": len(bridge.list_alarm_devices()) if bridge.enabled else 0,
                    "last_error": bridge.last_error,
                },
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        bridge = get_ring_mqtt_bridge()
        return {
            "success": False,
            "message": f"Health check failed: {str(e)}",
            "health_status": {
                "api_connected": False,
                "devices_accessible": len(bridge.list_alarm_devices()) if bridge.enabled else 0,
                "authentication_valid": False,
                "last_check": _utc_iso(),
                "ring_mqtt": {
                    "enabled": bridge.enabled,
                    "connected": bridge.connected,
                    "alarm_panels_seen": len(bridge.list_alarm_devices()) if bridge.enabled else 0,
                    "last_error": bridge.last_error,
                },
            }
        }


class LlmChatMessage(BaseModel):
    """OpenAI-style chat message for local LLM proxy."""

    role: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class LlmChatRequestBody(BaseModel):
    """POST /api/v1/llm/chat — proxied to local Ollama (default 127.0.0.1:11434)."""

    messages: list[LlmChatMessage] = Field(..., min_length=1)
    model: Optional[str] = Field(
        default=None,
        description="Model id; defaults to first from GET /api/v1/llm/models",
    )


@app.get("/api/v1/llm/models")
async def llm_list_models():
    """List model ids from the configured local OpenAI-compatible endpoint."""
    models, err = await list_model_ids()
    default_m = default_model_env()
    return {
        "success": bool(models),
        "models": models,
        "message": None if models else err,
        "default_model": default_m or (models[0] if models else None),
        "base_url": llm_base_url(),
    }


@app.post("/api/v1/llm/chat")
async def llm_chat(body: LlmChatRequestBody):
    """Chat completion via local Ollama (server-side proxy)."""
    msgs = [m.model_dump() for m in body.messages]
    sys_default = os.getenv(
        "RING_LLM_SYSTEM",
        "You are a helpful assistant for the Ring MCP fleet web UI. Be concise. "
        "Do not invent live Ring device state; suggest Status, Doorbell, or Logger when relevant.",
    ).strip()
    if sys_default and (not msgs or msgs[0].get("role") != "system"):
        msgs = [{"role": "system", "content": sys_default}, *msgs]
    try:
        reply = await chat_completion(msgs, model=body.model)
        return {"success": True, "reply": reply}
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@app.get("/api/v1/logs")
async def get_recent_logs(limit: int = Query(200, ge=1, le=500)):
    """Recent HTTP and Ring MCP log lines (in-memory ring buffer for the web UI)."""
    logs = get_logs(limit)
    return {"success": True, "logs": logs, "count": len(logs)}


@app.get("/api/v1/devices")
async def get_devices(force_refresh: bool = False):
    """Get all Ring devices."""
    try:
        client = get_ring_client()
        devices = await client.get_devices(force_refresh=force_refresh)
        bridge = get_ring_mqtt_bridge()
        if bridge.enabled:
            devices = [*devices, *bridge.list_alarm_devices()]

        return {
            "success": True,
            "devices": devices,
            "count": len(devices)
        }
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error("Failed to get devices", error=str(e))
        raise

@app.get("/api/v1/devices/{device_id}")
async def get_device(device_id: str):
    """Get details for a specific device."""
    try:
        client = get_ring_client()
        device = await client.get_device(device_id)
        if not device:
            bridge = get_ring_mqtt_bridge()
            if bridge.enabled:
                device = bridge.get_device_dict(device_id)

        if not device:
            raise DeviceNotFoundError(f"Device {device_id} not found")

        return {
            "success": True,
            "device": device
        }
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error("Failed to get device", device_id=device_id, error=str(e))
        raise

@app.get("/api/v1/devices/{device_id}/events")
async def get_device_events(device_id: str, limit: int = 10):
    """Get events for a specific device."""
    try:
        client = get_ring_client()
        events = await client.get_device_events(device_id, limit=limit)

        return {
            "success": True,
            "events": events,
            "count": len(events)
        }
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error("Failed to get device events", device_id=device_id, error=str(e))
        raise

@app.get("/api/v1/devices/{device_id}/stream")
async def get_live_stream_url(device_id: str):
    """Get live stream URL for a camera device."""
    try:
        client = get_ring_client()
        stream_url = await client.get_live_stream_url(device_id)

        return {
            "success": True,
            "url": stream_url
        }
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error("Failed to get stream URL", device_id=device_id, error=str(e))
        raise


async def _stream_mjpeg_from_rtsp(device_id: str) -> AsyncGenerator[bytes, None]:
    """Produce MJPEG multipart stream from Ring RTSP URL using ffmpeg. Requires ffmpeg on PATH."""
    proc = None
    try:
        client = get_ring_client()
        rtsp_url = await client.get_live_stream_url(device_id)
        if not rtsp_url.strip().lower().startswith("rtsp"):
            raise HTTPException(
                status_code=400,
                detail="Stream URL is not RTSP; browser proxy only supports RTSP.",
            )
        if not shutil.which("ffmpeg"):
            raise HTTPException(
                status_code=503,
                detail="ffmpeg not found. Install ffmpeg on the server for in-browser video.",
            )
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-rtsp_transport", "tcp",
            "-i", rtsp_url,
            "-f", "mjpeg",
            "-q:v", "5",
            "-r", "5",
            "-an",
            "-loglevel", "quiet",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        if proc.stdout is None:
            raise HTTPException(status_code=500, detail="ffmpeg stdout not available")
        soi, eoi = b"\xff\xd8", b"\xff\xd9"
        buffer = b""
        while True:
            chunk = await proc.stdout.read(8192)
            if not chunk:
                break
            buffer += chunk
            while eoi in buffer:
                i = buffer.find(soi)
                j = buffer.find(eoi, i) + 2
                if i == -1 or j < 2:
                    break
                frame = buffer[i:j]
                buffer = buffer[j:]
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Stream proxy error", device_id=device_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if proc is not None and proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=2.0)
            except (asyncio.TimeoutError, Exception):
                proc.kill()
                await proc.wait()


@app.get("/api/v1/devices/{device_id}/stream/live")
async def stream_live_mjpeg(device_id: str):
    """Stream live video as MJPEG for in-browser display. Requires ffmpeg on server PATH."""
    return StreamingResponse(
        _stream_mjpeg_from_rtsp(device_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.websocket("/api/v1/devices/{device_id}/stream/webrtc")
async def webrtc_signaling(websocket: WebSocket, device_id: str):
    """WebSocket relay for WebRTC signaling: browser sends SDP offer and ICE; backend relays Ring answer and ICE."""
    await websocket.accept()
    client = get_ring_client()
    try:
        await client.connect()
    except Exception as e:
        await websocket.send_json({"type": "error", "message": f"Not connected: {e}"})
        await websocket.close()
        return
    session_id: Optional[str] = None
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            typ = msg.get("type")
            if typ == "offer":
                sdp = msg.get("sdp")
                if not sdp:
                    await websocket.send_json({"type": "error", "message": "Missing sdp in offer"})
                    continue

                async def on_message(payload: Dict[str, Any]) -> None:
                    try:
                        await websocket.send_json(payload)
                    except Exception:
                        pass

                try:
                    session_id = await client.webrtc_start(device_id, sdp, on_message)
                    await websocket.send_json({"type": "session", "session_id": session_id})
                except (DeviceNotFoundError, StreamingError) as e:
                    await websocket.send_json({"type": "error", "message": str(e)})
                continue
            if typ == "ice":
                c = msg.get("candidate")
                mline = msg.get("mlineindex", 0)
                if session_id is None or c is None:
                    await websocket.send_json({"type": "error", "message": "Send offer first or missing candidate"})
                    continue
                try:
                    await client.webrtc_ice(device_id, session_id, c, int(mline))
                except Exception as e:
                    await websocket.send_json({"type": "error", "message": str(e)})
                continue
            await websocket.send_json({"type": "error", "message": f"Unknown message type: {typ}"})
    except WebSocketDisconnect:
        pass
    except json.JSONDecodeError as e:
        logger.warning("WebRTC WebSocket invalid JSON", error=str(e))
    except Exception as e:
        logger.error("WebRTC WebSocket error", error=str(e), exc_info=True)
    finally:
        if session_id:
            try:
                await client.webrtc_close(device_id, session_id)
            except Exception as e:
                logger.debug("WebRTC close ignored", error=str(e))

@app.post("/api/v1/devices/{device_id}/arm")
async def post_device_arm(device_id: str, body: ArmRequestBody):
    """Arm or disarm a security device (Ring API or ring-mqtt MQTT bridge)."""
    try:
        bridge = get_ring_mqtt_bridge()
        if bridge.enabled and bridge.is_alarm_panel(device_id):
            if body.mode:
                mode_l = body.mode.strip().lower()
            elif body.status is True:
                mode_l = "arm_away"
            elif body.status is False:
                mode_l = "disarm"
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Send status (boolean) or mode (disarm|arm_home|arm_away)",
                )
            try:
                result = await bridge.publish_alarm_mode(device_id, mode_l)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e)) from e
            return {
                "success": result,
                "message": f"Device {device_id} command {mode_l} sent via MQTT",
                "operation": mode_l,
                "timestamp": _utc_iso(),
                "device_id": device_id,
            }

        if body.status is None:
            raise HTTPException(
                status_code=400,
                detail="status must be a boolean for Ring API devices (or enable ring-mqtt for alarm panels)",
            )
        if not isinstance(body.status, bool):
            raise HTTPException(status_code=400, detail="status must be a boolean")

        client = get_ring_client()
        result = await client.set_arm_status(device_id, body.status)

        action = "armed" if body.status else "disarmed"

        return {
            "success": result,
            "message": f"Device {device_id} {action} {'successfully' if result else 'failed'}",
            "operation": action,
            "timestamp": _utc_iso(),
            "device_id": device_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to set arm status", device_id=device_id, error=str(e))
        raise

@app.post("/api/v1/devices/{device_id}/intercom/start")
async def intercom_start(device_id: str):
    """Start two-way audio (talk to visitor, e.g. tell delivery to leave package with neighbour)."""
    try:
        client = get_ring_client()
        if hasattr(client, "start_intercom") and callable(getattr(client, "start_intercom")):
            await client.start_intercom(device_id)
            return {"success": True, "message": "Two-way audio started"}
        raise HTTPException(
            status_code=501,
            detail="Two-way audio not implemented in this backend. Use Ring app for now.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Intercom start failed", device_id=device_id, error=str(e))
        raise


@app.post("/api/v1/devices/{device_id}/intercom/stop")
async def intercom_stop(device_id: str):
    """Stop two-way audio."""
    try:
        client = get_ring_client()
        if hasattr(client, "stop_intercom") and callable(getattr(client, "stop_intercom")):
            await client.stop_intercom(device_id)
            return {"success": True, "message": "Two-way audio stopped"}
        raise HTTPException(
            status_code=501,
            detail="Two-way audio not implemented in this backend.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Intercom stop failed", device_id=device_id, error=str(e))
        raise


@app.post("/api/v1/devices/{device_id}/chime")
async def trigger_doorbell_chime(device_id: str):
    """Trigger doorbell chime."""
    try:
        client = get_ring_client()
        result = await client.trigger_chime(device_id)

        return {
            "success": result,
            "message": f"Doorbell chime {'triggered successfully' if result else 'failed to trigger'}",
            "operation": "chime",
            "timestamp": _utc_iso(),
            "device_id": device_id
        }
    except Exception as e:
        logger.error("Failed to trigger chime", device_id=device_id, error=str(e))
        raise

@app.get("/api/v1/status")
async def get_system_status():
    """Get overall system status."""
    try:
        client = get_ring_client()
        devices = await client.get_devices(force_refresh=False)
        bridge = get_ring_mqtt_bridge()
        if bridge.enabled:
            devices = [*devices, *bridge.list_alarm_devices()]

        # Categorize devices
        doorbells = [d for d in devices if d.get('type') == 'doorbell']
        cameras = [d for d in devices if d.get('type') == 'camera']
        alarms = [d for d in devices if d.get('type') == 'alarm']

        return {
            "success": True,
            "status": {
                "total_devices": len(devices),
                "online_devices": len([d for d in devices if d.get('online')]),
                "doorbells": len(doorbells),
                "cameras": len(cameras),
                "alarms": len(alarms),
                "last_updated": _utc_iso(),
            }
        }
    except AuthenticationError:
        raise
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        raise

def main():
    """Run the HTTP server."""
    # Configure logging
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Configure structlog for JSON logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Get server configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", str(FLEET_RING_HTTP_API_PORT)))

    logger.info(f"Starting Ring MCP HTTP server on http://{host}:{port}")
    logger.info(f"API documentation available at: http://127.0.0.1:{port}/docs")
    logger.info("Press Ctrl+C to stop")

    # Run the server
    uvicorn.run(
        "ring_mcp.http_server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()