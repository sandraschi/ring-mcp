set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]
import 'scripts/just/fleet.just'

# ── Dashboard ─────────────────────────────────────────────────────────────────

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# ── Dependencies (uv) ───────────────────────────────────────────────────────

# Install / sync Python deps from lockfile
sync:
    Set-Location '{{justfile_directory()}}'
    uv sync

# Refresh uv.lock after pyproject changes
lock:
    Set-Location '{{justfile_directory()}}'
    uv lock

# ── Quality ───────────────────────────────────────────────────────────────────

# Ruff lint (Python) + Biome CI (web_sota)
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome ci .

# Ruff fix/format + Biome write (web_sota)
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .
    Set-Location '{{justfile_directory()}}\web_sota'
    npx @biomejs/biome check --write .

# ── Test ─────────────────────────────────────────────────────────────────────

# Full pytest suite (mock default; real tests skip without RING_* env)
test:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/ -q

# Fast mock/unit slice (no Ring account required)
test-unit:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/test_unit_mock.py tests/test_basic.py tests/test_ring_mcp.py tests/test_utilities.py -q

# Real Ring integration only (requires RING_USERNAME + RING_PASSWORD in env)
test-real:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/test_integration_real.py -v --tb=short

# Same as test-real but prompts for user/password if RING_* not set (child process only)
test-real-prompt:
    Set-Location '{{justfile_directory()}}'
    uv run python scripts/run_test_real_prompt.py

# Ring devices: print online + battery (RingClient; use RING_* env or interactive prompt)
devices:
    Set-Location '{{justfile_directory()}}'
    uv run python scripts/ring_device_status.py

# Same as devices but never prompt (CI / scripts; requires RING_USERNAME + RING_PASSWORD)
devices-env:
    Set-Location '{{justfile_directory()}}'
    uv run python scripts/ring_device_status.py --no-prompt

# ── Dev (repo-specific) ───────────────────────────────────────────────────────

# Fleet UI: Vite 10728 + REST API 10729 (see web_sota\start.ps1)
dev:
    Set-Location '{{justfile_directory()}}\web_sota'
    .\start.ps1

# REST API only (fleet default port 10729 via PORT env)
dev-http:
    Set-Location '{{justfile_directory()}}'
    uv run ring-mcp-http

# ── Serve ────────────────────────────────────────────────────────────────────

# Run MCP server stdio
serve:
    Set-Location '{{justfile_directory()}}'
    uv run python -m ring_mcp

# Run webapp (Vite dev)
serve-web:
    Set-Location '{{justfile_directory()}}\web_sota'
    bun run dev

# Build webapp
build-web:
    Set-Location '{{justfile_directory()}}\web_sota'
    bun run build

# ── Test ────────────────────────────────────────────────────────────────────

# Run pytest
test:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/ -q

# ── Docker ────────────────────────────────────────────────────────────────────

docker-up:
    Set-Location '{{justfile_directory()}}'
    docker compose up -d --build

docker-down:
    Set-Location '{{justfile_directory()}}'
    docker compose down

# ── Hardening ─────────────────────────────────────────────────────────────────

# Bandit on ring_mcp package + tests (tools via uv; no extra pyproject dep)
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv tool run --from bandit bandit -r ring_mcp tests

# Known-vuln scan on lockfile-resolved requirements (pip-audit via uv)
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv export --frozen --format requirements.txt -o .audit-reqs.txt
    uv tool run pip-audit -r .audit-reqs.txt
    if (Test-Path .audit-reqs.txt) { Remove-Item .audit-reqs.txt -Force }
