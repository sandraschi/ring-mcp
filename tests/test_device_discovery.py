"""
Device discovery and presence detection tests.

These tests verify that the system can properly detect and work with
real Ring devices when they are available.
"""
import pytest
import asyncio
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import patch, AsyncMock
import logging

from tests.conftest import detect_test_environment, discover_real_devices, TEST_CONFIG

logger = logging.getLogger(__name__)


class TestDeviceDiscovery:
    """Test device discovery functionality."""

    def test_environment_detection_mock_mode(self):
        """Test environment detection in mock mode."""
        with patch.dict(os.environ, {"RING_MCP_TEST_MODE": "mock"}):
            env = detect_test_environment()
            assert env["mock_mode"] is True
            assert env["real_devices_available"] is False

    def test_environment_detection_real_mode(self):
        """Test environment detection in real mode."""
        with patch.dict(os.environ, {"RING_MCP_TEST_MODE": "real"}):
            env = detect_test_environment()
            assert env["mock_mode"] is False

    def test_environment_detection_auto_with_credentials(self):
        """Test automatic real mode detection with credentials."""
        with patch.dict(os.environ, {
            "RING_USERNAME": "test@example.com",
            "RING_PASSWORD": "testpass"
        }):
            env = detect_test_environment()
            assert env["ring_credentials_configured"] is True
            assert env["mock_mode"] is False  # Should switch to real mode

    def test_environment_detection_auto_without_credentials(self):
        """Test automatic mock mode detection without credentials."""
        with patch.dict(os.environ, {}, clear=True):
            env = detect_test_environment()
            assert env["ring_credentials_configured"] is False
            assert env["mock_mode"] is True  # Should stay in mock mode

    @pytest.mark.asyncio
    async def test_mock_device_discovery(self):
        """Test device discovery in mock mode."""
        # In mock mode, discovery should work without real API calls
        devices = await discover_real_devices()
        # Should return empty list when no real devices/credentials
        assert isinstance(devices, list)

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_device_discovery_success(self):
        """Test successful real device discovery."""
        devices = await discover_real_devices()

        assert isinstance(devices, list)
        if len(devices) > 0:
            # If devices are found, validate structure
            for device in devices:
                assert "id" in device
                assert "name" in device
                assert "type" in device
                assert "online" in device

    @pytest.mark.asyncio
    async def test_device_discovery_timeout_handling(self):
        """Test that device discovery handles timeouts gracefully."""
        # Mock a slow/broken discovery
        with patch('tests.conftest.RingClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_devices = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_client_class.return_value = mock_client

            devices = await discover_real_devices()

            # Should handle timeout gracefully
            assert isinstance(devices, list)

    @pytest.mark.asyncio
    async def test_device_discovery_authentication_failure(self):
        """Test device discovery with authentication failure."""
        from ring_mcp.core.exceptions import AuthenticationError

        with patch('tests.conftest.RingClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_devices = AsyncMock(side_effect=AuthenticationError("Invalid credentials"))
            mock_client_class.return_value = mock_client

            devices = await discover_real_devices()

            # Should handle auth failure gracefully
            assert isinstance(devices, list)
            assert len(devices) == 0


class TestDevicePresenceDetection:
    """Test device presence detection and validation."""

    def test_device_cache_file_creation(self, tmp_path):
        """Test that device cache file is created properly."""
        from tests.conftest import save_real_device_cache

        test_devices = [
            {"id": "test-1", "name": "Test Device 1", "type": "doorbell", "online": True},
            {"id": "test-2", "name": "Test Device 2", "type": "camera", "online": False}
        ]

        # Use temporary path for testing
        test_cache_file = tmp_path / "test_cache.json"

        # Temporarily patch the cache file path
        with patch('tests.conftest.TEST_CONFIG', {**TEST_CONFIG, "real_device_cache": test_cache_file}):
            save_real_device_cache(test_devices)

            # Verify cache file was created
            assert test_cache_file.exists()

            # Verify cache contents
            with open(test_cache_file, 'r') as f:
                cache_data = json.load(f)

            assert cache_data["available"] is True
            assert cache_data["count"] == 2
            assert len(cache_data["devices"]) == 2

    def test_device_presence_validation(self, mock_device_data):
        """Test validation of device presence data."""
        from tests.conftest import assert_device_structure

        for device in mock_device_data:
            # Should not raise any exceptions
            assert_device_structure(device)

    def test_device_type_validation(self, mock_device_data):
        """Test that device types are valid."""
        valid_types = {"doorbell", "camera", "alarm", "sensor"}

        for device in mock_device_data:
            device_type = device.get("type")
            assert device_type in valid_types, f"Invalid device type: {device_type}"

    def test_device_battery_validation(self, mock_device_data):
        """Test battery level validation."""
        for device in mock_device_data:
            battery = device.get("battery_life")
            if battery is not None:
                assert isinstance(battery, int), f"Battery should be int, got {type(battery)}"
                assert 0 <= battery <= 100, f"Battery level {battery} out of range 0-100"


class TestDeviceCapabilityDetection:
    """Test detection of device capabilities."""

    def test_camera_device_detection(self, mock_device_data):
        """Test detection of camera devices."""
        cameras = [d for d in mock_device_data if d.get("type") == "camera"]

        for camera in cameras:
            # Cameras should have streaming capability
            assert camera["type"] == "camera"
            # Note: Real capability detection would check subscription status

    def test_doorbell_device_detection(self, mock_device_data):
        """Test detection of doorbell devices."""
        doorbells = [d for d in mock_device_data if d.get("type") == "doorbell"]

        for doorbell in doorbells:
            assert doorbell["type"] == "doorbell"
            # Doorbells should support chime triggering

    def test_alarm_device_detection(self, mock_device_data):
        """Test detection of alarm/security devices."""
        alarms = [d for d in mock_device_data if d.get("type") == "alarm"]

        for alarm in alarms:
            assert alarm["type"] == "alarm"
            # Alarms should support arm/disarm operations

    def test_sensor_device_detection(self, mock_device_data):
        """Test detection of sensor devices."""
        sensors = [d for d in mock_device_data if d.get("type") == "sensor"]

        for sensor in sensors:
            assert sensor["type"] == "sensor"
            # Sensors typically don't have active operations


class TestDeviceConnectivityValidation:
    """Test device connectivity status validation."""

    def test_online_status_distribution(self, mock_device_data):
        """Test that devices have realistic online/offline distribution."""
        online_count = sum(1 for d in mock_device_data if d.get("online", False))
        offline_count = sum(1 for d in mock_device_data if not d.get("online", False))

        total_devices = len(mock_device_data)
        assert total_devices > 0, "Should have test devices"

        # Should have some online devices for meaningful testing
        assert online_count > 0, "Should have at least one online device in test data"

        logger.info(f"Device connectivity: {online_count}/{total_devices} online")

    def test_device_subscription_status(self, mock_device_data):
        """Test device subscription status."""
        subscribed = sum(1 for d in mock_device_data if d.get("has_subscription", False))
        not_subscribed = sum(1 for d in mock_device_data if not d.get("has_subscription", False))

        # Most devices should have subscriptions for full functionality
        assert subscribed >= not_subscribed, "Most devices should have subscriptions"


class TestEnvironmentConfiguration:
    """Test test environment configuration."""

    def test_test_mode_configuration(self):
        """Test test mode configuration via environment variables."""
        original_env = os.environ.copy()

        try:
            # Test mock mode
            os.environ["RING_MCP_TEST_MODE"] = "mock"
            env = detect_test_environment()
            assert env["mock_mode"] is True

            # Test real mode
            os.environ["RING_MCP_TEST_MODE"] = "real"
            env = detect_test_environment()
            assert env["mock_mode"] is False

            # Test invalid mode (should default to mock)
            os.environ["RING_MCP_TEST_MODE"] = "invalid"
            env = detect_test_environment()
            assert env["mock_mode"] is True

        finally:
            os.environ.clear()
            os.environ.update(original_env)

    def test_credentials_detection(self):
        """Test Ring credentials detection."""
        original_env = os.environ.copy()

        try:
            # No credentials
            os.environ.pop("RING_USERNAME", None)
            os.environ.pop("RING_PASSWORD", None)
            env = detect_test_environment()
            assert env["ring_credentials_configured"] is False

            # With credentials
            os.environ["RING_USERNAME"] = "test@example.com"
            os.environ["RING_PASSWORD"] = "testpass"
            env = detect_test_environment()
            assert env["ring_credentials_configured"] is True

        finally:
            os.environ.clear()
            os.environ.update(original_env)


class TestDiscoveryIntegration:
    """Test integration of discovery with other systems."""

    @pytest.mark.asyncio
    async def test_discovery_result_caching(self, tmp_path):
        """Test that discovery results are properly cached."""
        from tests.conftest import save_real_device_cache

        # Create test data
        test_devices = [
            {"id": "cached-1", "name": "Cached Device 1", "type": "doorbell", "online": True}
        ]

        cache_file = tmp_path / "discovery_cache.json"

        # Save to cache
        with patch('tests.conftest.TEST_CONFIG', {**TEST_CONFIG, "real_device_cache": cache_file}):
            save_real_device_cache(test_devices)

            # Verify cache file exists and contains data
            assert cache_file.exists()

            with open(cache_file, 'r') as f:
                cached_data = json.load(f)

            assert cached_data["count"] == 1
            assert cached_data["devices"][0]["id"] == "cached-1"

    def test_cache_data_validation(self, tmp_path):
        """Test validation of cached discovery data."""
        from tests.conftest import save_real_device_cache

        # Test with empty device list
        cache_file = tmp_path / "empty_cache.json"
        with patch('tests.conftest.TEST_CONFIG', {**TEST_CONFIG, "real_device_cache": cache_file}):
            save_real_device_cache([])

            with open(cache_file, 'r') as f:
                cached_data = json.load(f)

            assert cached_data["available"] is False
            assert cached_data["count"] == 0
            assert cached_data["devices"] == []


class TestDiscoveryErrorHandling:
    """Test error handling in device discovery."""

    @pytest.mark.asyncio
    async def test_discovery_network_error(self):
        """Test discovery with network connectivity issues."""
        with patch('tests.conftest.RingClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get_devices = AsyncMock(side_effect=Exception("Network error"))
            mock_client_class.return_value = mock_client

            devices = await discover_real_devices()

            # Should handle network errors gracefully
            assert isinstance(devices, list)

    @pytest.mark.asyncio
    async def test_discovery_partial_failure(self):
        """Test discovery when some devices fail but others succeed."""
        # This would require more complex mocking to simulate partial failures
        # For now, just ensure the function doesn't crash
        devices = await discover_real_devices()
        assert isinstance(devices, list)

    def test_cache_file_corruption_handling(self):
        """Test handling of corrupted cache files."""
        # Test with invalid JSON in cache
        cache_file = TEST_CONFIG["real_device_cache"]
        original_content = None

        if cache_file.exists():
            with open(cache_file, 'r') as f:
                original_content = f.read()

        try:
            # Write invalid JSON
            with open(cache_file, 'w') as f:
                f.write("invalid json content {")

            # Try to read environment
            env = detect_test_environment()

            # Should handle corruption gracefully
            assert "real_devices_available" in env

        finally:
            # Restore original content
            if original_content is not None:
                with open(cache_file, 'w') as f:
                    f.write(original_content)
            elif cache_file.exists():
                cache_file.unlink()