"""
Server Composition and Proxy for Ring MCP - FastMCP 3.4

This module provides functionality to compose multiple MCP servers together
and proxy requests between them, enabling a unified API for multiple services.

This module uses FastMCP 3.4 patterns with multiline decorators and proper
tool registration for Claude Desktop stdio communication.
"""

import logging
from typing import Annotated, Any

from fastmcp import Client, FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)


class MCPServerComposition:
    """Compose multiple MCP servers together with proxy capabilities."""

    def __init__(self, base_server: FastMCP):
        """Initialize the server composition.

        Args: See Parameters block.
        """
        self.base_server = base_server
        # namespace -> transport (URL string) for the peer server.
        self.connected_servers: dict[str, str] = {}
        # "namespace.tool" -> (namespace, tool) routing table.
        self.namespace_mapping: dict[str, tuple[str, str]] = {}

        # Register composition tools with the base server
        self._register_tools(base_server)

    def _client_for(self, namespace: str) -> Client:
        """Build a short-lived client for a connected peer (per-call lifecycle)."""
        return Client(self.connected_servers[namespace])

    def _register_tools(self, app: FastMCP) -> None:
        """Register composition and proxy tools with the base server.

        Args: See Parameters block.
        """

        @app.tool(
            name="list_connected_servers",
            description="List all connected MCP servers and their namespaces",
            annotations={"readOnlyHint": True, "idempotentHint": True},
            output_schema={
                "type": "object",
                "required": ["success"],
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "servers": {"type": "array"},
                },
            },
        )
        async def list_connected_servers() -> dict[str, Any]:
            """List all connected MCP servers and their namespaces.

            ## Return Format
            {"success": true, "message": "N server(s) connected", "servers": [...]}

            ## Examples
            await list_connected_servers()
            """
            servers = [
                {
                    "namespace": namespace,
                    "server_url": server_url,
                    "tools_registered": sum(1 for key in self.namespace_mapping if key.startswith(f"{namespace}.")),
                }
                for namespace, server_url in self.connected_servers.items()
            ]
            return {
                "success": True,
                "message": f"{len(servers)} server(s) connected",
                "servers": servers,
            }

        @app.tool(
            name="connect_server",
            description="Connect to another MCP server",
            annotations={"readOnlyHint": False, "idempotentHint": False},
            output_schema={
                "type": "object",
                "required": ["success"],
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "error": {"type": "string"},
                    "status": {"type": "string"},
                    "namespace": {"type": "string"},
                    "server_url": {"type": "string"},
                    "tools_registered": {"type": "array"},
                },
            },
        )
        async def connect_server(
            namespace: Annotated[str, Field(description="Namespace prefix for the peer tools.", min_length=1)],
            server_url: Annotated[str, Field(description="MCP server URL (http/https).", min_length=1)],
            api_key: Annotated[str | None, Field(description="Optional bearer token for the peer.")] = None,
        ) -> dict[str, Any]:
            """Connect to another MCP server.

            Probes the peer once to build the namespace routing table; every
            proxied call after that uses a short-lived client (no connections
            are held open between calls).

            ## Return Format
            {"success": true, "message": "Connected ...", "tools_registered": [...]}

            ## Examples
            await connect_server(namespace="ring2", server_url="http://127.0.0.1:10729/mcp")
            """
            if namespace in self.connected_servers:
                return {"success": False, "error": f"Namespace '{namespace}' is already in use"}

            try:
                client: Client = Client(server_url, auth=api_key) if api_key else Client(server_url)
                async with client:
                    peer_tools = await client.list_tools()

                # Register all tools from the connected server with the namespace
                for tool in peer_tools:
                    prefixed_name = f"{namespace}.{tool.name}"
                    self.namespace_mapping[prefixed_name] = (namespace, tool.name)
                self.connected_servers[namespace] = server_url

                registered = sorted(k for k in self.namespace_mapping if k.startswith(f"{namespace}."))
                return {
                    "success": True,
                    "message": f"Connected to {server_url} as '{namespace}'",
                    "status": "connected",
                    "namespace": namespace,
                    "server_url": server_url,
                    "tools_registered": registered,
                }

            except Exception as e:
                logger.error("Failed to connect to server %s: %s", server_url, str(e))
                return {"success": False, "error": f"Failed to connect to server: {e!s}"}

        @self.base_server.tool(
            name="disconnect_server",
            description="Disconnect from a connected MCP server",
            annotations={"readOnlyHint": False, "idempotentHint": False},
            output_schema={
                "type": "object",
                "required": ["success"],
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "error": {"type": "string"},
                    "status": {"type": "string"},
                    "namespace": {"type": "string"},
                    "tools_removed": {"type": "array"},
                },
            },
        )
        async def disconnect_server(
            namespace: Annotated[str, Field(description="Namespace to disconnect.", min_length=1)],
        ) -> dict[str, Any]:
            """Disconnect from a connected MCP server.

            ## Return Format
            {"success": true, "message": "Disconnected ...", "tools_removed": [...]}

            ## Examples
            await disconnect_server(namespace="ring2")
            """
            if namespace not in self.connected_servers:
                return {"success": False, "error": f"No server connected with namespace '{namespace}'"}

            # Remove all tools from this namespace
            tools_to_remove = sorted(name for name in self.namespace_mapping if name.startswith(f"{namespace}."))
            for tool_name in tools_to_remove:
                self.namespace_mapping.pop(tool_name, None)

            # Note: call_namespaced_tool remains available for other namespaces
            self.connected_servers.pop(namespace, None)

            return {
                "success": True,
                "message": f"Disconnected '{namespace}'",
                "status": "disconnected",
                "namespace": namespace,
                "tools_removed": tools_to_remove,
            }

        @app.tool(
            name="call_namespaced_tool",
            description="Call a tool from a connected MCP server using namespace prefix (e.g., 'namespace.tool_name')",
            annotations={"readOnlyHint": False, "idempotentHint": False},
            output_schema={
                "type": "object",
                "required": ["success"],
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "error": {"type": "string"},
                    "tool": {"type": "string"},
                    "result": {},
                },
            },
        )
        async def proxy_tool_call(
            tool_name: Annotated[
                str, Field(description="Namespaced tool name (e.g., 'ring2.list_devices').", min_length=1)
            ],
            arguments: Annotated[dict[str, Any] | None, Field(description="Arguments for the peer tool.")] = None,
        ) -> dict[str, Any]:
            """Call a tool from a connected MCP server using namespace prefix.

            ## Return Format
            {"success": true, "tool": "...", "result": <peer payload>}

            ## Examples
            await proxy_tool_call(tool_name="ring2.list_devices", arguments={"device_type": "camera"})
            """
            if tool_name not in self.namespace_mapping:
                return {"success": False, "error": f"No such tool: {tool_name}"}

            namespace, actual_tool_name = self.namespace_mapping[tool_name]
            if namespace not in self.connected_servers:
                return {"success": False, "error": f"Server '{namespace}' is not connected"}

            try:
                async with self._client_for(namespace) as client:
                    result = await client.call_tool(actual_tool_name, arguments or {})
                data = result.data
                if data is not None and not isinstance(data, dict):
                    data = getattr(data, "__dict__", None) or getattr(data, "model_dump", lambda: data)()
                    if callable(data):
                        data = data()
                if data is None and result.content:
                    data = getattr(result.content[0], "text", None)
                return {
                    "success": not getattr(result, "is_error", False),
                    "message": f"Called {tool_name}",
                    "tool": tool_name,
                    "result": data,
                }
            except Exception as e:
                logger.error("Error calling tool %s on server %s: %s", actual_tool_name, namespace, str(e))
                return {"success": False, "error": f"Failed to call tool {tool_name}: {e!s}"}

    async def close(self) -> None:
        """Close all connections to remote servers."""
        for namespace, client in list(self.connected_servers.items()):
            try:
                await client.close()
                logger.info("Disconnected from server: %s", namespace)
            except Exception as e:
                logger.error("Error disconnecting from server %s: %s", namespace, str(e))

        self.connected_servers.clear()
        self.namespace_mapping.clear()


def create_composed_app(ring_client=None) -> FastMCP:
    """Create a composed FastMCP application with Ring MCP and composition support.

    Uses FastMCP 3.4 patterns with multiline decorators and proper
    stdio communication support for Claude Desktop integration.

    Args:
        ring_client: Optional initialized Ring client instance

    Returns:
        Configured FastMCP application with composition support
    """
    # Create the base FastMCP application with FastMCP 3.4 patterns
    app = FastMCP(
        name="Ring MCP with Composition",
        version="1.0.4",
    )

    # Add the Ring MCP tools
    from .server import register_ring_tools

    if ring_client:
        register_ring_tools(app, ring_client)
    else:
        # Initialize a default Ring client if none provided
        from ring_mcp.core.ring_client_modern import RingClient

        default_client = RingClient()
        register_ring_tools(app, default_client)

    # Add composition capabilities (per-call peer clients hold no connections,
    # so there is no shutdown lifecycle to wire - close() just clears state).
    _composition = MCPServerComposition(app)
    assert _composition is not None

    return app
