"""
Comprehensive test configuration and fixtures for Ring MCP.

This module provides:
- Test environment detection (mock vs real devices)
- Comprehensive fixtures for all test scenarios
- Device discovery and presence detection
- Mock data generators and utilities
- Test configuration management
"""
import asyncio
import json
import os
import pytest
import pytest_asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from unittest.mock import AsyncMock, MagicMock, patch
import logging

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_CONFIG = {
    "mock_mode": True,  # Default to mock mode for CI/CD
    "real_devices_required": False,
    "device_scan_timeout": 30,
    "test_data_dir": Path(__file__).parent / "test_data",
    "mock_data_file": Path(__file__).parent / "test_data" / "mock_devices.json",
    "real_device_cache": Path(__file__).parent / "test_data" / ".real_devices_cache.json"
}

# Create test data directory
TEST_CONFIG["test_data_dir"].mkdir(exist_ok=True)

# Test device data structures
class TestDeviceData:
    """Container for test device data and utilities."""

    DOORBELL_DATA = {
        "id": "doorbell-001",
        "name": "Front Door",
        "type": "doorbell",
        "model": "Ring Video Doorbell Pro",
        "firmware": "4.2.1",
        "battery_life": 85,
        "online": True,
        "address": "123 Main St",
        "timezone": "America/New_York",
        "has_subscription": True,
        "last_update": "2025-01-18T10:30:00Z"
    }

    CAMERA_DATA = {
        "id": "camera-001",
        "name": "Backyard Cam",
        "type": "camera",
        "model": "Ring Spotlight Cam Pro",
        "firmware": "3.1.0",
        "battery_life": 92,
        "online": True,
        "address": "123 Main St",
        "timezone": "America/New_York",
        "has_subscription": True,
        "last_update": "2025-01-18T10:30:00Z"
    }

    ALARM_DATA = {
        "id": "alarm-001",
        "name": "Home Security System",
        "type": "alarm",
        "model": "Ring Alarm Pro",
        "firmware": "2.8.3",
        "battery_life": None,  # Wired device
        "online": True,
        "address": "123 Main St",
        "timezone": "America/New_York",
        "has_subscription": True,
        "last_update": "2025-01-18T10:30:00Z"
    }

    EVENT_DATA = [
        {
            "id": "event-001",
            "created_at": "2025-01-18T10:30:00Z",
            "answered": False,
            "kind": "motion",
            "recording_status": "ready"
        },
        {
            "id": "event-002",
            "created_at": "2025-01-18T10:25:00Z",
            "answered": True,
            "kind": "doorbell",
            "recording_status": "ready"
        }
    ]

def detect_test_environment() -> Dict[str, Any]:
    """Detect test environment and capabilities."""
    env_info = {
        "mock_mode": True,
        "real_devices_available": False,
        "ring_credentials_configured": False,
        "real_device_count": 0,
        "detected_devices": []
    }

    # Check for Ring credentials
    ring_username = os.getenv("RING_USERNAME")
    ring_password = os.getenv("RING_PASSWORD")

    if ring_username and ring_password:
        env_info["ring_credentials_configured"] = True
        env_info["mock_mode"] = False  # Switch to real mode if credentials available

    # Check for explicit test mode override
    test_mode = os.getenv("RING_MCP_TEST_MODE", "").lower()
    if test_mode == "mock":
        env_info["mock_mode"] = True
    elif test_mode == "real":
        env_info["mock_mode"] = False

    # Check for real device cache
    if TEST_CONFIG["real_device_cache"].exists():
        try:
            with open(TEST_CONFIG["real_device_cache"], 'r') as f:
                cache_data = json.load(f)
                env_info["real_devices_available"] = cache_data.get("available", False)
                env_info["real_device_count"] = cache_data.get("count", 0)
                env_info["detected_devices"] = cache_data.get("devices", [])
        except Exception as e:
            logger.warning(f"Failed to read real device cache: {e}")

    return env_info

def save_real_device_cache(devices: List[Dict[str, Any]]) -> None:
    """Save detected real devices to cache."""
    cache_data = {
        "available": len(devices) > 0,
        "count": len(devices),
        "devices": devices,
        "timestamp": "2025-01-18T10:30:00Z"
    }

    with open(TEST_CONFIG["real_device_cache"], 'w') as f:
        json.dump(cache_data, f, indent=2)

def load_mock_device_data() -> List[Dict[str, Any]]:
    """Load mock device data from file or generate defaults."""
    if TEST_CONFIG["mock_data_file"].exists():
        try:
            with open(TEST_CONFIG["mock_data_file"], 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load mock data: {e}")

    # Generate default mock data
    return [
        TestDeviceData.DOORBELL_DATA,
        TestDeviceData.CAMERA_DATA,
        TestDeviceData.ALARM_DATA
    ]

def create_mock_ring_client() -> MagicMock:
    """Create a comprehensive mock Ring client."""
    from ring_mcp.core.ring_client_modern import RingClient

    mock_client = MagicMock(spec=RingClient)

    # Configure mock methods
    mock_client.get_devices = AsyncMock(return_value=load_mock_device_data())
    mock_client.get_device = AsyncMock(return_value=TestDeviceData.DOORBELL_DATA)
    mock_client.get_device_events = AsyncMock(return_value=TestDeviceData.EVENT_DATA)
    mock_client.get_live_stream_url = AsyncMock(return_value="rtsp://mock-stream-url")
    mock_client.set_arm_status = AsyncMock(return_value=True)
    mock_client.trigger_chime = AsyncMock(return_value=True)

    return mock_client

async def discover_real_devices() -> List[Dict[str, Any]]:
    """Attempt to discover real Ring devices."""
    try:
        from ring_mcp.core.ring_client_modern import RingClient

        # Check for credentials
        ring_username = os.getenv("RING_USERNAME")
        ring_password = os.getenv("RING_PASSWORD")

        if not ring_username or not ring_password:
            logger.info("No Ring credentials configured, skipping real device discovery")
            return []

        logger.info("Attempting to discover real Ring devices...")

        # Create real client (with timeout)
        client = RingClient()

        # Attempt to get devices with timeout
        devices = await asyncio.wait_for(
            client.get_devices(force_refresh=True),
            timeout=TEST_CONFIG["device_scan_timeout"]
        )

        logger.info(f"Discovered {len(devices)} real Ring devices")
        save_real_device_cache(devices)
        return devices

    except asyncio.TimeoutError:
        logger.warning("Real device discovery timed out")
        return []
    except Exception as e:
        logger.warning(f"Real device discovery failed: {e}")
        return []

# Pytest fixtures
@pytest.fixture(scope="session")
def test_environment():
    """Provide test environment information."""
    return detect_test_environment()

@pytest.fixture(scope="session")
def mock_device_data():
    """Provide mock device test data."""
    return load_mock_device_data()

@pytest.fixture
def mock_ring_client():
    """Provide a comprehensive mock Ring client."""
    return create_mock_ring_client()

@pytest.fixture
def sample_doorbell():
    """Provide sample doorbell device data."""
    return TestDeviceData.DOORBELL_DATA.copy()

@pytest.fixture
def sample_camera():
    """Provide sample camera device data."""
    return TestDeviceData.CAMERA_DATA.copy()

@pytest.fixture
def sample_alarm():
    """Provide sample alarm device data."""
    return TestDeviceData.ALARM_DATA.copy()

@pytest.fixture
def sample_events():
    """Provide sample event data."""
    return TestDeviceData.EVENT_DATA.copy()

@pytest_asyncio.fixture
async def real_devices(test_environment):
    """Provide real devices if available, otherwise skip."""
    if test_environment["mock_mode"]:
        pytest.skip("Test requires real Ring devices (mock mode enabled)")

    if not test_environment["real_devices_available"]:
        pytest.skip("No real Ring devices detected")

    return test_environment["detected_devices"]

@pytest_asyncio.fixture
async def real_ring_client(test_environment):
    """Provide real Ring client if credentials available."""
    if test_environment["mock_mode"]:
        pytest.skip("Test requires real Ring client (mock mode enabled)")

    if not test_environment["ring_credentials_configured"]:
        pytest.skip("Ring credentials not configured")

    from ring_mcp.core.ring_client_modern import RingClient
    return RingClient()

@pytest.fixture
def device_discovery_enabled(test_environment):
    """Mark tests that require device discovery."""
    return not test_environment["mock_mode"]

# Test configuration markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "mock_only: Tests that only run with mocks")
    config.addinivalue_line("markers", "real_devices: Tests that require real Ring devices")
    config.addinivalue_line("markers", "device_discovery: Tests that involve device discovery")
    config.addinivalue_line("markers", "integration: Integration tests")

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment."""
    env = detect_test_environment()

    for item in items:
        # Skip real device tests in mock mode
        if "real_devices" in item.keywords and env["mock_mode"]:
            item.add_marker(pytest.mark.skip(reason="Requires real Ring devices"))

        # Skip device discovery tests if not configured
        if "device_discovery" in item.keywords and env["mock_mode"]:
            item.add_marker(pytest.mark.skip(reason="Device discovery not available in mock mode"))

        # Mark integration tests appropriately
        if "integration" in item.keywords:
            if env["mock_mode"]:
                item.add_marker(pytest.mark.skip(reason="Integration tests skipped in mock mode"))
            else:
                item.add_marker(pytest.mark.skip(reason="Real device integration not configured"))

# Environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment and perform initial device discovery."""
    env = detect_test_environment()

    logger.info("Test Environment Setup:")
    logger.info(f"  Mock Mode: {env['mock_mode']}")
    logger.info(f"  Real Devices Available: {env['real_devices_available']}")
    logger.info(f"  Ring Credentials: {env['ring_credentials_configured']}")
    logger.info(f"  Real Device Count: {env['real_device_count']}")

    # Perform initial real device discovery if credentials available and not in mock mode
    if not env["mock_mode"] and env["ring_credentials_configured"]:
        logger.info("Performing initial real device discovery...")
        try:
            devices = asyncio.run(discover_real_devices())
            if devices:
                logger.info(f"Initial discovery found {len(devices)} devices")
            else:
                logger.warning("Initial discovery found no devices")
        except Exception as e:
            logger.error(f"Initial device discovery failed: {e}")

    return env

# Utility functions for tests
def assert_device_structure(device: Dict[str, Any]):
    """Assert that a device has the expected structure."""
    required_fields = ["id", "name", "type", "online"]
    for field in required_fields:
        assert field in device, f"Device missing required field: {field}"

    assert isinstance(device["id"], str), "Device ID must be string"
    assert isinstance(device["name"], str), "Device name must be string"
    assert isinstance(device["type"], str), "Device type must be string"
    assert isinstance(device["online"], bool), "Device online status must be boolean"

def assert_event_structure(event: Dict[str, Any]):
    """Assert that an event has the expected structure."""
    required_fields = ["id", "created_at", "kind"]
    for field in required_fields:
        assert field in event, f"Event missing required field: {field}"

def create_mock_response(success: bool = True, message: str = "", **kwargs) -> Dict[str, Any]:
    """Create a mock API response."""
    response = {"success": success, "message": message}
    response.update(kwargs)
    return response

# Export utilities for use in tests
__all__ = [
    "TEST_CONFIG",
    "TestDeviceData",
    "detect_test_environment",
    "load_mock_device_data",
    "create_mock_ring_client",
    "discover_real_devices",
    "assert_device_structure",
    "assert_event_structure",
    "create_mock_response"
]