# Development — ring-mcp

## Prereqs

Python 3.12 (via uv), Bun (webapp), PowerShell 7. No other global tools needed;
`just bootstrap` installs the rest.

## Daily flow

```powershell
just bootstrap   # uv sync --extra dev + pre-commit install + bun install
just serve       # MCP stdio server (Claude Desktop path)
just dev         # full stack: API :10729 + UI :10728
just dev-http    # REST API only
just lint        # ruff check . + bun run biome:ci
just fix         # ruff --fix + format + biome --write  (alias: fmt)
just test        # full pytest (mock default; real tests skip without RING_* env)
just test-unit   # fast mock slice
just test-real   # needs RING_USERNAME + RING_PASSWORD (never in CI)
just mcpb-pack   # bundle (needs src-layout migration — currently blocked, see below)
just cua-webapp-test / just cua-nsis-test   # browser / installer smoke walks
```

## Layout

Top-level package `ring_mcp/` (NOT src-layout — see MCPB note). `ring_mcp/server.py`
is the FastMCP factory (`create_app()` registers 29 tools + 2 prompts + 3 resources
+ Prefab cards + SkillsDirectoryProvider). `http_server.py` is the FastAPI REST app.
`tools/*_tools.py` hold domain tools against `core/ring_client_modern.py` (the ONLY
live client; the legacy sync client was deleted). `composition.py` ports peer-proxying
to the FastMCP 3.4 Client API. `run_server.py` is the dual-transport entry.

## Testing

- Mock-first: `tests/test_tool_wiring.py` invokes 28/29 served tools through a real
  FastMCP client against modern-spec mocks (`ring_shutdown` excluded — `os._exit`).
- `tests/test_composition.py` proves peer connect/proxy/disconnect via a fake transport.
- `tests/test_skills.py` guards skill frontmatter + `skill://` serving + `/api/skills` scan.
- Coverage gate: `--cov-fail-under=30` (currently ~43%).
- Real-device: `RING_USERNAME`/`RING_PASSWORD` in env, then `just test-real`. Never commit creds.
- Webapp: `bun run build` (tsc + vite) and `bun run biome:ci` must both exit 0.

## Conventions (fleet)

- Tool docstrings: 1-3 line summary + `## Return Format` + `## Examples`; params in
  `Annotated[..., Field(description=...)]`; `annotations=` on every tool; `output_schema=`
  with `required: ["success"]` (or the honest discriminator: `system_status`, `content`,
  `devices_tested` where no success key exists).
- Returns: `{success, message, ...}`; Prefab cards return `{content, structured_content}`.
- Errors: honest payloads, never fabricated state (armed is `unknown` unless reported).
- Commits: ≤5 files each, conventional messages, pre-commit hooks stay installed.
- `.bak` discipline: timestamped backups before 3+ file mutations; remove before commit;
  `*.bak`, `*.bak.*`, `*.bak-*` are all gitignored.

## Known structural debts (do not reintroduce)

- `server.py` `__main__` block configures logging/metrics but serves nothing
  (`__main__.py` + `run_server.py` are the real entries).
- `mcpb/server/server.py` references a nonexistent `main` (legacy staging leftover).
- `just mcpb-pack` needs the src-layout migration (`pack.ps1` Step 0 requires `src/<pkg>`).
