"""Print Ring device status (online, battery) to the terminal. Uses RingClient (no HTTP server)."""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import sys
from typing import Any

from ring_mcp.core.ring_client_modern import RingClient


def _creds_from_env_or_prompt(*, no_prompt: bool) -> tuple[str, str]:
    username = (os.getenv("RING_USERNAME") or "").strip()
    password = os.getenv("RING_PASSWORD") or ""

    if username and password:
        return username, password

    if no_prompt:
        print(
            "Missing RING_USERNAME or RING_PASSWORD. Set them or run without --no-prompt.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Ring device status (credentials are not written to disk).")
    if not username:
        username = input("Ring email / username: ").strip()
    if not password:
        password = getpass.getpass("Ring password: ")

    if not username or not password:
        print("Username and password are required.", file=sys.stderr)
        sys.exit(1)

    return username, password


def _battery_str(d: dict[str, Any]) -> str:
    b = d.get("battery_life")
    if b is None:
        return "wired"
    return f"{int(b)}%"


def _is_doorcam(t: str) -> bool:
    x = (t or "").lower()
    return "doorbell" in x or "camera" in x or "stickup" in x or "flood" in x


def _print_table(devices: list[dict[str, Any]]) -> None:
    doorcam = [d for d in devices if _is_doorcam(str(d.get("type", "")))]
    other = [d for d in devices if d not in doorcam]
    ordered = doorcam + other

    if not ordered:
        print("No devices returned.")
        return

    w_name = max(len(str(d.get("name", ""))) for d in ordered)
    w_name = min(max(w_name, 12), 48)
    w_type = max(len(str(d.get("type", ""))) for d in ordered)
    w_type = min(max(w_type, 8), 20)

    header = f"{'TYPE':<{w_type}}  {'NAME':<{w_name}}  {'ONLINE':<8}  BATTERY"
    print(header)
    print("-" * len(header))
    for d in ordered:
        t = str(d.get("type", "?"))
        name = str(d.get("name", "?"))[:w_name]
        online = "yes" if d.get("online") else "no"
        bat = _battery_str(d)
        print(f"{t:<{w_type}}  {name:<{w_name}}  {online:<8}  {bat}")

    print()
    print(f"Total: {len(ordered)} device(s) ({len(doorcam)} doorbell/camera-like).")


async def _run(username: str, password: str) -> None:
    client = RingClient(username=username, password=password)
    try:
        await client.connect()
        devices = await client.get_devices(force_refresh=True)
    finally:
        await client.close()

    _print_table(devices)


def main() -> int:
    p = argparse.ArgumentParser(description="Print Ring device online/battery status.")
    p.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not prompt for credentials; require RING_USERNAME and RING_PASSWORD.",
    )
    args = p.parse_args()

    username, password = _creds_from_env_or_prompt(no_prompt=args.no_prompt)

    try:
        asyncio.run(_run(username, password))
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
