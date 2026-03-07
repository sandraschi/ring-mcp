#!/usr/bin/env python3
"""
Comprehensive test runner for Ring MCP.

This script provides intelligent test execution based on environment capabilities,
with options for mock-only, real device, and mixed testing scenarios.
"""
import asyncio
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import from the correct location
from tests.conftest import detect_test_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestRunner:
    """Intelligent test runner for Ring MCP."""

    def __init__(self):
        self.env = detect_test_environment()
        self.project_root = project_root

    def get_test_command(self, test_type: str, markers: Optional[List[str]] = None) -> List[str]:
        """Generate pytest command for specific test type."""
        cmd = ["python", "-m", "pytest"]

        # Base test path
        if test_type == "unit":
            cmd.extend(["tests/test_unit_mock.py", "tests/test_utilities.py"])
        elif test_type == "integration":
            cmd.extend(["tests/test_integration_real.py"])
        elif test_type == "end_to_end":
            cmd.extend(["tests/test_end_to_end.py"])
        elif test_type == "device_discovery":
            cmd.extend(["tests/test_device_discovery.py"])
        elif test_type == "all":
            cmd.extend(["tests/"])
        else:
            cmd.extend([f"tests/test_{test_type}.py"])

        # Add markers if specified
        if markers:
            marker_expr = " or ".join(markers)
            cmd.extend(["-m", marker_expr])

        # Add environment-specific options
        if self.env["mock_mode"]:
            cmd.extend(["-m", "not real_devices"])
        else:
            # In real mode, allow both mock and real tests
            pass

        return cmd

    def run_command(self, cmd: List[str]) -> int:
        """Run a command and return exit code."""
        import subprocess

        logger.info(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            return result.returncode
        except Exception as e:
            logger.error(f"Failed to run command: {e}")
            return 1

    def run_unit_tests(self) -> int:
        """Run unit tests with mocks."""
        logger.info("Running unit tests with mocks...")
        cmd = self.get_test_command("unit")
        return self.run_command(cmd)

    def run_integration_tests(self) -> int:
        """Run integration tests (may include real devices)."""
        if self.env["mock_mode"]:
            logger.info("Mock mode: Skipping integration tests that require real devices")
            return 0

        logger.info("Running integration tests...")
        cmd = self.get_test_command("integration")
        return self.run_command(cmd)

    def run_device_discovery_tests(self) -> int:
        """Run device discovery tests."""
        logger.info("Running device discovery tests...")
        cmd = self.get_test_command("device_discovery")
        return self.run_command(cmd)

    def run_end_to_end_tests(self) -> int:
        """Run end-to-end workflow tests."""
        if self.env["mock_mode"]:
            logger.info("Running end-to-end tests in mock mode...")
            cmd = self.get_test_command("end_to_end", ["not real_devices"])
        else:
            logger.info("Running end-to-end tests with real devices...")
            cmd = self.get_test_command("end_to_end")

        return self.run_command(cmd)

    def run_all_tests(self) -> int:
        """Run all applicable tests."""
        logger.info("Running all applicable tests...")

        results = []

        # Always run unit tests
        results.append(("Unit Tests", self.run_unit_tests()))

        # Run device discovery tests
        results.append(("Device Discovery", self.run_device_discovery_tests()))

        # Run integration tests if not in mock mode
        if not self.env["mock_mode"]:
            results.append(("Integration Tests", self.run_integration_tests()))
            results.append(("End-to-End Tests", self.run_end_to_end_tests()))
        else:
            logger.info("Skipping integration and end-to-end tests in mock mode")
            # Still run end-to-end tests with mocks
            results.append(("End-to-End Tests (Mock)", self.run_end_to_end_tests()))

        # Summary
        passed = sum(1 for _, code in results if code == 0)
        total = len(results)

        logger.info(f"\nTest Summary: {passed}/{total} test suites passed")

        for name, code in results:
            status = "✓ PASS" if code == 0 else f"✗ FAIL ({code})"
            logger.info(f"  {name}: {status}")

        return 0 if passed == total else 1

    def run_performance_tests(self) -> int:
        """Run performance-focused tests."""
        logger.info("Running performance tests...")
        # Focus on tests that measure timing
        cmd = [
            "python", "-m", "pytest",
            "tests/test_end_to_end.py::TestWorkflowPerformance",
            "-v", "--tb=short"
        ]
        return self.run_command(cmd)

    def run_smoke_tests(self) -> int:
        """Run quick smoke tests to verify basic functionality."""
        logger.info("Running smoke tests...")
        cmd = [
            "python", "-m", "pytest",
            "tests/test_basic.py",
            "tests/test_unit_mock.py::TestMockDeviceManagement::test_get_devices_success",
            "-v", "--tb=short"
        ]
        return self.run_command(cmd)

    def show_environment_info(self):
        """Display environment information."""
        print("\n" + "="*60)
        print("RING MCP TEST ENVIRONMENT")
        print("="*60)

        print(f"Mock Mode: {'[ENABLED]' if self.env['mock_mode'] else '[DISABLED]'}")
        print(f"Ring Credentials: {'[CONFIGURED]' if self.env['ring_credentials_configured'] else '[NOT CONFIGURED]'}")
        print(f"Real Devices Available: {'[YES]' if self.env['real_devices_available'] else '[NO]'}")
        print(f"Real Device Count: {self.env['real_device_count']}")

        if self.env['detected_devices']:
            print("\nDetected Devices:")
            for device in self.env['detected_devices'][:5]:  # Show first 5
                online_status = "[ONLINE]" if device.get('online') else "[OFFLINE]"
                print(f"  - {device.get('name', 'Unknown')} ({device.get('type', 'unknown')}) - {online_status}")

            if len(self.env['detected_devices']) > 5:
                print(f"  ... and {len(self.env['detected_devices']) - 5} more")

        # Test recommendations
        print("\nRecommended Test Commands:")
        if self.env['mock_mode']:
            print("  python tests/run_tests.py unit        # Unit tests with mocks")
            print("  python tests/run_tests.py smoke       # Quick functionality check")
        else:
            print("  python tests/run_tests.py all         # Full test suite")
            print("  python tests/run_tests.py integration # Real device integration")

        print("="*60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Ring MCP Test Runner")
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "device_discovery", "end_to_end", "all", "performance", "smoke", "info"],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    runner = TestRunner()

    if args.test_type == "info":
        runner.show_environment_info()
        return 0

    # Run the requested test type
    test_methods = {
        "unit": runner.run_unit_tests,
        "integration": runner.run_integration_tests,
        "device_discovery": runner.run_device_discovery_tests,
        "end_to_end": runner.run_end_to_end_tests,
        "all": runner.run_all_tests,
        "performance": runner.run_performance_tests,
        "smoke": runner.run_smoke_tests,
    }

    method = test_methods.get(args.test_type)
    if method:
        exit_code = method()
        sys.exit(exit_code)
    else:
        logger.error(f"Unknown test type: {args.test_type}")
        sys.exit(1)


if __name__ == "__main__":
    main()