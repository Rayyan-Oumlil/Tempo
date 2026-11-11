"""Gateway watchdog for the VPS: checks the IBKR API every few minutes, restarts Gateway when it stays down, alerts you.

Usage (cron, every 10 minutes, all week):  python -m tempo.watchdog

Rules (pure logic in `step`): a failed check is only noise; the 2nd in a row alerts, the 3rd restarts the Gateway container
once, the 6th says the restart did not help. The nightly Gateway restart (IBC, 23:59 ET) is not counted as an outage.
It only reads (read-only API session) and never places an order.
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "logs" / "watchdog_state.json"
HEARTBEAT_FILE = ROOT / "logs" / "heartbeat.json"
COMPOSE_FILE = ROOT / "deploy" / "docker-compose.yml"
ET = ZoneInfo("America/New_York")
HOST, PORT, CLIENT_ID, CHECK_TIMEOUT = "127.0.0.1", 4002, 98, 20
ALERT_AFTER, RESTART_AFTER, STILL_DOWN_AFTER = 2, 3, 6
MAINTENANCE_START, MAINTENANCE_END = time(23, 50), time(0, 25)


@dataclass(frozen=True)
class State:
    failures: int = 0
    restarted: bool = False


def in_maintenance(now: datetime) -> bool:
    t = now.astimezone(ET).time()
    return t >= MAINTENANCE_START or t < MAINTENANCE_END


def step(state: State, ok: bool, now: datetime) -> tuple[State, list[str]]:
    if ok:
        return State(), (["recovered"] if state.failures >= ALERT_AFTER else [])
    if in_maintenance(now):
        return state, []
    failures, restarted, actions = state.failures + 1, state.restarted, []
    if failures == ALERT_AFTER:
        actions.append("alert_down")
    if failures == RESTART_AFTER and not restarted:
        actions.append("restart")
        restarted = True
    if failures == STILL_DOWN_AFTER:
        actions.append("alert_still_down")
    return State(failures, restarted), actions


def load_state(path: Path = STATE_FILE) -> State:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return State(int(raw["failures"]), bool(raw["restarted"]))
    except (OSError, ValueError, KeyError, TypeError):
        return State()


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def check_api() -> tuple[bool, str]:  # pragma: no cover - needs a live Gateway
    from ib_async import IB
    ib = IB()
    try:
        ib.connect(HOST, PORT, clientId=CLIENT_ID, timeout=CHECK_TIMEOUT, readonly=True)
        accounts = ib.managedAccounts()
        server_time = ib.reqCurrentTime()
        return (bool(accounts and server_time), f"accounts={len(accounts)}")
    except Exception as err:  # noqa: BLE001 - any failure means "not healthy"; the reason goes to the log
        return False, f"{type(err).__name__}: {err}"[:200]
    finally:
        if ib.isConnected():
            ib.disconnect()


def restart_gateway() -> int:  # pragma: no cover - needs docker
    return subprocess.run(["sudo", "-n", "docker", "compose", "-f", str(COMPOSE_FILE), "restart"], capture_output=True,
                          timeout=180, check=False).returncode


def run_once(*, now: datetime, check: Callable[[], tuple[bool, str]], restart: Callable[[], int], notify: Callable[[str, str], None],
             state_path: Path = STATE_FILE, heartbeat_path: Path = HEARTBEAT_FILE, log: Callable[[str], None] = print) -> State:
    ok, detail = check()
    state, actions = step(load_state(state_path), ok, now)
    stamp = now.astimezone(ET).strftime("%Y-%m-%d %H:%M ET")
    log(f"{stamp} api {'ok' if ok else 'DOWN'} ({detail}) failures={state.failures} actions={actions}")
    for action in actions:
        if action == "alert_down":
            notify("Tempo watchdog: Gateway DOWN", f"{stamp}: the IBKR API has not answered {ALERT_AFTER} checks in a row ({detail}). "
                   "It will be restarted automatically if it stays down.")
        elif action == "restart":
            code = restart()
            notify("Tempo watchdog: restarting Gateway", f"{stamp}: still down after {RESTART_AFTER} checks; docker compose restart returned {code}.")
        elif action == "alert_still_down":
            notify("Tempo watchdog: Gateway STILL DOWN", f"{stamp}: the restart did not bring the API back ({detail}). Needs a human: "
                   "check docker logs, and IBKR Mobile for a 2FA prompt.")
        elif action == "recovered":
            notify("Tempo watchdog: Gateway recovered", f"{stamp}: the IBKR API answers again.")
    _write(state_path, asdict(state))
    _write(heartbeat_path, {"ts": now.timestamp(), "ok": ok, "detail": detail})
    return state


def main() -> int:  # pragma: no cover - entry point
    from tempo.notify import notify
    run_once(now=datetime.now(ET), check=check_api, restart=restart_gateway, notify=lambda t, b: notify(t, b))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
