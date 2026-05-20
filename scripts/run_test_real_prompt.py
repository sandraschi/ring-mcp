"""Run tests/test_integration_real.py with Ring credentials from env or one-time prompts."""

from __future__ import annotations

import getpass
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET = REPO_ROOT / "tests" / "test_integration_real.py"


def main() -> int:
    username = (os.getenv("RING_USERNAME") or "").strip()
    password = os.getenv("RING_PASSWORD") or ""

    if not username:
        print("Ring integration tests (credentials are not saved to disk).")
        username = input("Ring email / username: ").strip()
    else:
        print("Using RING_USERNAME from environment.")

    if not password:
        password = getpass.getpass("Ring password: ")
    else:
        print("Using RING_PASSWORD from environment.")

    if not username or not password:
        print("Username and password are required.", file=sys.stderr)
        return 1

    env = os.environ.copy()
    env["RING_USERNAME"] = username
    env["RING_PASSWORD"] = password
    env["RING_MCP_TEST_MODE"] = "real"

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(TARGET),
        "-v",
        "--tb=short",
        *sys.argv[1:],
    ]
    return subprocess.run(cmd, cwd=REPO_ROOT, env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
