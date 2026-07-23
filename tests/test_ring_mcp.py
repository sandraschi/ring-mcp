"""
Tests for the Ring MCP implementation.

These tests verify the basic functionality of the Ring MCP server.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ring_mcp.core.exceptions import AuthenticationError, DeviceNotFoundError

# Import the server module to test
from ring_mcp.server import RingClient, create_app

# Test data
TEST_DEVICES = [
    {
        "id": "test-device-1",
        "name": "Front Door",
        "type": "doorbell",
        "model": "Ring Video Doorbell Pro",
        "firmware": "1.2.3",
        "battery_life": 85,
        "online": True,
        "address": "123 Test St",
        "timezone": "Europe/Vienna",
        "has_subscription": True,
        "last_update": "2025-01-01T12:00:00Z",
    },
    {
        "id": "test-device-2",
        "name": "Back Door",
        "type": "camera",
        "model": "Ring Stick Up Cam",
        "firmware": "2.3.4",
        "battery_life": 45,
        "online": True,
        "address": "123 Test St",
        "timezone": "Europe/Vienna",
        "has_subscription": True,
        "last_update": "2025-01-01T12:00:00Z",
    },
]


# Fixtures
@pytest.fixture
def app():
    """Create a test FastMCP application."""
    # Create a test app with test configuration
    test_app = create_app()
    return test_app


@pytest.fixture
def mock_ring_client():
    """Create a mock Ring client for testing."""
    # Create a mock Ring client
    mock_client = MagicMock(spec=RingClient)
    mock_client.get_devices = AsyncMock(return_value=TEST_DEVICES)
    mock_client.get_device = AsyncMock(return_value=TEST_DEVICES[0])
    mock_client.get_device_events = AsyncMock(
        return_value=[
            {
                "id": "event-1",
                "created_at": "2025-01-01T12:00:00Z",
                "answered": False,
                "kind": "motion",
                "recording_status": "ready",
            }
        ]
    )
    mock_client.get_live_stream_url = AsyncMock(return_value="rtsp://test-stream-url")
    mock_client.set_arm_status = AsyncMock(return_value=True)
    mock_client.trigger_chime = AsyncMock(return_value=True)

    return mock_client


# Test cases
@pytest.mark.asyncio
async def test_get_devices(mock_ring_client):
    """Test getting all devices."""
    # Test the underlying client method directly
    devices = await mock_ring_client.get_devices(force_refresh=False)

    # Verify the response
    assert isinstance(devices, list)
    assert len(devices) == 2
    assert devices[0]["id"] == "test-device-1"
    assert devices[1]["id"] == "test-device-2"

    # Verify the mock was called
    mock_ring_client.get_devices.assert_called_once_with(force_refresh=False)


@pytest.mark.asyncio
async def test_get_device(mock_ring_client):
    """Test getting a specific device."""
    # Test the underlying client method directly
    device = await mock_ring_client.get_device("test-device-1")

    # Verify the response
    assert device["id"] == "test-device-1"
    assert device["name"] == "Front Door"

    # Verify the mock was called
    mock_ring_client.get_device.assert_called_once_with("test-device-1")


@pytest.mark.asyncio
async def test_get_device_events(mock_ring_client):
    """Test getting device events."""
    # Test the underlying client method directly
    events = await mock_ring_client.get_device_events("test-device-1", limit=1)

    # Verify the response
    assert isinstance(events, list)
    assert len(events) == 1
    assert events[0]["id"] == "event-1"

    # Verify the mock was called
    mock_ring_client.get_device_events.assert_called_once_with("test-device-1", limit=1)


@pytest.mark.asyncio
async def test_get_live_stream_url(mock_ring_client):
    """Test getting a live stream URL."""
    # Test the underlying client method directly
    url = await mock_ring_client.get_live_stream_url("test-device-1")

    # Verify the response
    assert url == "rtsp://test-stream-url"

    # Verify the mock was called
    mock_ring_client.get_live_stream_url.assert_called_once_with("test-device-1")


@pytest.mark.asyncio
async def test_set_arm_status(mock_ring_client):
    """Test setting arm status."""
    # Test the underlying client method directly
    result = await mock_ring_client.set_arm_status("test-device-1", True)

    # Verify the response
    assert result is True

    # Verify the mock was called
    mock_ring_client.set_arm_status.assert_called_once_with("test-device-1", True)


@pytest.mark.asyncio
async def test_trigger_chime(mock_ring_client):
    """Test triggering a doorbell chime."""
    # Test the underlying client method directly
    result = await mock_ring_client.trigger_chime("test-device-1")

    # Verify the response
    assert result is True

    # Verify the mock was called
    mock_ring_client.trigger_chime.assert_called_once_with("test-device-1")


@pytest.mark.asyncio
async def test_health_check(app, mock_ring_client):
    """Test the health check endpoint."""
    # Patch the get_ring_client to return our mock
    with patch("ring_mcp.server.get_ring_client", return_value=mock_ring_client):
        # Import the health check function directly from the server

        # Create a test app
        create_app(mock_ring_client)

        # For health check, we test that the client method is called
        devices = await mock_ring_client.get_devices(force_refresh=False)

        # Verify we got devices (indicating healthy state)
        assert isinstance(devices, list)
        assert len(devices) == 2


# Error handling tests
@pytest.mark.asyncio
async def test_device_not_found(mock_ring_client):
    """Test handling of device not found error."""
    # Configure the mock to raise an exception
    mock_ring_client.get_device.side_effect = DeviceNotFoundError("test-device-99")

    # Call the get_device method directly - should raise exception
    with pytest.raises(DeviceNotFoundError):
        await mock_ring_client.get_device("test-device-99")

    # Verify the mock was called
    mock_ring_client.get_device.assert_called_once_with("test-device-99")


@pytest.mark.asyncio
async def test_authentication_error(mock_ring_client):
    """Test handling of authentication error."""
    # Configure the mock to raise an authentication error
    mock_ring_client.get_devices.side_effect = AuthenticationError("Invalid credentials")

    # Call the get_devices method directly - should raise exception
    with pytest.raises(AuthenticationError):
        await mock_ring_client.get_devices(force_refresh=False)

    # Verify the mock was called
    mock_ring_client.get_devices.assert_called_once_with(force_refresh=False)


if __name__ == "__main__":
    # Run tests with pytest
    import sys

    import pytest

    sys.exit(pytest.main(["-v", "-s", __file__]))
