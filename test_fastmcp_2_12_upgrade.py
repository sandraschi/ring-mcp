#!/usr/bin/env python3
"""
Test script to verify FastMCP 2.12 upgrade is working correctly.

This script tests the key FastMCP 2.12 features:
- Multiline decorators
- Proper stdio communication
- Tool registration patterns
- Response models
"""

import sys
import os
import asyncio
from pathlib import Path

def test_fastmcp_version():
    """Test that FastMCP 2.12 is installed and working."""
    print("Testing FastMCP 2.12 installation...")

    try:
        import fastmcp
        print(f"✅ FastMCP version: {fastmcp.__version__}")

        # Check if it's version 2.12 or higher
        version_parts = fastmcp.__version__.split('.')
        major = int(version_parts[0])
        minor = int(version_parts[1])

        if major > 2 or (major == 2 and minor >= 12):
            print("✅ FastMCP 2.12+ detected")
            return True
        else:
            print(f"❌ FastMCP version {fastmcp.__version__} is too old. Need 2.12+")
            return False

    except ImportError:
        print("❌ FastMCP not installed")
        return False
    except Exception as e:
        print(f"❌ Error checking FastMCP version: {e}")
        return False

def test_multiline_decorators():
    """Test that multiline decorators work correctly."""
    print("\nTesting multiline decorators...")

    try:
        from fastmcp import FastMCP
        import inspect

        # Create a test app
        app = FastMCP("Test App", version="2.12.0")

        # Test multiline decorator
        @app.tool(
            name="test_tool",
            description="Test tool with multiline decorator"
        )
        async def test_tool(message: str) -> dict:
            """Test tool function."""
            return {"message": message}

        # Check if tool was registered correctly
        tools = app._tools
        if "test_tool" in tools:
            tool_info = tools["test_tool"]
            if hasattr(tool_info, 'description'):
                print("✅ Multiline decorator working correctly")
                return True
            else:
                print("❌ Tool registered but missing description")
                return False
        else:
            print("❌ Tool not registered with multiline decorator")
            return False

    except Exception as e:
        print(f"❌ Error testing multiline decorators: {e}")
        return False

def test_stdio_configuration():
    """Test that stdio transport is properly configured."""
    print("\nTesting stdio configuration...")

    try:
        from fastmcp import FastMCP

        # Create app with stdio transport
        app = FastMCP(
            name="Test App",
            version="2.12.0",
            transport=["stdio", "http"]
        )

        # Check if stdio transport is configured
        if hasattr(app, '_stdio_transport') or "stdio" in getattr(app, 'transport', []):
            print("✅ Stdio transport configured")
            return True
        else:
            print("❌ Stdio transport not configured")
            return False

    except Exception as e:
        print(f"❌ Error testing stdio configuration: {e}")
        return False

def test_response_models():
    """Test that response models work correctly."""
    print("\nTesting response models...")

    try:
        from fastmcp import FastMCP
        from pydantic import BaseModel, Field

        app = FastMCP("Test App", version="2.12.0")

        # Define a response model
        class TestResponse(BaseModel):
            success: bool = Field(..., description="Operation success status")
            message: str = Field(..., description="Response message")

        # Test tool with response model
        @app.tool(
            name="test_response_model",
            description="Test tool with response model",
            response_model=TestResponse
        )
        async def test_response_model() -> TestResponse:
            """Test response model function."""
            return TestResponse(success=True, message="Test successful")

        # Check if tool was registered with response model
        tools = app._tools
        if "test_response_model" in tools:
            print("✅ Response models working correctly")
            return True
        else:
            print("❌ Response model tool not registered")
            return False

    except Exception as e:
        print(f"❌ Error testing response models: {e}")
        return False

def test_tool_registration_patterns():
    """Test that tool registration patterns are correct."""
    print("\nTesting tool registration patterns...")

    try:
        from fastmcp import FastMCP

        app = FastMCP("Test App", version="2.12.0")

        # Test the new pattern
        @app.tool(
            name="test_registration",
            description="Test tool registration pattern"
        )
        async def test_registration() -> dict:
            """Test registration function."""
            return {"status": "registered"}

        # Check registration
        if "test_registration" in app._tools:
            print("✅ Tool registration patterns working correctly")
            return True
        else:
            print("❌ Tool registration patterns not working")
            return False

    except Exception as e:
        print(f"❌ Error testing tool registration patterns: {e}")
        return False

def test_ring_mcp_import():
    """Test that Ring MCP can be imported with FastMCP 2.12."""
    print("\nTesting Ring MCP import...")

    try:
        # Test importing the main server module
        from ring_mcp.server import app
        print("✅ Ring MCP server imports successfully")

        # Check if app has the right attributes
        if hasattr(app, 'name') and hasattr(app, 'version'):
            print(f"   App name: {app.name}")
            print(f"   App version: {app.version}")

            # Check for FastMCP 2.12 features
            if hasattr(app, '_tools'):
                tool_count = len(app._tools)
                print(f"   Tools registered: {tool_count}")

                # Check for stdio transport
                transport = getattr(app, 'transport', [])
                if "stdio" in transport:
                    print("   ✅ Stdio transport enabled")
                else:
                    print("   ❌ Stdio transport not enabled")
                    return False

                return True
            else:
                print("   ❌ No _tools attribute found")
                return False
        else:
            print("   ❌ App missing name or version")
            return False

    except ImportError as e:
        print(f"❌ Ring MCP import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing Ring MCP import: {e}")
        return False

def main():
    """Run all FastMCP 2.12 upgrade tests."""
    print("🔍 FastMCP 2.12 Upgrade Test Suite")
    print("=" * 50)

    tests = [
        ("FastMCP Version", test_fastmcp_version),
        ("Multiline Decorators", test_multiline_decorators),
        ("Stdio Configuration", test_stdio_configuration),
        ("Response Models", test_response_models),
        ("Tool Registration Patterns", test_tool_registration_patterns),
        ("Ring MCP Import", test_ring_mcp_import),
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

    print("\n" + "=" * 50)
    print("📊 Test Results:")

    passed = sum(results)
    total = len(results)

    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {status} - {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All FastMCP 2.12 upgrade tests passed!")
        print("\nNext steps:")
        print("1. Start Ring MCP: python -m ring_mcp")
        print("2. Test with Claude Desktop via stdio communication")
        print("3. Verify all tools are available with new patterns")
    else:
        print("⚠️  Some tests failed. Check the FastMCP 2.12 upgrade.")
        print("   Make sure all dependencies are installed: pip install -e .")
        sys.exit(1)

if __name__ == "__main__":
    main()
