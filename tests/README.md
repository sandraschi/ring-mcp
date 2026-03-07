# Ring MCP Testing Framework

Comprehensive testing scaffold for Ring MCP with support for both mock and real device testing.

## Overview

This testing framework provides:
- **Mock-based unit tests** for isolated functionality testing
- **Real device integration tests** for end-to-end validation
- **Device discovery and presence detection** utilities
- **Performance and workflow testing** capabilities
- **Intelligent environment detection** and test selection

## Quick Start

### Environment Setup

The test framework automatically detects your environment:

```bash
# Check test environment and recommendations
python tests/run_tests.py info
```

### Run Tests

```bash
# Run all applicable tests (auto-detects environment)
python tests/run_tests.py all

# Run specific test types
python tests/run_tests.py unit           # Unit tests with mocks
python tests/run_tests.py integration    # Real device integration
python tests/run_tests.py smoke          # Quick functionality check
python tests/run_tests.py performance    # Performance-focused tests
```

## Test Categories

### 🔧 Unit Tests (`test_unit_mock.py`)
- Isolated functionality testing with comprehensive mocks
- Covers all Ring MCP tools and core functions
- Fast execution, no external dependencies
- Tests error handling, edge cases, and data validation

### 🔗 Integration Tests (`test_integration_real.py`)
- Tests with real Ring devices and API
- Requires Ring credentials and accessible devices
- Validates end-to-end functionality
- Performance and reliability testing

### 🔍 Device Discovery (`test_device_discovery.py`)
- Device presence detection and validation
- Environment capability assessment
- Cache management for discovered devices
- Connectivity and authentication testing

### 🚀 End-to-End Workflows (`test_end_to_end.py`)
- Complete user workflow simulation
- Home security setup scenarios
- Device monitoring and control workflows
- Error recovery and resilience testing

### 🛠️ Utilities (`test_utilities.py`)
- Test data generation and validation
- Mock creation helpers
- Performance testing utilities
- Test scenario builders

## Environment Configuration

### Mock Mode (Default)
```bash
# No credentials needed - uses generated mock data
export RING_MCP_TEST_MODE=mock  # or don't set (default)
python tests/run_tests.py all
```

### Real Device Mode
```bash
# Requires Ring credentials and accessible devices
export RING_USERNAME="your@email.com"
export RING_PASSWORD="your_password"
export RING_MCP_TEST_MODE=real
python tests/run_tests.py all
```

### Auto-Detection
```bash
# Framework detects based on available credentials
# Set RING_USERNAME/PASSWORD for real device access
python tests/run_tests.py all  # Runs appropriate tests automatically
```

## Test Data

### Mock Data (`test_data/mock_devices.json`)
- 8 comprehensive test devices (doorbells, cameras, alarms, sensors)
- Realistic device configurations and states
- Battery levels, online status, firmware versions
- Subscription and location data

### Generated Test Data
```python
from tests.test_utilities import TestDataGenerator

# Generate custom test devices
devices = TestDataGenerator.generate_device_list(count=5, device_types=["camera", "doorbell"])

# Generate realistic events
events = TestDataGenerator.generate_event_list("device-123", count=10)
```

## Mock Creation

### Standard Mock Client
```python
from tests.conftest import mock_ring_client

async def test_my_function(mock_ring_client):
    devices = await mock_ring_client.get_devices()
    # Mock returns pre-configured test data
```

### Custom Scenario Mocks
```python
from tests.test_utilities import MockBuilder

# Create mock for specific scenarios
mock_client = MockBuilder.create_scenario_mock("all_offline")
mock_client = MockBuilder.create_scenario_mock("network_errors")
mock_client = MockBuilder.create_scenario_mock("auth_errors")
```

## Real Device Testing

### Prerequisites
- Valid Ring account with 2FA enabled
- At least one Ring device (doorbell, camera, or alarm)
- Internet connectivity to Ring services
- Appropriate permissions for device access

### Device Requirements
- **Doorbells**: Video Doorbell Pro, Wired, Elite
- **Cameras**: Spotlight Cam, Floodlight Cam, Indoor Cam
- **Alarms**: Ring Alarm systems
- **Sensors**: Contact sensors, motion sensors

### Test Safety
- **Security Operations**: Tests avoid actual arming/disarming of security systems
- **Chime Testing**: Limited to avoid disturbing household
- **Stream Testing**: Validates URL generation without extended streaming
- **Rate Limiting**: Respects Ring API limits with appropriate delays

## Test Fixtures

### Automatic Fixtures
```python
def test_with_mock_data(mock_device_data):
    """Access comprehensive mock device data"""
    assert len(mock_device_data) >= 8

def test_with_real_devices(real_devices):
    """Access real devices (skipped in mock mode)"""
    for device in real_devices:
        assert device["online"]
```

### Custom Fixtures
```python
@pytest.fixture
def sample_doorbell():
    """Single doorbell device for testing"""
    return {
        "id": "doorbell-001",
        "name": "Front Door",
        "type": "doorbell",
        "online": True,
        "battery_life": 85
    }
```

## Performance Testing

### Benchmark Operations
```python
from tests.test_utilities import PerformanceTester

# Measure operation performance
duration, result = await PerformanceTester.measure_operation_time(
    mock_ring_client.get_devices
)

# Run multiple iterations
results = await PerformanceTester.benchmark_operation(
    mock_ring_client.get_devices,
    iterations=10
)
print(f"Average time: {results['avg_time']:.3f}s")
```

### Concurrent Testing
```python
# Test concurrent device operations
results = await PerformanceTester.test_concurrent_operations(
    mock_ring_client.get_device,
    concurrency=5,
    device_ids=["device-1", "device-2", "device-3", "device-4", "device-5"]
)
```

## Test Utilities

### Data Validation
```python
from tests.test_utilities import ValidationUtils

# Validate device structure
errors = ValidationUtils.validate_device_response(device)
assert len(errors) == 0, f"Validation errors: {errors}"

# Validate event structure
errors = ValidationUtils.validate_event_response(event)
assert len(errors) == 0
```

### Test Data Management
```python
from tests.test_utilities import TestDataManager

# Save test scenario
filepath = TestDataManager.save_test_data("my_scenario.json", test_data)

# Load test scenario
data = TestDataManager.load_test_data("my_scenario.json")
```

## Pytest Integration

### Custom Markers
```python
@pytest.mark.real_devices
async def test_requires_real_devices(real_ring_client):
    """Only runs when real Ring devices are available"""

@pytest.mark.mock_only
def test_mock_functionality_only():
    """Only runs in mock mode"""

@pytest.mark.integration
async def test_full_integration():
    """Full integration test with real systems"""
```

### Configuration (`pytest.ini`)
```ini
[tool:pytest]
markers =
    mock_only: Tests that only run with mocks
    real_devices: Tests that require real Ring devices
    device_discovery: Tests that involve device discovery
    integration: Full integration tests
    slow: Tests that take longer to run
```

## CI/CD Integration

### Mock-Only Pipeline
```yaml
# For pull requests and basic validation
- name: Run Mock Tests
  run: python tests/run_tests.py unit
```

### Full Test Pipeline
```yaml
# For main branch and releases (requires secrets)
- name: Run Full Test Suite
  env:
    RING_USERNAME: ${{ secrets.RING_USERNAME }}
    RING_PASSWORD: ${{ secrets.RING_PASSWORD }}
    RING_MCP_TEST_MODE: real
  run: python tests/run_tests.py all
```

## Troubleshooting

### Common Issues

#### Tests Failing in CI/CD
```bash
# Force mock mode for CI
export RING_MCP_TEST_MODE=mock
python tests/run_tests.py unit
```

#### Real Device Tests Failing
```bash
# Check environment
python tests/run_tests.py info

# Verify credentials
export RING_USERNAME="your@email.com"
export RING_PASSWORD="your_password"

# Test connectivity
python tests/run_tests.py device_discovery
```

#### Mock Data Issues
```bash
# Regenerate mock data
python -c "from tests.test_utilities import TestDataGenerator; print(TestDataGenerator.generate_device_list(5))"
```

### Debug Mode
```bash
# Enable verbose logging
python tests/run_tests.py --verbose unit
```

## Contributing

### Adding New Tests
1. Follow existing patterns in test files
2. Use appropriate markers (`@pytest.mark.real_devices`, etc.)
3. Add comprehensive docstrings
4. Include both success and error scenarios
5. Test with both mock and real environments

### Test Data Updates
```python
# Update mock data file
from tests.test_utilities import TestDataManager, TestDataGenerator

new_devices = TestDataGenerator.generate_device_list(count=10)
TestDataManager.save_test_data("mock_devices.json", new_devices)
```

### Performance Baselines
- Device discovery: < 30 seconds
- Individual device query: < 5 seconds
- Concurrent operations: < 2 seconds for 5 devices
- Event retrieval: < 10 seconds for 50 events

---

## Test Environment Summary

| Environment | Credentials | Devices | Test Types | Speed |
|-------------|-------------|---------|------------|-------|
| **Mock Mode** | Not required | Generated | Unit, E2E | ⚡ Fast |
| **Real Mode** | Required | Live devices | Integration, E2E | 🐌 Slower |
| **Auto Mode** | Optional | As available | All applicable | ⚖️ Mixed |

Choose the appropriate environment based on your testing needs and available resources.