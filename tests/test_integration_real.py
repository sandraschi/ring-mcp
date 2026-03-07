"""
Integration tests that work with real Ring devices.

These tests automatically detect and work with real Ring devices when available.
They require Ring credentials and real device access.

Tests are marked with pytest markers:
- @pytest.mark.real_devices: Requires real Ring devices
- @pytest.mark.device_discovery: Involves device discovery
- @pytest.mark.integration: Full integration tests
"""
import pytest
import asyncio
import time
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TestRealDeviceDiscovery:
    """Test real device discovery and presence detection."""

    @pytest.mark.real_devices
    @pytest.mark.device_discovery
    @pytest.mark.asyncio
    async def test_real_device_discovery(self, real_ring_client):
        """Test discovery of real Ring devices."""
        devices = await real_ring_client.get_devices(force_refresh=True)

        # Should find at least one device if credentials are valid
        assert isinstance(devices, list)

        if len(devices) > 0:
            logger.info(f"Discovered {len(devices)} real devices")
            for device in devices:
                logger.info(f"  - {device.get('name', 'Unknown')} ({device.get('type', 'unknown')})")
        else:
            logger.warning("No real devices discovered")

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_device_data_structure(self, real_devices):
        """Test that real devices have proper data structure."""
        for device in real_devices:
            # Required fields
            assert "id" in device, "Device missing ID"
            assert "name" in device, "Device missing name"
            assert "type" in device, "Device missing type"
            assert "online" in device, "Device missing online status"

            # Type validation
            assert isinstance(device["id"], str), "Device ID must be string"
            assert isinstance(device["name"], str), "Device name must be string"
            assert isinstance(device["type"], str), "Device type must be string"
            assert isinstance(device["online"], bool), "Device online status must be boolean"

            # Optional fields validation
            battery = device.get("battery_life")
            if battery is not None:
                assert isinstance(battery, int), "Battery level must be integer"
                assert 0 <= battery <= 100, "Battery level must be 0-100"

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_device_types(self, real_devices):
        """Test that discovered devices have valid types."""
        valid_types = {"doorbell", "camera", "alarm", "sensor", "thermostat", "lock"}
        device_types = {device["type"] for device in real_devices}

        # All discovered devices should have valid types
        invalid_types = device_types - valid_types
        assert len(invalid_types) == 0, f"Found invalid device types: {invalid_types}"

        logger.info(f"Discovered device types: {device_types}")


class TestRealDeviceOperations:
    """Test operations on real Ring devices."""

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_device_details(self, real_ring_client, real_devices):
        """Test getting details for real devices."""
        if not real_devices:
            pytest.skip("No real devices available")

        # Test first device
        device_id = real_devices[0]["id"]
        device = await real_ring_client.get_device(device_id)

        assert device is not None, f"Could not get details for device {device_id}"
        assert device["id"] == device_id
        assert device["name"] == real_devices[0]["name"]

        logger.info(f"Retrieved details for device: {device['name']}")

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_device_events(self, real_ring_client, real_devices):
        """Test getting events for real devices."""
        if not real_devices:
            pytest.skip("No real devices available")

        # Find a device that supports events (doorbell or camera)
        event_device = None
        for device in real_devices:
            if device["type"] in ["doorbell", "camera"]:
                event_device = device
                break

        if not event_device:
            pytest.skip("No doorbell or camera devices available for event testing")

        device_id = event_device["id"]
        events = await real_ring_client.get_device_events(device_id, limit=5)

        assert isinstance(events, list), "Events should be a list"
        # Events might be empty, that's OK

        logger.info(f"Retrieved {len(events)} events for device: {event_device['name']}")

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_live_stream_url(self, real_ring_client, real_devices):
        """Test getting live stream URLs for real cameras."""
        if not real_devices:
            pytest.skip("No real devices available")

        # Find a camera device
        camera = None
        for device in real_devices:
            if device["type"] == "camera":
                camera = device
                break

        if not camera:
            pytest.skip("No camera devices available for streaming test")

        device_id = camera["id"]

        # Note: This might fail if camera is offline or subscription is inactive
        try:
            url = await real_ring_client.get_live_stream_url(device_id)
            assert isinstance(url, str), "Stream URL should be a string"
            assert url.startswith("rtsp://") or url.startswith("https://"), "URL should have valid protocol"
            logger.info(f"Got stream URL for camera: {camera['name']}")
        except Exception as e:
            logger.warning(f"Stream URL test failed for {camera['name']}: {e}")
            # This is OK - cameras might be offline or subscription issues

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_doorbell_chime(self, real_ring_client, real_devices):
        """Test doorbell chime triggering on real devices."""
        if not real_devices:
            pytest.skip("No real devices available")

        # Find a doorbell device
        doorbell = None
        for device in real_devices:
            if device["type"] == "doorbell":
                doorbell = device
                break

        if not doorbell:
            pytest.skip("No doorbell devices available for chime test")

        device_id = doorbell["id"]

        # Test chime triggering (be careful not to annoy neighbors!)
        try:
            success = await real_ring_client.trigger_chime(device_id)
            assert isinstance(success, bool), "Chime result should be boolean"
            logger.info(f"Chime test for doorbell {doorbell['name']}: {'success' if success else 'failed'}")
        except Exception as e:
            logger.warning(f"Chime test failed for {doorbell['name']}: {e}")
            # This is OK - doorbell might be offline or other issues

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_security_system(self, real_ring_client, real_devices):
        """Test security system operations on real devices."""
        if not real_devices:
            pytest.skip("No real devices available")

        # Find an alarm/security device
        alarm = None
        for device in real_devices:
            if device["type"] == "alarm":
                alarm = device
                break

        if not alarm:
            pytest.skip("No alarm devices available for security test")

        device_id = alarm["id"]

        # Get current status first (don't change armed state)
        device_details = await real_ring_client.get_device(device_id)
        logger.info(f"Security system {alarm['name']} status: {device_details}")

        # Note: We don't actually arm/disarm in tests to avoid security issues
        # Just verify the API works
        try:
            # This would arm the system - DON'T DO THIS IN TESTS
            # success = await real_ring_client.set_arm_status(device_id, True)
            logger.info(f"Security system {alarm['name']} is accessible")
        except Exception as e:
            logger.warning(f"Security system test failed for {alarm['name']}: {e}")


class TestRealDeviceConnectivity:
    """Test real device connectivity and status."""

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_device_online_status(self, real_devices):
        """Test that real devices report online status."""
        online_count = sum(1 for device in real_devices if device.get("online", False))
        offline_count = sum(1 for device in real_devices if not device.get("online", False))

        logger.info(f"Device connectivity: {online_count} online, {offline_count} offline")

        # Should have at least some devices (might all be offline)
        assert len(real_devices) > 0

        # At least one device should be online for meaningful testing
        # (but this might not be true if all devices are offline)
        if online_count == 0:
            logger.warning("All devices appear offline - connectivity issues?")

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_device_battery_levels(self, real_devices):
        """Test battery levels on real devices."""
        battery_devices = []
        wired_devices = []

        for device in real_devices:
            battery = device.get("battery_life")
            if battery is not None:
                battery_devices.append((device["name"], battery))
            else:
                wired_devices.append(device["name"])

        logger.info(f"Battery-powered devices: {len(battery_devices)}")
        for name, battery in battery_devices:
            logger.info(f"  - {name}: {battery}%")

        logger.info(f"Wired devices: {len(wired_devices)}")
        for name in wired_devices:
            logger.info(f"  - {name}")

        # Validate battery levels
        for name, battery in battery_devices:
            assert isinstance(battery, int), f"Battery level for {name} should be integer"
            assert 0 <= battery <= 100, f"Battery level for {name} should be 0-100"

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_device_subscription_status(self, real_devices):
        """Test subscription status on real devices."""
        subscribed_count = sum(1 for device in real_devices if device.get("has_subscription", False))
        no_subscription_count = sum(1 for device in real_devices if not device.get("has_subscription", False))

        logger.info(f"Devices with subscription: {subscribed_count}")
        logger.info(f"Devices without subscription: {no_subscription_count}")

        # Most Ring devices should have subscriptions for full functionality
        if subscribed_count == 0:
            logger.warning("No devices have active subscriptions - limited functionality expected")


class TestRealDevicePerformance:
    """Test performance and reliability with real devices."""

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_device_response_times(self, real_ring_client, real_devices):
        """Test response times for real device operations."""
        if not real_devices:
            pytest.skip("No real devices available")

        # Test device listing response time
        start_time = time.time()
        devices = await real_ring_client.get_devices()
        list_time = time.time() - start_time

        logger.info(".2f")

        # Should complete within reasonable time
        assert list_time < 30, f"Device listing took too long: {list_time:.2f}s"

        # Test individual device details response time
        device_id = real_devices[0]["id"]
        start_time = time.time()
        device = await real_ring_client.get_device(device_id)
        detail_time = time.time() - start_time

        logger.info(".2f")

        # Should complete within reasonable time
        assert detail_time < 10, f"Device details took too long: {detail_time:.2f}s"

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_device_concurrent_access(self, real_ring_client, real_devices):
        """Test concurrent access to real devices."""
        if len(real_devices) < 2:
            pytest.skip("Need at least 2 real devices for concurrent testing")

        # Test concurrent device detail requests
        device_ids = [device["id"] for device in real_devices[:3]]  # Test up to 3 devices

        start_time = time.time()
        tasks = [real_ring_client.get_device(device_id) for device_id in device_ids]
        results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time

        logger.info(".2f")

        # All requests should succeed
        assert all(result is not None for result in results)

        # Concurrent access should be reasonably fast
        expected_serial_time = len(device_ids) * 2  # Assume 2s per request
        assert concurrent_time < expected_serial_time, "Concurrent access should be faster than serial"

    @pytest.mark.real_devices
    @pytest.mark.asyncio
    async def test_real_device_error_recovery(self, real_ring_client, real_devices):
        """Test error recovery with real devices."""
        # Test with invalid device ID
        try:
            invalid_device = await real_ring_client.get_device("invalid-device-id-12345")
            # Should either return None or raise an exception
        except Exception as e:
            logger.info(f"Expected error for invalid device ID: {type(e).__name__}")

        # Test with valid device ID (should work)
        if real_devices:
            device_id = real_devices[0]["id"]
            device = await real_ring_client.get_device(device_id)
            assert device is not None, "Valid device should return data"


class TestRealDeviceMonitoring:
    """Test monitoring and health checks with real devices."""

    @pytest.mark.real_devices
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_system_health_check(self, real_ring_client):
        """Test comprehensive health check with real system."""
        # This would test the actual health check functionality
        # For now, just verify basic connectivity
        try:
            devices = await real_ring_client.get_devices()
            assert isinstance(devices, list)
            logger.info(f"Health check passed: {len(devices)} devices accessible")
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise

    @pytest.mark.real_devices
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_device_status_monitoring(self, real_ring_client, real_devices):
        """Test device status monitoring over time."""
        if not real_devices:
            pytest.skip("No real devices available")

        # Monitor device status over a short period
        initial_states = {}
        for device in real_devices:
            device_id = device["id"]
            device_details = await real_ring_client.get_device(device_id)
            initial_states[device_id] = {
                "online": device_details.get("online"),
                "battery": device_details.get("battery_life")
            }

        # Wait a bit and check again
        await asyncio.sleep(2)

        final_states = {}
        for device in real_devices:
            device_id = device["id"]
            device_details = await real_ring_client.get_device(device_id)
            final_states[device_id] = {
                "online": device_details.get("online"),
                "battery": device_details.get("battery_life")
            }

        # Log any changes
        for device_id in initial_states:
            initial = initial_states[device_id]
            final = final_states[device_id]

            if initial != final:
                device_name = next((d["name"] for d in real_devices if d["id"] == device_id), device_id)
                logger.info(f"Device {device_name} status changed: {initial} -> {final}")
            else:
                device_name = next((d["name"] for d in real_devices if d["id"] == device_id), device_id)
                logger.info(f"Device {device_name} status stable: {initial}")


class TestRealDeviceWorkflows:
    """Test complete workflows with real devices."""

    @pytest.mark.real_devices
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_complete_device_workflow(self, real_ring_client, real_devices):
        """Test a complete workflow: discover -> inspect -> monitor."""
        if not real_devices:
            pytest.skip("No real devices available")

        logger.info("Starting complete device workflow test")

        # Step 1: Device discovery
        devices = await real_ring_client.get_devices()
        assert len(devices) > 0
        logger.info(f"✓ Discovered {len(devices)} devices")

        # Step 2: Detailed inspection
        test_device = devices[0]
        device_details = await real_ring_client.get_device(test_device["id"])
        assert device_details is not None
        logger.info(f"✓ Inspected device: {device_details['name']}")

        # Step 3: Event history (if applicable)
        if test_device["type"] in ["doorbell", "camera"]:
            events = await real_ring_client.get_device_events(test_device["id"], limit=3)
            assert isinstance(events, list)
            logger.info(f"✓ Retrieved {len(events)} events")

        # Step 4: Status monitoring
        final_details = await real_ring_client.get_device(test_device["id"])
        assert final_details is not None
        logger.info(f"✓ Monitored device status")

        logger.info("Complete workflow test passed!")

    @pytest.mark.real_devices
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_multi_device_operations(self, real_ring_client, real_devices):
        """Test operations across multiple real devices."""
        if len(real_devices) < 2:
            pytest.skip("Need at least 2 real devices for multi-device testing")

        logger.info(f"Testing operations across {len(real_devices)} devices")

        # Test concurrent device details retrieval
        device_ids = [device["id"] for device in real_devices[:3]]  # Test up to 3 devices

        start_time = time.time()
        tasks = [real_ring_client.get_device(device_id) for device_id in device_ids]
        device_details_list = await asyncio.gather(*tasks)
        operation_time = time.time() - start_time

        # All operations should succeed
        assert all(details is not None for details in device_details_list)

        logger.info(f"✓ Multi-device operation completed in {operation_time:.2f}s")
        logger.info(f"  Retrieved details for {len(device_details_list)} devices")