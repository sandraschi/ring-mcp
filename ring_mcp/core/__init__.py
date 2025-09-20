"""
Core module for Ring MCP.

Contains the Ring API client, exception classes, and core utilities.
"""

from .ring_client import RingClient
from .exceptions import (
    RingError,
    AuthenticationError, 
    DeviceNotFoundError,
    StreamingError,
    ApiRateLimitError,
    DeviceOfflineError,
    InvalidConfigurationError
)

__all__ = [
    "RingClient",
    "RingError",
    "AuthenticationError",
    "DeviceNotFoundError", 
    "StreamingError",
    "ApiRateLimitError",
    "DeviceOfflineError",
    "InvalidConfigurationError"
]
