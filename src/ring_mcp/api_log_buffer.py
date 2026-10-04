"""In-memory ring buffer of recent log lines for the HTTP API / logger UI."""

from __future__ import annotations

import logging
from collections import deque
from datetime import UTC, datetime
from typing import Any

_MAX = 500
_entries: deque[dict[str, Any]] = deque(maxlen=_MAX)


class _SuppressSuccessfulLogsPollFilter(logging.Filter):
    """Hide successful GET /api/v1/logs from access logs (UI polls every ~2s)."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name != "uvicorn.access":
            return True
        msg = record.getMessage()
        if "/api/v1/logs" in msg and " 200" in msg:
            return False
        return True


def append_log(level: str, message: str, **extra: Any) -> None:
    _entries.append(
        {
            "ts": datetime.now(UTC).isoformat(),
            "level": level.upper(),
            "message": message,
            "extra": extra or {},
        }
    )


def get_logs(limit: int = 200) -> list[dict[str, Any]]:
    lim = max(1, min(limit, _MAX))
    return list(_entries)[-lim:]


class ApiLogHandler(logging.Handler):
    """Forwards standard-library log records to the in-memory buffer."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            append_log(record.levelname, msg, logger=record.name)
        except Exception:
            return


def attach_ring_mcp_loggers() -> None:
    """Idempotent: attach handler to ring_mcp and uvicorn loggers (HTTP server startup)."""
    access = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, _SuppressSuccessfulLogsPollFilter) for f in access.filters):
        access.addFilter(_SuppressSuccessfulLogsPollFilter())

    h = ApiLogHandler()
    h.setLevel(logging.INFO)
    h.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    for name in ("ring_mcp", "uvicorn.error", "uvicorn.access"):
        log = logging.getLogger(name)
        if not any(isinstance(x, ApiLogHandler) for x in log.handlers):
            log.addHandler(h)
