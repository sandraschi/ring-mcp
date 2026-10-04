"""
HTTP contract tests: fleet endpoints against TestClient (no credentials needed).

Covers shapes and status codes with and without Ring/LLM services. POST
/api/shutdown is deliberately NEVER called (it exits the process).
"""

import pytest
from fastapi.testclient import TestClient

from ring_mcp import http_server
from ring_mcp.http_server import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_capabilities_shape(client):
    r = client.get("/api/capabilities")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "ring-mcp"
    assert body["health_path"] == "/api/v1/health"
    assert body["features"]["llm_proxy"] is True


def test_system_info_shape(client):
    r = client.get("/api/v1/system/info")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["tool_count"] >= 29
    assert body["uptime_seconds"] >= 0


def test_diagnostics_shape(client):
    r = client.get("/api/v1/diagnostics")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["backend"]["status"] == "ok"
    assert data["tools"]["total"] >= 29
    assert data["system"]["uptime_seconds"] >= 0


def test_skills_lists_domain_skill(client):
    r = client.get("/api/skills")
    assert r.status_code == 200
    names = [s["name"] for s in r.json()["skills"]]
    assert "ring-mcp" in names


def test_llm_registry_shapes(client):
    discover = client.get("/api/v1/llm/discover").json()
    assert set(discover) >= {"detected", "base_url", "models", "message"}
    providers = client.get("/api/v1/llm/providers").json()
    assert providers["default_provider"] == "local"
    assert providers["providers"][0]["id"] == "local"
    # Key material must never leave the server (only detected flags + base URL).
    dumped = client.get("/api/v1/llm/providers").text
    assert "RING_LLM_API_KEY" not in dumped
    assert "Bearer " not in dumped
    onboarding = client.get("/api/v1/llm/onboarding").json()
    assert len(onboarding["facts"]) >= 1
    assert len(onboarding["recommended_path"]) >= 1


def test_llm_models_and_chat_degrade_without_llm(client):
    # Passes whether or not a local LLM runs: asserts shape/status contract only.
    models = client.get("/api/v1/llm/models")
    assert models.status_code == 200
    assert set(models.json()) >= {"success", "models", "default_model", "base_url"}
    chat = client.post("/api/v1/llm/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert chat.status_code in (200, 503)
    if chat.status_code == 503:
        assert "detail" in chat.json()


def test_llm_chat_stream_framing(client, monkeypatch):
    async def fake_stream(messages, model=None):
        assert messages and messages[0]["role"] == "system"
        yield "Hello "
        yield "world"

    monkeypatch.setattr(http_server, "chat_completion_stream", fake_stream)
    r = client.post("/api/v1/llm/chat/stream", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert 'data: {"token": "Hello "}' in r.text
    assert "data: [DONE]" in r.text


def test_llm_chat_stream_error_frame(client, monkeypatch):
    async def failing_stream(messages, model=None):
        raise ValueError("no LLM here")
        yield  # pragma: no cover - makes this an async generator

    monkeypatch.setattr(http_server, "chat_completion_stream", failing_stream)
    r = client.post("/api/v1/llm/chat/stream", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 200
    assert '"error": "no LLM here"' in r.text
    assert "data: [DONE]" in r.text


def test_auth_gated_endpoints_without_creds(client):
    # No RING_* in this env: 401 with the auth error shape (200 if creds exist).
    for path in ("/api/v1/events/recent", "/api/v1/status"):
        r = client.get(path)
        assert r.status_code in (200, 401)
        if r.status_code == 401:
            assert r.json()["code"] == "AUTHENTICATION_ERROR"
