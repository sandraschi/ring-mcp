"""
Composition tests: peer connect/proxy/disconnect against a fake MCP transport.

The composition module talks to peers through fastmcp.Client (URL transport).
Here Client is replaced with an in-memory fake so routing, mapping, and error
paths are proven without network. Ring tools use the modern-spec mock client
from test_tool_wiring.
"""

import json
from unittest.mock import patch

import pytest
from fastmcp import Client

from ring_mcp.composition import create_composed_app
from tests.test_tool_wiring import _call as _call_ring
from tests.test_tool_wiring import make_client, patch_all_clients


class _FakeContent:
    def __init__(self, text):
        self.text = text


class _FakeResult:
    def __init__(self, data):
        self.data = data
        self.content = [_FakeContent(json.dumps(data))]
        self.is_error = False


class _FakeTool:
    def __init__(self, name):
        self.name = name


class FakeClient:
    """Stand-in for fastmcp.Client(URL transport). Records calls."""

    instances = []

    def __init__(self, transport, auth=None):
        self.transport = transport
        self.auth = auth
        self.calls = []
        FakeClient.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def list_tools(self):
        return [_FakeTool("ping"), _FakeTool("echo")]

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        return _FakeResult({"echo": args, "tool": name})


@pytest.fixture
def composed():
    """Composed app with fake peer transport + mocked Ring client."""
    FakeClient.instances.clear()
    mock_client = make_client()
    ring_patches = patch_all_clients(mock_client)
    for p in ring_patches:
        p.start()
    comp_patch = patch("ring_mcp.composition.Client", FakeClient)
    comp_patch.start()
    yield create_composed_app()
    comp_patch.stop()
    for p in reversed(ring_patches):
        p.stop()


async def _ccall(app, name, args=None):
    async with Client(app) as client:
        result = await client.call_tool(name, args or {})
    data = result.data
    if isinstance(data, dict):
        return data
    dd = getattr(data, "__dict__", None)
    if isinstance(dd, dict) and dd:
        return dict(dd)
    return json.loads(result.content[0].text)


async def test_composed_app_builds():
    app = create_composed_app()
    names = sorted(t.name for t in await app.list_tools())
    assert "list_connected_servers" in names
    assert "connect_server" in names
    assert "disconnect_server" in names
    assert "call_namespaced_tool" in names
    assert "list_devices" in names  # single-surface delegation


async def test_composition_connect_proxy_disconnect(composed):
    empty = await _ccall(composed, "list_connected_servers")
    assert empty["success"] is True
    assert empty["servers"] == []

    connected = await _ccall(
        composed, "connect_server", {"namespace": "peer1", "server_url": "http://127.0.0.1:11999/mcp"}
    )
    assert connected["success"] is True
    assert connected["tools_registered"] == ["peer1.echo", "peer1.ping"]

    listed = await _ccall(composed, "list_connected_servers")
    assert len(listed["servers"]) == 1
    assert listed["servers"][0]["namespace"] == "peer1"

    dup = await _ccall(composed, "connect_server", {"namespace": "peer1", "server_url": "http://127.0.0.1:11999/mcp"})
    assert dup["success"] is False

    unknown = await _ccall(composed, "call_namespaced_tool", {"tool_name": "peer1.nope"})
    assert unknown["success"] is False

    proxied = await _ccall(
        composed,
        "call_namespaced_tool",
        {"tool_name": "peer1.echo", "arguments": {"text": "hi"}},
    )
    assert proxied["success"] is True
    assert proxied["result"] == {"echo": {"text": "hi"}, "tool": "echo"}

    # The peer transport itself still serves Ring tools through the same surface.
    ring = await _call_ring("list_devices")
    assert ring["success"] is True

    gone = await _ccall(composed, "disconnect_server", {"namespace": "peer1"})
    assert gone["success"] is True
    assert gone["tools_removed"] == ["peer1.echo", "peer1.ping"]

    after = await _ccall(composed, "call_namespaced_tool", {"tool_name": "peer1.echo"})
    assert after["success"] is False

    missing = await _ccall(composed, "disconnect_server", {"namespace": "peer1"})
    assert missing["success"] is False
