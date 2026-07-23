"""
Modern Ring API Client using python-ring-doorbell.

This module provides an asynchronous interface to Ring devices using the official
python-ring-doorbell library, which handles the reverse-engineered Ring API.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any, cast

import aiocache
from ring_doorbell import Auth, Ring, RingChime, RingDoorBell, RingOther, RingStickUpCam
from ring_doorbell.exceptions import AuthenticationError as RingDoorbellAuthenticationError
from ring_doorbell.exceptions import Requires2FAError as RingRequires2FAError
from ring_doorbell.generic import RingGeneric
from ring_doorbell.webrtcstream import RingWebRtcMessage, RingWebRtcStream
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import (
    AuthenticationError,
    DeviceNotFoundError,
    RateLimitError,
    RingConnectionError,
    RingError,
    StreamingError,
)
from .token_manager import TokenManager

logger = logging.getLogger(__name__)

DeviceData = dict[str, Any]


def _device_ui_category(device: RingGeneric) -> str:
    """Map ring_doorbell classes to stable API types for HTTP/MCP consumers."""
    if isinstance(device, RingStickUpCam):
        return "camera"
    if isinstance(device, RingDoorBell):
        return "doorbell"
    if isinstance(device, RingChime):
        return "chime"
    if isinstance(device, RingOther):
        return "intercom"
    return "other"


# Cache configuration
CACHE_TTL = 300  # 5 minutes


class RingClient:
    """Modern Ring client with async support and rate limiting."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        token: str | None = None,
        cache_ttl: int = CACHE_TTL,
        token_storage_path: str | None = None,
        two_factor_code: str | None = None,
        force_password_login: bool = False,
    ):
        """Initialize the Ring client.

        Args:
            username: Ring account username
            password: Ring account password
            token: OAuth token (alternative to username/password)
            cache_ttl: Cache TTL in seconds
            token_storage_path: Optional path to store tokens securely
            two_factor_code: If set, used on first password login (Ring SMS/email OTP).
            force_password_login: If True, skip cached disk token and authenticate with
                username/password (and optional OTP). Use for Settings "save credentials"
                so a stale token cannot mask a fresh login or new verification code.
        """
        self.username = username or os.getenv("RING_USERNAME")
        self.password = password or os.getenv("RING_PASSWORD")
        self.token = token or os.getenv("RING_TOKEN")
        self.cache_ttl = cache_ttl
        raw_otp = (two_factor_code or "").strip()
        self._two_factor_code: str | None = "".join(raw_otp.split()) or None
        self.force_password_login = force_password_login

        self._ring: Ring | None = None
        self._auth: Auth | None = None
        self._devices: dict[str, RingGeneric] = {}
        self._token_manager = TokenManager(storage_path=token_storage_path)
        self._token_refresh_task: asyncio.Task | None = None

        # Initialize cache
        self.cache = aiocache.Cache(
            aiocache.SimpleMemoryCache,
            ttl=cache_ttl,
            namespace="ring_mcp",
        )

    async def _close_auth_session(self) -> None:
        """Close ring_doorbell Auth aiohttp session (avoids 'Unclosed client session' warnings)."""
        auth = self._auth
        self._auth = None
        if auth is None:
            return
        try:
            closer = getattr(auth, "async_close", None)
            if closer is not None:
                await closer()
        except Exception as ex:
            logger.warning("Error closing Ring auth session: %s", ex)

    async def __aenter__(self) -> RingClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def _load_saved_token(self) -> bool:
        """Load and validate a saved token from the token manager.

        Returns:
            bool: True if a valid token was loaded, False otherwise
        """
        if not self.username:
            return False

        try:
            # Load tokens from storage
            await self._token_manager.load_tokens()

            # Try to get a valid token
            token_data = await self._token_manager.get_token(self.username)
            if not token_data:
                return False

            # Use the token to authenticate
            self.token = token_data  # Store the full token data dict
            self._auth = Auth("ring_mcp/1.0", self.token, token_updater=self._on_token_updated)

            # Initialize Ring with the auth
            self._ring = Ring(self._auth)

            # Verify the token is still valid by making a simple API call
            await asyncio.to_thread(self._ring.devices)

            logger.info("Successfully authenticated with saved token")
            return True

        except Exception as e:
            logger.warning("Failed to use saved token: %s", str(e))
            return False

    def _on_token_updated(self, token: dict[str, Any]) -> None:
        """Callback when the token is updated by the Ring API.

        Args:
            token: The updated token data
        """
        if not self.username:
            return

        logger.debug("Token updated, saving new token")

        # Schedule the token save in the event loop
        if asyncio.iscoroutinefunction(self._token_manager.save_token):
            asyncio.create_task(
                self._token_manager.save_token(
                    username=self.username,
                    access_token=token["access_token"],
                    refresh_token=token.get("refresh_token"),
                    expires_in=token.get("expires_in", 3600),
                )
            )

    async def _start_token_refresh_task(self) -> None:
        """Start a background task to refresh tokens before they expire."""
        if self._token_refresh_task and not self._token_refresh_task.done():
            return

        async def refresh_loop() -> None:
            while True:
                try:
                    if not self.username or not self._ring:
                        await asyncio.sleep(60)  # Check again in 1 minute
                        continue

                    # Get the current token data
                    token_data = await self._token_manager.get_token(self.username)
                    if not token_data:
                        await asyncio.sleep(300)  # Check again in 5 minutes
                        continue

                    # Calculate when to refresh (5 minutes before expiration)
                    expires_at = datetime.fromisoformat(token_data["expires_at"])
                    now = datetime.utcnow()
                    refresh_time = expires_at - timedelta(minutes=5)

                    if now >= refresh_time:
                        # Time to refresh
                        logger.info("Refreshing token before expiration")
                        try:
                            # This will trigger _on_token_updated with the new token
                            await asyncio.to_thread(self._ring.update_data)
                        except Exception as e:
                            logger.error("Failed to refresh token: %s", str(e))

                    # Sleep until it's time to refresh or for a maximum of 1 hour
                    sleep_time = min((refresh_time - now).total_seconds(), 3600)
                    if sleep_time > 0:
                        await asyncio.sleep(sleep_time)

                except Exception as e:
                    logger.error("Error in token refresh loop: %s", str(e))
                    await asyncio.sleep(300)  # Wait 5 minutes before retrying

        self._token_refresh_task = asyncio.create_task(refresh_loop())

    async def connect(self, two_factor_callback: Callable[[], Awaitable[str]] | None = None) -> None:
        """Initialize connection to Ring API with support for 2FA and token management.

        Args:
            two_factor_callback: Optional async callback function that will be called if 2FA is required.
                The function should return the 2FA code as a string.
                If not provided, will raise AuthenticationError when 2FA is required.
        """
        if self._ring is not None:
            return

        try:
            # First, try to use a saved token if available (skip when re-authenticating from Settings)
            if not self.force_password_login and not self.token and self.username and await self._load_saved_token():
                # Successfully loaded and validated a saved token
                await self._start_token_refresh_task()
                return

            # If we have a token, try to use it directly (skip when forcing a password re-login)
            if self.token and not self.force_password_login:
                self._auth = Auth("ring_mcp/1.0", self.token, token_updater=self._on_token_updated)
            # Fall back to username/password
            elif self.username and self.password:
                # Create Auth object
                self._auth = Auth("ring_mcp/1.0", token_updater=self._on_token_updated)

                explicit_otp = self._two_factor_code
                if explicit_otp:
                    # User already has the SMS/email code (e.g. Settings second submit).
                    await self._auth.async_fetch_token(self.username, self.password, explicit_otp)
                    logger.info("Successfully authenticated with Ring API (explicit 2FA code)")
                    self._two_factor_code = None
                else:
                    try:
                        await self._auth.async_fetch_token(self.username, self.password)
                        logger.info("Successfully authenticated with Ring API")
                    except RingRequires2FAError:
                        # python-ring-doorbell raises this (not a string "Verification Code").
                        logger.info("2FA verification code required (Requires2FAError)")
                        if two_factor_callback and inspect.iscoroutinefunction(two_factor_callback):
                            otp_val = await two_factor_callback()
                            if not (otp_val and str(otp_val).strip()):
                                raise AuthenticationError("2FA code is required but not provided")

                            otp_clean = "".join(str(otp_val).strip().split())
                            await self._auth.async_fetch_token(self.username, self.password, otp_clean)
                            logger.info("Successfully authenticated with Ring API (with 2FA)")
                        else:
                            raise AuthenticationError("2FA is required but no callback provided")
                    except Exception as e:
                        if "Verification Code" in str(e) or "2FA" in str(e) or "verification" in str(e).lower():
                            logger.info("2FA verification code required (message heuristic)")
                            if two_factor_callback and inspect.iscoroutinefunction(two_factor_callback):
                                otp_val = await two_factor_callback()
                                if not (otp_val and str(otp_val).strip()):
                                    raise AuthenticationError("2FA code is required but not provided")
                                otp_clean = "".join(str(otp_val).strip().split())
                                await self._auth.async_fetch_token(self.username, self.password, otp_clean)
                                logger.info("Successfully authenticated with Ring API (with 2FA)")
                            else:
                                raise AuthenticationError("2FA is required but no callback provided")
                        else:
                            raise AuthenticationError(f"Authentication failed: {e}") from e

                # Extract token from auth object
                self.token = self._auth._token

                # Save the new token
                if self.username and self.token:
                    await self._token_manager.save_token(
                        username=self.username,
                        access_token=self.token,
                        refresh_token=getattr(self._auth, "refresh_token", None),
                        expires_in=3600,  # Default expiration
                    )
            else:
                raise AuthenticationError("Either a valid token or username/password is required")

            # Initialize the Ring API client
            self._ring = Ring(self._auth)

            # Update device cache
            await self._update_devices()

            # Start the token refresh task
            await self._start_token_refresh_task()

            logger.info("Successfully connected to Ring API")

        except AuthenticationError:
            self._ring = None
            await self._close_auth_session()
            raise
        except RingDoorbellAuthenticationError as e:
            self._ring = None
            await self._close_auth_session()
            msg = str(e).strip()
            logger.warning("Ring rejected credentials or verification code: %s", msg)
            raise AuthenticationError(f"Failed to authenticate with Ring: {msg}") from e
        except Exception as e:
            self._ring = None
            await self._close_auth_session()
            logger.error("Failed to connect to Ring API: %s", str(e), exc_info=True)
            raise AuthenticationError(f"Failed to authenticate with Ring: {e!s}") from e

    async def close(self) -> None:
        """Close the Ring client and clean up resources."""
        # Cancel the token refresh task if it's running
        if self._token_refresh_task and not self._token_refresh_task.done():
            self._token_refresh_task.cancel()
            try:
                await self._token_refresh_task
            except asyncio.CancelledError:
                pass
            self._token_refresh_task = None

        if self._ring is not None:
            try:
                # Clear any active sessions
                await asyncio.to_thread(self._ring.update_data, force_logout=True)
            except Exception as e:
                logger.warning("Error during logout: %s", str(e))
            finally:
                self._ring = None

        await self._close_auth_session()

        # Clear the cache
        try:
            await self.cache.clear()
        except Exception as e:
            logger.warning("Error clearing cache: %s", str(e))

        self._devices.clear()

        logger.info("Ring client closed")

    def _save_token(self, token: str) -> None:
        """Callback to save the updated OAuth token."""
        self.token = token
        # In a real application, you'd want to persist this token
        logger.debug("Received new OAuth token")

    @retry(
        retry=retry_if_exception_type((RateLimitError, asyncio.TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make an authenticated request to the Ring API with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments to pass to the request

        Returns:
            The response from the API

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            RingConnectionError: For network-related errors
            RingError: For other Ring API errors
        """

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            retry=retry_if_exception_type((RateLimitError, asyncio.TimeoutError)),
            reraise=True,
        )
        async def _request():
            try:
                # Ensure we're connected
                if not self._ring or not self._auth:
                    await self.connect()

                # Make the request with timeout
                try:
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            getattr(self._auth, method.lower()), f"https://api.ring.com/clients_api{endpoint}", **kwargs
                        ),
                        timeout=60.0,  # 60 second timeout for API requests
                    )
                except TimeoutError as e:
                    raise RingConnectionError("Request to Ring API timed out") from e

                # Check for rate limiting and other error responses
                if isinstance(response, dict):
                    if response.get("code") == 429:
                        retry_after = int(response.get("retry_after", 60))
                        logger.warning("Rate limit exceeded. Retrying after %s seconds", retry_after)
                        raise RateLimitError(
                            f"Rate limit exceeded. Try again in {retry_after} seconds.", retry_after=retry_after
                        )
                    elif response.get("code") == 401:
                        # Clear the auth token if it's invalid
                        self._auth = None
                        self._ring = None
                        logger.error("Authentication failed: %s", response.get("error", "Unknown error"))
                        raise AuthenticationError("Invalid or expired token. Please re-authenticate.")
                    elif "error" in response:
                        error_msg = response.get("error", "Unknown error")
                        logger.error("Ring API error: %s", error_msg)

                        # Handle specific error cases
                        if "not found" in str(error_msg).lower():
                            raise DeviceNotFoundError(f"Resource not found: {endpoint}")
                        elif "permission" in str(error_msg).lower():
                            raise AuthenticationError("Insufficient permissions to access this resource")
                        else:
                            raise RingError(f"Ring API error: {error_msg}")

                return response

            except (OSError, TimeoutError) as e:
                # Handle network-related errors
                error_msg = str(e).lower()
                if "timeout" in error_msg or "timed out" in error_msg:
                    raise RingConnectionError("Connection to Ring API timed out") from e
                elif "connection" in error_msg or "network" in error_msg:
                    raise RingConnectionError("Network error connecting to Ring servers") from e
                else:
                    raise RingError(f"Request failed: {e!s}") from e

            except json.JSONDecodeError as e:
                raise RingError("Failed to parse response from Ring API") from e

            except Exception as e:
                # For any other unexpected errors, wrap them in RingError
                raise RingError(f"Unexpected error: {e!s}") from e

        try:
            return await _request()
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error("Error in _make_request: %s", str(e), exc_info=True)
            raise

    async def _update_devices(self) -> None:
        """Update the internal device cache."""
        if self._ring is None:
            # connect() ends by calling _update_devices again once _ring exists
            await self.connect()
            return

        try:
            # Ring.devices() returns RingDevices; iterating it yields category names (strings),
            # not device objects. Use all_devices for the flattened list.
            ring_devices = await asyncio.to_thread(lambda: self._ring.devices())

            self._devices = {str(device.id): device for device in ring_devices.all_devices}

            logger.info("Updated device cache with %d devices", len(self._devices))

        except Exception as e:
            if "429" in str(e):
                logger.error("Failed to update devices: %s", str(e), exc_info=True)
                raise RateLimitError("Rate limit exceeded while updating devices") from e
            if "401" in str(e):
                self._auth = None  # Clear invalid auth
                logger.warning("Ring returned 401 while updating devices: %s", str(e))
                raise AuthenticationError("Authentication failed while updating devices") from e
            logger.error("Failed to update devices: %s", str(e), exc_info=True)
            raise RingError(f"Failed to update devices: {e!s}") from e

    async def get_devices(self, force_refresh: bool = False) -> list[DeviceData]:
        """Get all Ring devices.

        Args:
            force_refresh: If True, force refresh the device cache.

        Returns:
            List of device dictionaries with their details.
        """
        # v2: correct device enumeration (was empty due to list(Ring.devices()) misuse).
        cache_key = f"devices_v2_{self.username}"

        if not force_refresh:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return cast(list[DeviceData], cached)

        if not self._devices or force_refresh:
            await self._update_devices()

        devices_data = []
        for device_id, device in self._devices.items():
            try:
                device_info = await self._get_device_info(device)
                devices_data.append(device_info)
            except Exception as e:
                logger.error("Error getting info for device %s: %s", device_id, str(e))

        await self.cache.set(cache_key, devices_data, ttl=self.cache_ttl)
        return devices_data

    async def _get_device_info(self, device: RingGeneric) -> DeviceData:
        """Get standardized device information."""
        device_info: DeviceData = {
            "id": str(device.id),
            "name": device.name,
            "family": device.family,
            "type": _device_ui_category(device),
            "model": device.model,
            "firmware": device.firmware,
            "battery_life": getattr(device, "battery_life", None),
            "alarm": getattr(device, "alarm", None),
            "online": device.online,
            "address": getattr(device, "address", None),
            "timezone": getattr(device, "timezone", None),
            "has_subscription": getattr(device, "has_subscription", False),
            "last_update": datetime.utcnow().isoformat(),
        }
        return device_info

    async def get_device(self, device_id: str) -> DeviceData | None:
        """Get a specific device by ID."""
        devices = await self.get_devices()
        return next((d for d in devices if d["id"] == device_id), None)

    async def get_device_events(self, device_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent events for a device."""
        if not self._devices:
            await self._update_devices()

        device = self._devices.get(device_id)
        if not device:
            raise DeviceNotFoundError(f"Device {device_id} not found")

        try:
            events = await asyncio.to_thread(lambda: device.history(limit=limit, kind="alarm"))
            return [
                {
                    "id": str(e["id"]),
                    "created_at": e["created_at"],
                    "answered": e.get("answered", False),
                    "kind": e.get("kind"),
                    "recording_status": e.get("recording", {}).get("status"),
                }
                for e in events
                if e
            ]
        except Exception as e:
            logger.error("Error getting events for device %s: %s", device_id, str(e))
            raise RingError(f"Failed to get device events: {e!s}") from e

    def _get_library_device(self, device_id: str):
        """Return the underlying ring_doorbell device (RingDoorBell or RingStickUpCam)."""
        return self._devices.get(device_id)

    async def webrtc_start(
        self,
        device_id: str,
        sdp_offer: str,
        on_message: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> str:
        """Start WebRTC signaling with Ring; call on_message with answer/ICE. Returns session_id."""
        if not self._devices:
            await self._update_devices()
        device = self._devices.get(device_id)
        if not device:
            raise DeviceNotFoundError(device_id)
        if not hasattr(device, "generate_async_webrtc_stream"):
            raise StreamingError("Device does not support WebRTC streaming")
        session_id = RingWebRtcStream.get_sdp_session_id(sdp_offer)
        if not session_id:
            raise StreamingError("Could not extract session id from SDP offer")

        def sync_cb(msg: RingWebRtcMessage) -> None:
            if msg.error_code is not None:
                asyncio.create_task(
                    on_message({"type": "error", "code": msg.error_code, "message": msg.error_message or ""})
                )
            if msg.answer:
                asyncio.create_task(on_message({"type": "answer", "sdp": msg.answer}))
            if msg.candidate is not None:
                asyncio.create_task(
                    on_message(
                        {
                            "type": "ice",
                            "candidate": msg.candidate,
                            "mlineindex": msg.sdp_m_line_index or 0,
                        }
                    )
                )

        await device.generate_async_webrtc_stream(
            sdp_offer,
            session_id,
            sync_cb,
            keep_alive_timeout=60 * 5,
        )
        return session_id

    async def webrtc_ice(
        self,
        device_id: str,
        session_id: str,
        candidate: str,
        mlineindex: int,
    ) -> None:
        """Send an ICE candidate from the client to Ring."""
        device = self._devices.get(device_id)
        if not device:
            raise DeviceNotFoundError(device_id)
        await device.on_webrtc_candidate(session_id, candidate, mlineindex)

    async def webrtc_close(self, device_id: str, session_id: str) -> None:
        """Close the WebRTC stream for the given session."""
        device = self._devices.get(device_id)
        if device and hasattr(device, "close_webrtc_stream"):
            await device.close_webrtc_stream(session_id)

    async def get_live_stream_url(self, device_id: str) -> str:
        """Live stream is WebRTC-only; use the WebSocket signaling endpoint for in-browser video."""
        raise StreamingError(
            "Use WebRTC streaming: connect to /api/v1/devices/{id}/stream/webrtc WebSocket for in-browser video."
        )

    async def set_arm_status(self, device_id: str, status: bool) -> bool:
        """Arm or disarm a security device."""
        if not self._devices:
            await self._update_devices()

        device = self._devices.get(device_id)
        if not device:
            raise DeviceNotFoundError(f"Device {device_id} not found")

        if not hasattr(device, "alarm"):
            raise RingError("Device does not support arming/disarming")

        try:
            result = await asyncio.to_thread(lambda: device.alarm.set_status("home" if status else "disarmed"))
            # Invalidate cache
            await self.cache.delete(f"devices_{self.username}")
            return bool(result)

        except Exception as e:
            logger.error("Error setting arm status for %s: %s", device_id, str(e))
            raise RingError(f"Failed to set arm status: {e!s}") from e

    async def trigger_chime(self, device_id: str) -> bool:
        """Trigger a doorbell chime."""
        if not self._devices:
            await self._update_devices()

        device = self._devices.get(device_id)
        if not device:
            raise DeviceNotFoundError(f"Device {device_id} not found")

        if not hasattr(device, "test_sound"):
            raise RingError("Device does not support chime testing")

        try:
            return await asyncio.to_thread(device.test_sound)

        except Exception as e:
            logger.error("Error triggering chime for %s: %s", device_id, str(e))
            raise RingError(f"Failed to trigger chime: {e!s}") from e
