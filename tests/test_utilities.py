"""
Test utilities and helpers for Ring MCP testing.

This module provides:
- Test data generators
- Mock creation utilities
- Test scenario builders
- Performance testing helpers
- Validation utilities
"""
import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from unittest.mock import AsyncMock, MagicMock
import logging

from tests.conftest import TEST_CONFIG, TestDeviceData

logger = logging.getLogger(__name__)


class TestDataGenerator:
    """Generate realistic test data for Ring devices and events."""

    DEVICE_TYPES = ["doorbell", "camera", "alarm", "sensor"]
    CAMERA_MODELS = ["Ring Spotlight Cam Pro", "Ring Floodlight Cam", "Ring Indoor Cam", "Ring Stick Up Cam"]
    DOORBELL_MODELS = ["Ring Video Doorbell Pro", "Ring Video Doorbell Wired", "Ring Video Doorbell Elite"]
    ALARM_MODELS = ["Ring Alarm Pro", "Ring Alarm 5-piece kit", "Ring Alarm Contact Sensor"]
    SENSOR_MODELS = ["Ring Contact Sensor", "Ring Motion Sensor", "Ring Flood/Freeze Sensor"]

    LOCATIONS = ["Front Door", "Back Door", "Driveway", "Garage", "Living Room", "Kitchen", "Basement"]
    TIMEZONES = ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "Europe/Vienna"]

    @classmethod
    def generate_device(cls,
                       device_type: Optional[str] = None,
                       online: Optional[bool] = None,
                       battery_level: Optional[int] = None,
                       location: Optional[str] = None) -> Dict[str, Any]:
        """Generate a single test device with realistic data."""
        if device_type is None:
            device_type = random.choice(cls.DEVICE_TYPES)

        device_id = f"{device_type}-{random.randint(100, 999)}"

        if location is None:
            location = random.choice(cls.Locations)

        name = f"{location} {device_type.title()}"

        # Generate model based on type
        if device_type == "camera":
            model = random.choice(cls.CAMERA_MODELS)
        elif device_type == "doorbell":
            model = random.choice(cls.DOORBELL_MODELS)
        elif device_type == "alarm":
            model = random.choice(cls.ALARM_MODELS)
        elif device_type == "sensor":
            model = random.choice(cls.SENSOR_MODELS)
        else:
            model = f"Ring {device_type.title()} Device"

        # Generate battery level (None for wired devices)
        if battery_level is None:
            if device_type in ["alarm", "doorbell"] and random.random() < 0.3:
                # 30% chance of wired devices for these types
                battery_level = None
            else:
                battery_level = random.randint(10, 100)

        # Generate online status
        if online is None:
            online = random.random() > 0.1  # 90% chance of being online

        # Generate firmware version
        firmware = f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

        # Generate timestamps
        now = datetime.now()
        last_update = now - timedelta(minutes=random.randint(0, 1440))  # Within last 24 hours

        return {
            "id": device_id,
            "name": name,
            "type": device_type,
            "model": model,
            "firmware": firmware,
            "battery_life": battery_level,
            "online": online,
            "address": f"123 {location} St",
            "timezone": random.choice(cls.TIMEZONES),
            "has_subscription": random.random() > 0.2,  # 80% have subscriptions
            "last_update": last_update.isoformat() + "Z"
        }

    @classmethod
    def generate_device_list(cls,
                           count: int = 5,
                           device_types: Optional[List[str]] = None,
                           online_ratio: float = 0.9) -> List[Dict[str, Any]]:
        """Generate a list of test devices."""
        devices = []

        if device_types is None:
            device_types = cls.DEVICE_TYPES

        for i in range(count):
            device_type = random.choice(device_types)
            online = random.random() < online_ratio
            device = cls.generate_device(device_type=device_type, online=online)
            devices.append(device)

        return devices

    @classmethod
    def generate_event(cls,
                      device_id: str,
                      event_type: Optional[str] = None,
                      age_minutes: Optional[int] = None) -> Dict[str, Any]:
        """Generate a single test event."""
        if event_type is None:
            event_type = random.choice(["motion", "doorbell", "alarm"])

        if age_minutes is None:
            age_minutes = random.randint(0, 1440)  # Within last 24 hours

        created_at = datetime.now() - timedelta(minutes=age_minutes)

        event = {
            "id": f"event-{random.randint(10000, 99999)}",
            "created_at": created_at.isoformat() + "Z",
            "answered": random.random() > 0.7 if event_type == "doorbell" else False,
            "kind": event_type,
            "recording_status": "ready" if random.random() > 0.1 else "processing"
        }

        return event

    @classmethod
    def generate_event_list(cls,
                          device_id: str,
                          count: int = 10,
                          event_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Generate a list of test events for a device."""
        events = []

        for i in range(count):
            # Events get progressively older
            age_minutes = i * random.randint(10, 60)
            event = cls.generate_event(device_id, age_minutes=age_minutes)
            events.append(event)

        return events

    @classmethod
    def generate_stream_url(cls, device_id: str) -> str:
        """Generate a mock stream URL."""
        return f"rtsp://stream.ring.com/live/{device_id}?token={random.randint(100000, 999999)}&expires={int(time.time()) + 300}"


class MockBuilder:
    """Build comprehensive mocks for Ring MCP testing."""

    @staticmethod
    def create_ring_client_mock(device_data: Optional[List[Dict[str, Any]]] = None,
                               event_data: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> MagicMock:
        """Create a comprehensive Ring client mock."""
        from ring_mcp.core.ring_client_modern import RingClient

        mock_client = MagicMock(spec=RingClient)

        # Set up device data
        if device_data is None:
            device_data = TestDataGenerator.generate_device_list(3)

        mock_client.get_devices = AsyncMock(return_value=device_data)

        # Set up device details
        def mock_get_device(device_id: str):
            for device in device_data:
                if device["id"] == device_id:
                    return device
            return None

        mock_client.get_device = AsyncMock(side_effect=mock_get_device)

        # Set up events
        if event_data is None:
            event_data = {}
            for device in device_data:
                if device["type"] in ["doorbell", "camera"]:
                    event_data[device["id"]] = TestDataGenerator.generate_event_list(device["id"], 5)

        def mock_get_events(device_id: str, limit: int = 10):
            return event_data.get(device_id, [])[:limit]

        mock_client.get_device_events = AsyncMock(side_effect=mock_get_events)

        # Set up streaming
        def mock_get_stream_url(device_id: str):
            return TestDataGenerator.generate_stream_url(device_id)

        mock_client.get_live_stream_url = AsyncMock(side_effect=mock_get_stream_url)

        # Set up security operations
        mock_client.set_arm_status = AsyncMock(return_value=True)
        mock_client.trigger_chime = AsyncMock(return_value=True)

        return mock_client

    @staticmethod
    def create_scenario_mock(scenario: str) -> MagicMock:
        """Create a mock for specific test scenarios."""
        if scenario == "all_offline":
            devices = TestDataGenerator.generate_device_list(3, online_ratio=0.0)
            return MockBuilder.create_ring_client_mock(devices)

        elif scenario == "mixed_battery":
            devices = []
            # Create mix of battery and wired devices
            for i in range(3):
                device = TestDataGenerator.generate_device()
                if i == 0:
                    device["battery_life"] = None  # Wired
                elif i == 1:
                    device["battery_life"] = 15   # Low battery
                else:
                    device["battery_life"] = 85   # Good battery
                devices.append(device)
            return MockBuilder.create_ring_client_mock(devices)

        elif scenario == "no_subscriptions":
            devices = TestDataGenerator.generate_device_list(3)
            for device in devices:
                device["has_subscription"] = False
            return MockBuilder.create_ring_client_mock(devices)

        elif scenario == "network_errors":
            mock_client = MockBuilder.create_ring_client_mock()
            mock_client.get_devices = AsyncMock(side_effect=Exception("Network timeout"))
            return mock_client

        elif scenario == "auth_errors":
            from ring_mcp.core.exceptions import AuthenticationError
            mock_client = MockBuilder.create_ring_client_mock()
            mock_client.get_devices = AsyncMock(side_effect=AuthenticationError("Invalid credentials"))
            return mock_client

        else:
            return MockBuilder.create_ring_client_mock()


class TestScenario:
    """Define and run test scenarios."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.setup_steps: List[Callable] = []
        self.test_steps: List[Callable] = []
        self.cleanup_steps: List[Callable] = []

    def add_setup(self, step: Callable):
        """Add a setup step."""
        self.setup_steps.append(step)

    def add_test(self, step: Callable):
        """Add a test step."""
        self.test_steps.append(step)

    def add_cleanup(self, step: Callable):
        """Add a cleanup step."""
        self.cleanup_steps.append(step)

    async def run(self):
        """Run the complete scenario."""
        logger.info(f"Running scenario: {self.name}")
        logger.info(f"Description: {self.description}")

        try:
            # Setup
            for step in self.setup_steps:
                await step()

            # Test
            for step in self.test_steps:
                await step()

        finally:
            # Cleanup
            for step in self.cleanup_steps:
                try:
                    await step()
                except Exception as e:
                    logger.warning(f"Cleanup step failed: {e}")


class PerformanceTester:
    """Test performance characteristics."""

    @staticmethod
    async def measure_operation_time(operation: Callable, *args, **kwargs) -> float:
        """Measure the execution time of an async operation."""
        start_time = time.time()
        result = await operation(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time, result

    @staticmethod
    async def benchmark_operation(operation: Callable,
                                iterations: int = 10,
                                *args, **kwargs) -> Dict[str, float]:
        """Benchmark an operation over multiple iterations."""
        times = []

        for i in range(iterations):
            duration, _ = await PerformanceTester.measure_operation_time(operation, *args, **kwargs)
            times.append(duration)

        return {
            "min_time": min(times),
            "max_time": max(times),
            "avg_time": sum(times) / len(times),
            "total_time": sum(times),
            "iterations": iterations
        }

    @staticmethod
    async def test_concurrent_operations(operation: Callable,
                                       concurrency: int = 5,
                                       *args, **kwargs) -> Dict[str, Any]:
        """Test operation performance under concurrent load."""
        start_time = time.time()

        tasks = [operation(*args, **kwargs) for _ in range(concurrency)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        total_time = end_time - start_time

        return {
            "total_time": total_time,
            "avg_time_per_operation": total_time / concurrency,
            "concurrency": concurrency,
            "results": results
        }


class ValidationUtils:
    """Utilities for validating test data and results."""

    @staticmethod
    def validate_device_response(device: Dict[str, Any]) -> List[str]:
        """Validate a device response structure."""
        errors = []

        required_fields = ["id", "name", "type", "online"]
        for field in required_fields:
            if field not in device:
                errors.append(f"Missing required field: {field}")

        if "id" in device and not isinstance(device["id"], str):
            errors.append("Device ID must be a string")

        if "name" in device and not isinstance(device["name"], str):
            errors.append("Device name must be a string")

        if "type" in device and device["type"] not in ["doorbell", "camera", "alarm", "sensor"]:
            errors.append(f"Invalid device type: {device['type']}")

        if "online" in device and not isinstance(device["online"], bool):
            errors.append("Device online status must be a boolean")

        if "battery_life" in device and device["battery_life"] is not None:
            battery = device["battery_life"]
            if not isinstance(battery, int) or not (0 <= battery <= 100):
                errors.append(f"Invalid battery level: {battery}")

        return errors

    @staticmethod
    def validate_event_response(event: Dict[str, Any]) -> List[str]:
        """Validate an event response structure."""
        errors = []

        required_fields = ["id", "created_at", "kind"]
        for field in required_fields:
            if field not in event:
                errors.append(f"Missing required field: {field}")

        if "kind" in event and event["kind"] not in ["motion", "doorbell", "alarm"]:
            errors.append(f"Invalid event kind: {event['kind']}")

        if "answered" in event and not isinstance(event["answered"], bool):
            errors.append("Event answered status must be a boolean")

        return errors

    @staticmethod
    def validate_api_response(response: Dict[str, Any], expected_fields: List[str]) -> List[str]:
        """Validate a general API response."""
        errors = []

        for field in expected_fields:
            if field not in response:
                errors.append(f"Missing expected field: {field}")

        if "success" in response and not isinstance(response["success"], bool):
            errors.append("Success field must be a boolean")

        return errors


class TestDataManager:
    """Manage test data persistence and loading."""

    @staticmethod
    def save_test_data(filename: str, data: Any) -> Path:
        """Save test data to a file."""
        file_path = TEST_CONFIG["test_data_dir"] / filename

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return file_path

    @staticmethod
    def load_test_data(filename: str) -> Any:
        """Load test data from a file."""
        file_path = TEST_CONFIG["test_data_dir"] / filename

        if not file_path.exists():
            raise FileNotFoundError(f"Test data file not found: {file_path}")

        with open(file_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def generate_and_save_scenario(scenario_name: str, device_count: int = 5) -> Path:
        """Generate and save a complete test scenario."""
        devices = TestDataGenerator.generate_device_list(device_count)

        # Generate events for cameras and doorbells
        events = {}
        for device in devices:
            if device["type"] in ["camera", "doorbell"]:
                events[device["id"]] = TestDataGenerator.generate_event_list(device["id"], 10)

        scenario_data = {
            "name": scenario_name,
            "devices": devices,
            "events": events,
            "generated_at": datetime.now().isoformat()
        }

        filename = f"scenario_{scenario_name}.json"
        return TestDataManager.save_test_data(filename, scenario_data)


# Convenience functions for common test operations
def create_standard_mock_client() -> MagicMock:
    """Create a standard mock client for most tests."""
    return MockBuilder.create_ring_client_mock()

def create_scenario_mock(scenario: str) -> MagicMock:
    """Create a mock client for a specific scenario."""
    return MockBuilder.create_scenario_mock(scenario)

def generate_test_devices(count: int = 3) -> List[Dict[str, Any]]:
    """Generate a standard set of test devices."""
    return TestDataGenerator.generate_device_list(count)

def validate_device_list(devices: List[Dict[str, Any]]) -> List[str]:
    """Validate a list of devices."""
    all_errors = []
    for i, device in enumerate(devices):
        errors = ValidationUtils.validate_device_response(device)
        if errors:
            all_errors.extend([f"Device {i} ({device.get('id', 'unknown')}): {error}" for error in errors])
    return all_errors

# Export key classes and functions
__all__ = [
    "TestDataGenerator",
    "MockBuilder",
    "TestScenario",
    "PerformanceTester",
    "ValidationUtils",
    "TestDataManager",
    "create_standard_mock_client",
    "create_scenario_mock",
    "generate_test_devices",
    "validate_device_list"
]