"""
Skill surface tests: domain skill files exist with valid frontmatter, the
SkillsDirectoryProvider exposes skill:// resources on the served app, and the
REST /api/skills scanner sees the same skill.
"""

from pathlib import Path

from ring_mcp.http_server import _scan_skill_dir
from ring_mcp.server import create_app

REPO = Path(__file__).resolve().parent.parent


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{path} missing YAML frontmatter"
    head = text[3 : text.find("\n---", 3)]
    out: dict[str, str] = {}
    for line in head.splitlines():
        key, sep, val = line.partition(":")
        if sep:
            out[key.strip()] = val.strip().strip("\"'")
    return out


def test_domain_skill_exists_with_frontmatter():
    skill = REPO / "skills" / "ring-mcp" / "SKILL.md"
    assert skill.is_file()
    fm = _frontmatter(skill)
    assert fm.get("name") == "ring-mcp"
    assert len(fm.get("description", "")) > 20
    body = skill.read_text(encoding="utf-8")
    assert len(body.splitlines()) >= 50, "domain skill is a runt"
    for tool in ("list_devices", "get_security_system_status", "arm_security_system"):
        assert tool in body, f"skill missing real tool {tool}"


def test_opencode_and_agents_mirrors():
    for path in (
        REPO / ".opencode" / "skills" / "ring-mcp" / "SKILL.md",
        REPO / ".agents" / "skills" / "ring-mcp" / "SKILL.md",
    ):
        assert path.is_file(), f"missing skill mirror {path}"


async def test_skill_resources_served():
    app = create_app()
    uris = sorted(str(r.uri) for r in await app.list_resources())
    assert "skill://ring-mcp/SKILL.md" in uris


def test_api_skills_scanner():
    found = _scan_skill_dir(REPO / "skills")
    names = [s["name"] for s in found]
    assert "ring-mcp" in names
