"""Login trouble in the IB Gateway container log (IBC writes it there), for the daily report.

Why: on 2026-11-13 the nightly re-login got "Unrecognized Username or Password" at 00:17 ET and the Gateway sat on that dialog all day.
Nothing reached the owner. The watchdog now catches the dead session; this names the cause.
"""
from __future__ import annotations

import re
import subprocess

CONTAINER = "tempo-ib-gateway-1"
# IBC log fragments that mean the login did not go through (or needs a human)
PATTERNS = ("Unrecognized Username or Password", "Second Factor Authentication", "Existing session detected", "Login failed")
_STAMP = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")


def login_problems(log_text: str) -> list[str]:
    """One line per kind of problem: what, how many times, first and last time (the container clock, ET on the VPS)."""
    found: dict[str, list[str]] = {}
    for line in log_text.splitlines():
        for pattern in PATTERNS:
            if pattern in line:
                m = _STAMP.match(line)
                found.setdefault(pattern, []).append(m.group(1) if m else "?")
    return [f"Gateway login: '{p}' x{len(t)} (first {t[0]}, last {t[-1]})" for p, t in found.items()]


def read_log(hours: int = 24) -> str:  # pragma: no cover - needs docker
    """Raises on failure: a log that cannot be read must show up in the report, not look like a clean day."""
    done = subprocess.run(["sudo", "-n", "docker", "logs", "--since", f"{hours}h", CONTAINER], capture_output=True, text=True,
                          timeout=60, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"docker logs returned {done.returncode}: {done.stderr.strip()[:150]}")
    return done.stdout + done.stderr           # docker replays the container's stderr on stderr


def report() -> list[str]:  # pragma: no cover - needs docker
    try:
        return login_problems(read_log())
    except Exception as exc:  # noqa: BLE001 - surfaced in the email as a problem
        return [f"the Gateway log could not be read: {exc!r}"]
