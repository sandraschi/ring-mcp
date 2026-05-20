"""Server-side proxy to local OpenAI-compatible LLM (default Ollama :11434)."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Long generations (local models can be slow)
_CHAT_TIMEOUT = httpx.Timeout(180.0, connect=8.0)

_LOCAL_CLIENT_KW: dict[str, Any] = {"trust_env": False}

_DEFAULT_LLM = "http://127.0.0.1:11434"


def llm_base_url() -> str:
    raw = os.getenv("RING_LLM_BASE_URL", _DEFAULT_LLM).rstrip("/")
    if "://localhost" in raw:
        raw = raw.replace("://localhost", "://127.0.0.1", 1)
    return raw


def default_model_env() -> str:
    return os.getenv("RING_LLM_MODEL", "").strip()


def llm_api_key() -> str | None:
    k = os.getenv("RING_LLM_API_KEY", "").strip()
    return k or None


def _auth_headers() -> dict[str, str]:
    key = llm_api_key()
    if key:
        return {"Authorization": f"Bearer {key}"}
    return {}


async def list_model_ids() -> tuple[list[str], str | None]:
    """
    Return (model_ids, error). Prefers GET /v1/models; falls back to Ollama /api/tags.
    """
    base = llm_base_url()
    headers = _auth_headers()
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(15.0),
            **_LOCAL_CLIENT_KW,
        ) as client:
            r = await client.get(f"{base}/v1/models", headers=headers)
            if r.status_code == 200:
                data = r.json()
                out: list[str] = []
                for m in data.get("data", []) or []:
                    mid = m.get("id") or m.get("name")
                    if isinstance(mid, str) and mid.strip():
                        out.append(mid.strip())
                if out:
                    return out, None
            r2 = await client.get(f"{base}/api/tags", headers=headers)
            if r2.status_code == 200:
                data2 = r2.json()
                out2: list[str] = []
                for m in data2.get("models", []) or []:
                    name = m.get("name")
                    if isinstance(name, str) and name.strip():
                        out2.append(name.strip())
                if out2:
                    return out2, None
            return (
                [],
                f"LLM list failed: /v1/models HTTP {r.status_code}, /api/tags HTTP {r2.status_code}",
            )
    except Exception as e:
        logger.warning("LLM model list error: %s", e)
        return [], f"Could not reach local LLM at {base}: {e!s}"


async def chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
) -> str:
    """
    POST /v1/chat/completions (Ollama 0.2+ and LM Studio). ``model`` required unless
    ``RING_LLM_MODEL`` is set and non-empty.
    """
    base = llm_base_url()
    use_model = (model or "").strip() or default_model_env()
    if not use_model:
        ids, err = await list_model_ids()
        if not ids:
            raise ValueError(err or "No local models found; set RING_LLM_MODEL or pull a model")
        use_model = ids[0]
    body: dict[str, Any] = {
        "model": use_model,
        "messages": messages,
        "stream": False,
    }
    headers = {"Content-Type": "application/json", **_auth_headers()}
    async with httpx.AsyncClient(timeout=_CHAT_TIMEOUT, **_LOCAL_CLIENT_KW) as client:
        r = await client.post(f"{base}/v1/chat/completions", json=body, headers=headers)
        if r.status_code >= 400:
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            raise ValueError(f"LLM HTTP {r.status_code}: {detail!s}")
        data = r.json()
    choices = data.get("choices") or []
    if not choices:
        raise ValueError(f"Unexpected LLM response (no choices): {data!s}")
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if not isinstance(content, str):
        raise ValueError("LLM returned no message content")
    return content


async def probe_startup_log(append_log_fn: Callable[..., Any]) -> None:
    """If RING_MCP_LLM_GLOM is enabled, log whether the configured base answers."""
    if os.getenv("RING_MCP_LLM_GLOM", "1").strip().lower() in ("0", "false", "no", "off"):
        return
    base = llm_base_url()
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(2.0),
            **_LOCAL_CLIENT_KW,
        ) as c:
            r = await c.get(f"{base}/v1/models")
            if r.status_code == 200:
                append_log_fn("INFO", f"LLM probe: OpenAI-compatible API up at {base}")
                return
            r2 = await c.get(f"{base}/api/tags")
            if r2.status_code == 200:
                append_log_fn("INFO", f"LLM probe: Ollama /api/tags up at {base}")
                return
        append_log_fn(
            "WARNING",
            f"LLM probe: no response from {base} — start Ollama (default :11434)",
        )
    except Exception as e:
        append_log_fn("WARNING", f"LLM probe: {base} unreachable ({e!s})")
