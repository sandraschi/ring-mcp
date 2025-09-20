#!/usr/bin/env python3
"""
Test script to verify monitoring setup is working correctly.
"""

import sys
import os
import time
import requests
from pathlib import Path

def test_ring_mcp_metrics():
    """Test that Ring MCP server exposes metrics endpoint."""
    print("Testing Ring MCP metrics endpoint...")

    try:
        # Check if server is running on port 8001 (metrics port)
        response = requests.get("http://localhost:8001/metrics", timeout=5)
        if response.status_code == 200:
            print("✅ Ring MCP metrics endpoint is accessible")
            print(f"   Response length: {len(response.text)} characters")

            # Check for expected metrics
            metrics_text = response.text
            expected_metrics = [
                'ring_api_calls_total',
                'ring_device_battery_percent',
                'ring_security_armed',
                'ring_tool_calls_total'
            ]

            found_metrics = []
            for metric in expected_metrics:
                if metric in metrics_text:
                    found_metrics.append(metric)
                    print(f"   ✅ Found metric: {metric}")
                else:
                    print(f"   ❌ Missing metric: {metric}")

            return len(found_metrics) == len(expected_metrics)
        else:
            print(f"❌ Metrics endpoint returned status {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ring MCP metrics endpoint")
        print("   Make sure Ring MCP server is running with: python -m ring_mcp")
        return False
    except Exception as e:
        print(f"❌ Error testing metrics endpoint: {e}")
        return False

def test_prometheus_config():
    """Test that Prometheus configuration is valid."""
    print("\nTesting Prometheus configuration...")

    config_path = Path("monitoring/prometheus/prometheus.yml")
    if config_path.exists():
        print("✅ Prometheus config file exists")

        # Basic syntax check by trying to read it
        try:
            with open(config_path) as f:
                content = f.read()
                if 'scrape_configs:' in content:
                    print("✅ Prometheus config appears valid")
                    return True
                else:
                    print("❌ Prometheus config missing scrape_configs section")
                    return False
        except Exception as e:
            print(f"❌ Error reading Prometheus config: {e}")
            return False
    else:
        print("❌ Prometheus config file not found")
        return False

def test_docker_compose():
    """Test that docker-compose configuration is valid."""
    print("\nTesting Docker Compose configuration...")

    compose_path = Path("docker-compose.yml")
    if compose_path.exists():
        print("✅ docker-compose.yml exists")

        try:
            with open(compose_path) as f:
                content = f.read()

            required_services = ['prometheus', 'grafana', 'loki', 'promtail', 'node-exporter']
            found_services = []

            for service in required_services:
                if f'  {service}:' in content:
                    found_services.append(service)
                    print(f"   ✅ Found service: {service}")
                else:
                    print(f"   ❌ Missing service: {service}")

            return len(found_services) == len(required_services)

        except Exception as e:
            print(f"❌ Error reading docker-compose.yml: {e}")
            return False
    else:
        print("❌ docker-compose.yml not found")
        return False

def main():
    """Run all tests."""
    print("🔍 Ring MCP Monitoring Setup Test")
    print("=" * 40)

    tests = [
        ("Ring MCP Metrics", test_ring_mcp_metrics),
        ("Prometheus Config", test_prometheus_config),
        ("Docker Compose", test_docker_compose),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 40)
    print("📊 Test Results:")

    passed = sum(results)
    total = len(results)

    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {status} - {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Your monitoring setup is ready.")
        print("\nNext steps:")
        print("1. Start monitoring stack: docker-compose up -d")
        print("2. Start Ring MCP server: python -m ring_mcp")
        print("3. Access Grafana: http://localhost:3000")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
