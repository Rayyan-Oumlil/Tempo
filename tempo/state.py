"""Trading mode: `normal` or `reduce_only` (no new entries; exits are always allowed).

There is no separate "halt": exits are never refused, so a halt would behave exactly like reduce_only.
A missing file means normal. An unreadable or unknown file means reduce_only (fail closed on new exposure).

Usage: python -m tempo.state                  show the mode
       python -m tempo.state normal "why"     set it
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parents[1] / "state.json"
MODES = ("normal", "reduce_only")


def get_mode(path: Path = STATE_FILE) -> str:
    path = Path(path)
    if not path.exists():
        return "normal"
    try:
        mode = json.loads(path.read_text(encoding="utf-8")).get("mode")
    except (OSError, ValueError, AttributeError):
        return "reduce_only"
    return mode if mode in MODES else "reduce_only"


def set_mode(mode: str, reason: str, path: Path = STATE_FILE) -> None:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
    record = {"mode": mode, "reason": reason, "since": datetime.now(timezone.utc).isoformat()}
    Path(path).write_text(json.dumps(record), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        set_mode(sys.argv[1], " ".join(sys.argv[2:]) or "manual")
    print(f"mode: {get_mode()}")
