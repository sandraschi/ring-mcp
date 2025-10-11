"""
Tests for the Ring MCP implementation.

These tests verify the basic functionality of the Ring MCP server and client.
"""
import asyncio
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastmcp import Client

# Import the server module to test
from ring_mcp.server import create_app
from ring_mcp.core.ring_client_modern import RingClient
from ring_mcp.core.exceptions import AuthenticationError, DeviceNotFoundError

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
        "last_update": "2025-01-01T12:00:00Z"
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
        "last_update": "2025-01-01T12:00:00Z"
    }
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
    with patch('ring_mcp.server.RingClient') as mock_client:
        # Configure the mock client
        mock_instance = mock_client.return_value
        mock_instance.get_devices = AsyncMock(return_value=TEST_DEVICES)
        mock_instance.get_device = AsyncMock(return_value=TEST_DEVICES[0])
        mock_instance.get_device_events = AsyncMock(return_value=[
            {
                "id": "event-1",
                "created_at": "2025-01-01T12:00:00Z",
                "answered": False,
                "kind": "motion",
                "recording_status": "ready"
            }
        ])
        mock_instance.get_live_stream_url = AsyncMock(return_value="rtsp://test-stream-url")
        mock_instance.set_arm_status = AsyncMock(return_value=True)
        mock_instance.trigger_chime = AsyncMock(return_value=True)
        
        yield mock_instance

@pytest.fixture
async def client(app, mock_ring_client):
    """Create a test client for the FastMCP application."""
    # Use the mock Ring client
    app.ring_client = mock_ring_client
    
    # Create a test client
    test_client = await Client.connect("stdio://")
    return test_client

# Test cases
@pytest.mark.asyncio
async def test_get_devices(client, mock_ring_client):
    """Test getting all devices."""
    # Call the get_devices tool
    response = await client.call_tool("get_devices", {"force_refresh": False})
    
    # Verify the response
    assert isinstance(response.content, list)
    assert len(response.content) == 2
    assert response.content[0]["id"] == "test-device-1"
    assert response.content[1]["id"] == "test-device-2"
    
    # Verify the mock was called
    mock_ring_client.get_devices.assert_called_once_with(force_refresh=False)

@pytest.mark.asyncio
async def test_get_device(client, mock_ring_client):
    """Test getting a specific device."""
    # Call the get_device tool
    response = await client.call_tool("get_device", {"device_id": "test-device-1"})
    
    # Verify the response
    assert response.content["id"] == "test-device-1"
    assert response.content["name"] == "Front Door"
    
    # Verify the mock was called
    mock_ring_client.get_device.assert_called_once_with("test-device-1")

@pytest.mark.asyncio
async def test_get_device_events(client, mock_ring_client):
    """Test getting device events."""
    # Call the get_device_events tool
    response = await client.call_tool("get_device_events", {
        "device_id": "test-device-1",
        "limit": 1
    })
    
    # Verify the response
    assert isinstance(response.content, list)
    assert len(response.content) == 1
    assert response.content[0]["id"] == "event-1"
    
    # Verify the mock was called
    mock_ring_client.get_device_events.assert_called_once_with("test-device-1", limit=1)

@pytest.mark.asyncio
async def test_get_live_stream_url(client, mock_ring_client):
    """Test getting a live stream URL."""
    # Call the get_live_stream_url tool
    response = await client.call_tool("get_live_stream_url", {
        "device_id": "test-device-1"
    })
    
    # Verify the response
    assert "stream_url" in response.content
    assert response.content["stream_url"] == "rtsp://test-stream-url"
    
    # Verify the mock was called
    mock_ring_client.get_live_stream_url.assert_called_once_with("test-device-1")

@pytest.mark.asyncio
async def test_set_arm_status(client, mock_ring_client):
    """Test setting arm status."""
    # Call the set_arm_status tool
    response = await client.call_tool("set_arm_status", {
        "device_id": "test-device-1",
        "status": True
    })
    
    # Verify the response
    assert response.content["success"] is True
    
    # Verify the mock was called
    mock_ring_client.set_arm_status.assert_called_once_with("test-device-1", True)

@pytest.mark.asyncio
async def test_trigger_chime(client, mock_ring_client):
    """Test triggering a doorbell chime."""
    # Call the trigger_chime tool
    response = await client.call_tool("trigger_chime", {
        "device_id": "test-device-1"
    })
    
    # Verify the response
    assert response.content["success"] is True
    
    # Verify the mock was called
    mock_ring_client.trigger_chime.assert_called_once_with("test-device-1")

@pytest.mark.asyncio
async def test_health_check(client, mock_ring_client):
    """Test the health check endpoint."""
    # Call the health_check tool
    response = await client.call_tool("health_check", {})
    
    # Verify the response
    assert response.content["status"] == "healthy"
    assert "version" in response.content

# Error handling tests
@pytest.mark.asyncio
async def test_device_not_found(client, mock_ring_client):
    """Test handling of device not found error."""
    # Configure the mock to raise an exception
    mock_ring_client.get_device.side_effect = DeviceNotFoundError("test-device-99")
    
    # Call the get_device tool with a non-existent device ID
    response = await client.call_tool("get_device", {"device_id": "test-device-99"})
    
    # Verify the error response
    assert response.error is True
    assert response.content["code"] == "device_not_found"
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_authentication_error(client, mock_ring_client):
    """Test handling of authentication error."""
    # Configure the mock to raise an authentication error
    mock_ring_client.get_devices.side_effect = AuthenticationError("Invalid credentials")
    
    # Call the get_devices tool
    response = await client.call_tool("get_devices", {})
    
    # Verify the error response
    assert response.error is True
    assert response.content["code"] == "authentication_error"
    assert response.status_code == 401

if __name__ == "__main__":
    # Run tests with pytest
    import sys
    import pytest
    sys.exit(pytest.main(["-v", "-s", __file__]))
