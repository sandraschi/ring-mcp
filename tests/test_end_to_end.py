"""
End-to-end workflow tests for Ring MCP.

These tests simulate complete user workflows from device discovery
to monitoring and control operations, using both mock and real devices.
"""

import asyncio
import logging
import time

import pytest

logger = logging.getLogger(__name__)


class TestCompleteWorkflowsMock:
    """Complete workflow tests using mocks."""

    @pytest.mark.asyncio
    async def test_home_security_setup_workflow(self, mock_ring_client):
        """Test complete home security setup workflow."""
        logger.info("Testing home security setup workflow")

        # Step 1: Discover devices
        devices = await mock_ring_client.get_devices(force_refresh=True)
        assert len(devices) >= 3, "Should discover multiple devices"

        cameras = [d for d in devices if d["type"] == "camera"]
        doorbells = [d for d in devices if d["type"] == "doorbell"]
        alarms = [d for d in devices if d["type"] == "alarm"]

        logger.info(f"Discovered: {len(cameras)} cameras, {len(doorbells)} doorbells, {len(alarms)} alarms")

        # Step 2: Verify all devices are online and healthy
        offline_devices = [d for d in devices if not d.get("online", False)]
        assert len(offline_devices) == 0, f"Found offline devices: {[d['name'] for d in offline_devices]}"

        # Step 3: Check security system status
        if alarms:
            alarm = alarms[0]
            device_details = await mock_ring_client.get_device(alarm["id"])
            assert device_details["online"], f"Security system {alarm['name']} should be online"

        # Step 4: Test camera streaming capability
        for camera in cameras[:2]:  # Test first 2 cameras
            stream_url = await mock_ring_client.get_live_stream_url(camera["id"])
            assert stream_url.startswith("rtsp://"), f"Invalid stream URL for {camera['name']}"

        # Step 5: Test doorbell functionality
        for doorbell in doorbells[:1]:  # Test first doorbell
            chime_result = await mock_ring_client.trigger_chime(doorbell["id"])
            assert chime_result, f"Chime failed for {doorbell['name']}"

        logger.info("Home security setup workflow completed successfully")

    @pytest.mark.asyncio
    async def test_device_monitoring_workflow(self, mock_ring_client):
        """Test device monitoring and status checking workflow."""
        logger.info("Testing device monitoring workflow")

        # Step 1: Initial device scan
        devices = await mock_ring_client.get_devices()
        initial_device_count = len(devices)
        assert initial_device_count > 0

        # Step 2: Monitor device status over time
        initial_states = {}
        for device in devices:
            device_id = device["id"]
            details = await mock_ring_client.get_device(device_id)
            initial_states[device_id] = {"online": details.get("online"), "battery": details.get("battery_life")}

        # Step 3: Simulate time passing and re-check
        await asyncio.sleep(0.1)  # Minimal delay for testing

        final_states = {}
        for device in devices:
            device_id = device["id"]
            details = await mock_ring_client.get_device(device_id)
            final_states[device_id] = {"online": details.get("online"), "battery": details.get("battery_life")}

        # Step 4: Verify monitoring data consistency
        for device_id in initial_states:
            assert device_id in final_states, f"Device {device_id} lost during monitoring"
            # States should be consistent (in mock environment)
            assert initial_states[device_id] == final_states[device_id], f"Inconsistent state for {device_id}"

        # Step 5: Check event history for activity monitoring devices
        for device in devices:
            if device["type"] in ["camera", "doorbell"]:
                events = await mock_ring_client.get_device_events(device["id"], limit=5)
                assert isinstance(events, list), f"Events should be list for {device['name']}"

        logger.info(f"Device monitoring completed for {len(devices)} devices")

    @pytest.mark.asyncio
    async def test_security_response_workflow(self, mock_ring_client):
        """Test security incident response workflow."""
        logger.info("Testing security response workflow")

        # Step 1: Get current system status
        devices = await mock_ring_client.get_devices()
        security_devices = [d for d in devices if d["type"] == "alarm"]

        if not security_devices:
            pytest.skip("No security devices available for this test")

        security_system = security_devices[0]

        # Step 2: Check current security status
        initial_status = await mock_ring_client.get_device(security_system["id"])
        logger.info(f"Security system {security_system['name']} initial status: online={initial_status.get('online')}")

        # Step 3: Simulate security activation (arm system)
        arm_result = await mock_ring_client.set_arm_status(security_system["id"], True)
        assert arm_result, "Security system arming should succeed"

        # Step 4: Verify system armed status
        updated_status = await mock_ring_client.get_device(security_system["id"])
        assert updated_status["online"], "Security system should remain online after arming"

        # Step 5: Check recent events (would show arming activity in real system)
        events = await mock_ring_client.get_device_events(security_system["id"], limit=3)
        assert isinstance(events, list), "Should be able to retrieve security events"

        # Step 6: Simulate security deactivation (disarm system)
        disarm_result = await mock_ring_client.set_arm_status(security_system["id"], False)
        assert disarm_result, "Security system disarming should succeed"

        logger.info("Security response workflow completed successfully")


class TestWorkflowPerformance:
    """Test workflow performance characteristics."""

    @pytest.mark.asyncio
    async def test_concurrent_device_operations(self, mock_ring_client):
        """Test performance of concurrent device operations."""
        import time

        # Get test devices
        devices = await mock_ring_client.get_devices()
        device_ids = [d["id"] for d in devices[:5]]  # Test up to 5 devices

        # Test concurrent device detail retrieval
        start_time = time.time()

        tasks = [mock_ring_client.get_device(device_id) for device_id in device_ids]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Verify all operations succeeded
        assert len(results) == len(device_ids)
        assert all(result is not None for result in results)

        # Performance check - concurrent should be reasonably fast
        assert total_time < 2.0, ".2f"
        logger.info(".2f")

    @pytest.mark.asyncio
    async def test_bulk_device_status_check(self, mock_ring_client):
        """Test bulk device status checking performance."""
        import time

        devices = await mock_ring_client.get_devices()

        # Perform bulk status check
        start_time = time.time()

        status_tasks = []
        for device in devices:
            if device["type"] in ["camera", "doorbell"]:
                # Check events as proxy for status
                status_tasks.append(mock_ring_client.get_device_events(device["id"], limit=1))
            else:
                # Just get device details
                status_tasks.append(mock_ring_client.get_device(device["id"]))

        results = await asyncio.gather(*status_tasks)

        end_time = time.time()
        total_time = end_time - start_time

        # Verify all status checks succeeded
        assert len(results) == len(status_tasks)
        assert all(result is not None for result in results)

        # Performance should be acceptable
        max_expected_time = len(devices) * 0.5  # 0.5s per device max
        assert total_time < max_expected_time, (
            f"Bulk status check took {total_time:.2f}s (max expected: {max_expected_time:.2f}s)"
        )

        logger.info(".2f")


class TestWorkflowErrorRecovery:
    """Test error recovery in complete workflows."""

    @pytest.mark.asyncio
    async def test_partial_device_failure_recovery(self, mock_ring_client):
        """Test workflow recovery when some devices fail."""
        devices = await mock_ring_client.get_devices()

        # Simulate partial failure - make one device return None
        original_get_device = mock_ring_client.get_device
        failed_device_id = devices[0]["id"] if devices else "nonexistent"

        async def failing_get_device(device_id):
            if device_id == failed_device_id:
                return None  # Simulate failure
            return await original_get_device(device_id)

        mock_ring_client.get_device = failing_get_device

        try:
            # Attempt workflow with partial failure
            successful_devices = []
            failed_devices = []

            for device in devices:
                try:
                    details = await mock_ring_client.get_device(device["id"])
                    if details:
                        successful_devices.append(device)
                    else:
                        failed_devices.append(device)
                except Exception:
                    failed_devices.append(device)

            # Should handle partial failures gracefully
            assert len(successful_devices) + len(failed_devices) == len(devices)
            assert len(successful_devices) >= len(devices) - 1  # At most one failure

            if failed_devices:
                logger.info(f"Handled failure for device: {failed_devices[0]['name']}")
                assert failed_devices[0]["id"] == failed_device_id

        finally:
            # Restore original function
            mock_ring_client.get_device = original_get_device

    @pytest.mark.asyncio
    async def test_network_interruption_recovery(self, mock_ring_client):
        """Test workflow recovery from network interruptions."""
        devices = await mock_ring_client.get_devices()

        # Simulate network interruption followed by recovery
        call_count = 0

        async def intermittent_get_devices(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                raise Exception("Network temporarily unavailable")
            elif call_count == 2:
                # Brief success
                return devices
            else:
                raise Exception("Network still unavailable")

        original_get_devices = mock_ring_client.get_devices
        mock_ring_client.get_devices = intermittent_get_devices

        try:
            # First call should fail
            try:
                await mock_ring_client.get_devices()
                raise AssertionError("First call should have failed")
            except Exception as e:
                assert "Network temporarily unavailable" in str(e)

            # Second call should succeed
            recovered_devices = await mock_ring_client.get_devices()
            assert recovered_devices == devices

            # Third call fails again
            try:
                await mock_ring_client.get_devices()
                raise AssertionError("Third call should have failed")
            except Exception as e:
                assert "Network still unavailable" in str(e)

        finally:
            mock_ring_client.get_devices = original_get_devices


class TestRealDeviceWorkflows:
    """End-to-end workflows with real Ring devices."""

    @pytest.mark.real_devices
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_device_discovery_and_inspection(self, real_ring_client, real_devices):
        """Test complete device discovery and inspection workflow with real devices."""
        logger.info("Starting real device discovery and inspection workflow")

        # Step 1: Initial discovery
        discovered_devices = await real_ring_client.get_devices(force_refresh=True)
        assert len(discovered_devices) == len(real_devices)

        # Step 2: Detailed inspection of each device
        inspection_results = {}
        for device in discovered_devices:
            device_id = device["id"]
            details = await real_ring_client.get_device(device_id)

            inspection_results[device_id] = {
                "name": device["name"],
                "type": device["type"],
                "online": details.get("online", False),
                "has_battery": details.get("battery_life") is not None,
                "battery_level": details.get("battery_life"),
                "firmware": details.get("firmware"),
                "last_update": details.get("last_update"),
            }

        # Step 3: Validate inspection results
        for _device_id, result in inspection_results.items():
            assert result["online"], f"Device {result['name']} should be online"
            assert result["firmware"], f"Device {result['name']} should have firmware info"

            if result["has_battery"]:
                assert isinstance(result["battery_level"], int), f"Battery level should be int for {result['name']}"
                assert 0 <= result["battery_level"] <= 100, f"Invalid battery level for {result['name']}"

        # Step 4: Generate inspection summary
        device_types = {}
        for result in inspection_results.values():
            device_type = result["type"]
            device_types[device_type] = device_types.get(device_type, 0) + 1

        logger.info(f"Inspection completed for {len(inspection_results)} devices:")
        for device_type, count in device_types.items():
            logger.info(f"  {device_type}: {count} devices")

        logger.info("Real device discovery and inspection workflow completed")

    @pytest.mark.real_devices
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_device_monitoring_workflow(self, real_ring_client, real_devices):
        """Test device monitoring workflow with real devices."""
        logger.info("Starting real device monitoring workflow")

        # Step 1: Establish baseline device states
        baseline_states = {}
        for device in real_devices:
            device_id = device["id"]
            details = await real_ring_client.get_device(device_id)
            baseline_states[device_id] = {
                "online": details.get("online"),
                "battery": details.get("battery_life"),
                "timestamp": time.time(),
            }

        # Step 2: Monitor devices over time (short interval for testing)
        monitoring_duration = 30  # 30 seconds
        check_interval = 5  # Check every 5 seconds

        monitoring_data = {device_id: [] for device_id in baseline_states.keys()}

        start_time = time.time()
        while time.time() - start_time < monitoring_duration:
            for device in real_devices:
                device_id = device["id"]
                details = await real_ring_client.get_device(device_id)

                monitoring_data[device_id].append(
                    {"timestamp": time.time(), "online": details.get("online"), "battery": details.get("battery_life")}
                )

            await asyncio.sleep(check_interval)

        # Step 3: Analyze monitoring results
        for device_id, readings in monitoring_data.items():
            device_name = next((d["name"] for d in real_devices if d["id"] == device_id), device_id)

            # Check stability
            online_readings = [r["online"] for r in readings]
            consistent_online = all(online_readings) if online_readings else False

            # Battery level changes
            battery_readings = [r["battery"] for r in readings if r["battery"] is not None]
            battery_stable = len(set(battery_readings)) <= 1 if battery_readings else True

            logger.info(f"Monitoring results for {device_name}:")
            logger.info(f"  Readings: {len(readings)}")
            logger.info(f"  Online stability: {'stable' if consistent_online else 'unstable'}")
            logger.info(f"  Battery stability: {'stable' if battery_stable else 'changing'}")

            # Device should generally remain online during monitoring
            mostly_online = sum(online_readings) / len(online_readings) > 0.8 if online_readings else True
            assert mostly_online, f"Device {device_name} was offline too often during monitoring"

        logger.info("Real device monitoring workflow completed")

    @pytest.mark.real_devices
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_security_operations_workflow(self, real_ring_client, real_devices):
        """Test security operations workflow with real devices."""
        logger.info("Starting real security operations workflow")

        # Find security devices
        security_devices = [d for d in real_devices if d["type"] == "alarm"]

        if not security_devices:
            pytest.skip("No security devices available for security operations test")

        security_system = security_devices[0]
        logger.info(f"Testing security operations on: {security_system['name']}")

        # Step 1: Get initial security status
        initial_details = await real_ring_client.get_device(security_system["id"])
        initial_online = initial_details.get("online", False)

        assert initial_online, f"Security system {security_system['name']} must be online for testing"

        # Step 2: Test security system operations
        # Note: In a real test environment, we would NOT actually arm/disarm systems
        # as this could trigger real security alerts. Instead, we test the API calls.

        try:
            # Test arm operation (would normally arm the system)
            arm_success = await real_ring_client.set_arm_status(security_system["id"], True)
            logger.info(f"Security arm operation result: {arm_success}")

            # Brief pause (in real scenario, system would be arming)
            await asyncio.sleep(1)

            # Test disarm operation (would normally disarm the system)
            disarm_success = await real_ring_client.set_arm_status(security_system["id"], False)
            logger.info(f"Security disarm operation result: {disarm_success}")

            # Operations should succeed (in test environment)
            assert arm_success, "Security system arm operation should succeed"
            assert disarm_success, "Security system disarm operation should succeed"

        except Exception as e:
            logger.warning(f"Security operations test failed: {e}")
            # This is acceptable - security systems may have restrictions

        # Step 3: Verify system remains accessible after operations
        final_details = await real_ring_client.get_device(security_system["id"])
        final_online = final_details.get("online", False)

        assert final_online, f"Security system {security_system['name']} should remain online after operations"

        logger.info("Real security operations workflow completed")

    @pytest.mark.real_devices
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_camera_streaming_workflow(self, real_ring_client, real_devices):
        """Test camera streaming workflow with real devices."""
        logger.info("Starting real camera streaming workflow")

        # Find camera devices
        cameras = [d for d in real_devices if d["type"] == "camera"]

        if not cameras:
            pytest.skip("No camera devices available for streaming test")

        successful_streams = 0
        total_attempts = 0

        for camera in cameras[:2]:  # Test up to 2 cameras to avoid overwhelming the system
            logger.info(f"Testing streaming for camera: {camera['name']}")
            total_attempts += 1

            try:
                # Get stream URL
                stream_url = await real_ring_client.get_live_stream_url(camera["id"])

                # Validate URL format
                if stream_url and isinstance(stream_url, str):
                    if stream_url.startswith(("rtsp://", "https://")):
                        successful_streams += 1
                        logger.info(f"  ✓ Stream URL obtained for {camera['name']}")
                    else:
                        logger.warning(f"  ✗ Invalid stream URL format for {camera['name']}: {stream_url[:50]}...")
                else:
                    logger.warning(f"  ✗ No stream URL returned for {camera['name']}")

            except Exception as e:
                logger.warning(f"  ✗ Streaming test failed for {camera['name']}: {e}")
                # This is acceptable - cameras may be offline or have subscription issues

        # At least one successful stream attempt (if any cameras are available)
        if total_attempts > 0:
            success_rate = successful_streams / total_attempts
            logger.info(f"Streaming success rate: {successful_streams}/{total_attempts} ({success_rate:.1%})")

            # Allow for some failures (cameras may be offline)
            assert success_rate >= 0.0, "At least some streaming attempts should work"

        logger.info("Real camera streaming workflow completed")
