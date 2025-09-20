"""
FastMCP Test Client for Ring MCP.

This module provides a test client for the Ring MCP server that can be used for
automated testing and integration with other systems.
"""
import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import httpx
from fastmcp import FastMCPClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class RingMCPTestClient:
    """Test client for the Ring MCP server."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize the test client.
        
        Args:
            base_url: Base URL of the Ring MCP server
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        ""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
            
        # Initialize FastMCP client
        self.client = FastMCPClient(
            base_url=base_url,
            headers=self.headers,
            timeout=timeout,
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.client.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.close()
    
    async def get_health(self) -> Dict[str, Any]:
        """Get server health status."""
        try:
            return await self.client.call("health")
        except Exception as e:
            logger.error("Health check failed: %s", str(e))
            raise
    
    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get all Ring devices."""
        try:
            return await self.client.call("get_devices")
        except Exception as e:
            logger.error("Failed to get devices: %s", str(e))
            raise
    
    async def get_device_details(self, device_id: str) -> Dict[str, Any]:
        """Get details for a specific device."""
        try:
            return await self.client.call("get_device_details", {"device_id": device_id})
        except Exception as e:
            logger.error("Failed to get device details: %s", str(e))
            raise
    
    async def get_device_events(
        self, 
        device_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get events for a specific device."""
        try:
            return await self.client.call("get_device_events", {
                "device_id": device_id,
                "limit": limit
            })
        except Exception as e:
            logger.error("Failed to get device events: %s", str(e))
            raise
    
    async def get_live_stream_url(self, device_id: str) -> str:
        """Get a live stream URL for a camera device."""
        try:
            return await self.client.call("get_live_stream_url", {"device_id": device_id})
        except Exception as e:
            logger.error("Failed to get live stream URL: %s", str(e))
            raise
    
    async def set_arm_status(self, device_id: str, status: bool) -> bool:
        """Arm or disarm a security device."""
        try:
            return await self.client.call("set_arm_status", {
                "device_id": device_id,
                "status": status
            })
        except Exception as e:
            logger.error("Failed to set arm status: %s", str(e))
            raise
    
    async def trigger_chime(self, device_id: str) -> bool:
        """Trigger a doorbell chime."""
        try:
            return await self.client.call("trigger_chime", {"device_id": device_id})
        except Exception as e:
            logger.error("Failed to trigger chime: %s", str(e))
            raise


async def run_tests():
    """Run a series of tests against the Ring MCP server."""
    # Get configuration from environment variables
    base_url = os.getenv("RING_MCP_URL", "http://localhost:8000")
    api_key = os.getenv("RING_MCP_API_KEY")
    
    print(f"Testing Ring MCP server at {base_url}")
    
    async with RingMCPTestClient(base_url=base_url, api_key=api_key) as client:
        # Test health check
        print("\n=== Testing health check ===")
        health = await client.get_health()
        print(f"Server health: {health}")
        
        # Test getting devices
        print("\n=== Testing device listing ===")
        devices = await client.get_devices()
        print(f"Found {len(devices)} devices")
        
        if devices:
            # Test getting device details for the first device
            first_device = devices[0]
            print(f"\n=== Testing device details for {first_device['name']} ===")
            details = await client.get_device_details(first_device['id'])
            print(f"Device details: {json.dumps(details, indent=2, default=str)}")
            
            # Test getting device events if supported
            if details.get('type') in ['doorbell', 'camera']:
                print(f"\n=== Testing device events for {first_device['name']} ===")
                events = await client.get_device_events(first_device['id'], limit=3)
                print(f"Found {len(events)} recent events")
                for event in events:
                    print(f"- {event.get('created_at')}: {event.get('kind')}")
            
            # Test live stream URL for cameras
            if details.get('type') in ['doorbell', 'camera'] and details.get('online'):
                print(f"\n=== Testing live stream URL for {first_device['name']} ===")
                try:
                    stream_url = await client.get_live_stream_url(first_device['id'])
                    print(f"Live stream URL: {stream_url}")
                except Exception as e:
                    print(f"Could not get live stream URL: {str(e)}")
            
            # Test arming/disarming for security devices
            if details.get('type') in ['alarm', 'security-panel']:
                print(f"\n=== Testing arm status for {first_device['name']} ===")
                current_status = details.get('alarm', {}).get('status')
                print(f"Current status: {current_status}")
                
                # Toggle the status
                new_status = not bool(current_status == 'armed')
                print(f"Setting status to: {'armed' if new_status else 'disarmed'}")
                
                result = await client.set_arm_status(first_device['id'], new_status)
                print(f"Operation {'succeeded' if result else 'failed'}")
                
                # Verify the new status
                updated_details = await client.get_device_details(first_device['id'])
                print(f"New status: {updated_details.get('alarm', {}).get('status')}")
            
            # Test chime for doorbells
            if details.get('type') == 'doorbell' and details.get('online'):
                print(f"\n=== Testing chime for {first_device['name']} ===")
                print("Triggering chime...")
                result = await client.trigger_chime(first_device['id'])
                print(f"Chime {'triggered successfully' if result else 'failed to trigger'}")


if __name__ == "__main__":
    asyncio.run(run_tests())
