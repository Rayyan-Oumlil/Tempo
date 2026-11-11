"""Unattended runs of the daily routine, for Windows Task Scheduler (see tools/sched/register.ps1).

Usage: python -m tempo.sched morning|entries|exits|evening [--final]

Every job is safe to run any number of times and at any time of day: it first checks that it is a trading day and that
something is actually due (entries and exits read the paper journal), and the paper runner itself never double-trades.
That is what makes "run it again in 15 minutes" a valid retry. A failure never passes silently: it is logged, the exit
code is non-zero, and a popup tells you (once per job per day, and always on the --final attempt).

IB Gateway must still be logged in (paper account, Read-Only API unticked). If it is not, the job fails and says so.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from tempo.hours import EASTERN, is_trading_day
from tempo.journal import Journal
from tempo.ledger import Ledger
from tempo.paper_run import PAPER_FILE, due_actions, entries_allowed, exits_allowed, load_state

ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "logs" / "sched.log"
ALERTS_FILE = ROOT / "logs" / "sched_alerts.json"
JOBS = ("morning", "entries", "exits", "evening")
PULL_DAYS = 3          # the morning pull covers this many trading days, so a missed morning heals itself
STEP_TIMEOUT_S = 900


@dataclass(frozen=True)
class Step:
    argv: tuple[str, ...]
    env: tuple[tuple[str, str], ...] = ()


def previous_trading_days(day: date, n: int) -> list[date]:
    """The n trading days before `day`, oldest first."""
    out: list[date] = []
    d = day
    while len(out) < n:
        d -= timedelta(days=1)
        if is_trading_day(d):
            out.append(d)
    return out[::-1]


def steps_for(job: str, today: date) -> list[Step]:
    py = sys.executable
    orders = (("IBKR_READONLY", "0"),)
    if job == "morning":
        return [Step((py, "-m", "tempo.insider", *(d.isoformat() for d in previous_trading_days(today, PULL_DAYS))))]
    if job == "entries":
        return [Step((py, "-m", "tempo.paper_run", "entries"), orders)]
    if job == "exits":
        return [Step((py, "-m", "tempo.paper_run", "exits"), orders)]
    if job == "evening":
        return [Step((py, "-m", "tempo.earnings_reaction")), Step((py, "-m", "tempo.analyst_actions")),
                Step((py, "-m", "tempo.weekly_reversal")), Step((py, "-m", "tempo.ledger_score")), Step((py, "-m", "tempo.ledger"))]
    raise ValueError(f"unknown job {job!r}; expected one of {JOBS}")


def is_due(job: str, now: datetime, ledger: Ledger, paper: Journal) -> bool:
    if job not in JOBS:
        raise ValueError(f"unknown job {job!r}; expected one of {JOBS}")
    today = now.astimezone(EASTERN).date()
    if not is_trading_day(today):
        return False
    if job in ("morning", "evening"):
        return True
    actions = due_actions(ledger.signals(), load_state(paper), today)
    if job == "entries":
        return entries_allowed(now) and bool(actions["enter"])
    return exits_allowed(now) and bool(actions["exit"])


def _run(step: Step) -> tuple[int, str]:
    env = {**os.environ, **dict(step.env)}
    no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)   # Windows only: no console flashing up from a scheduled run
    try:
        done = subprocess.run(step.argv, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=STEP_TIMEOUT_S, creationflags=no_window)
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {STEP_TIMEOUT_S}s: {' '.join(step.argv)}"
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def _notify(title: str, text: str) -> None:
    """Email (if TEMPO_SMTP_* is set in .env) and a popup on Windows. Never raises; an undelivered email is logged."""
    from tempo.notify import notify
    notify(title, text, log=_log)


def _log(line: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).astimezone(EASTERN).strftime("%Y-%m-%d %H:%M:%S ET")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{stamp} {line}\n")


def _tail(text: str, lines: int = 6) -> str:
    return "\n".join(text.strip().splitlines()[-lines:])


def _first_failure_today(path: Path, job: str, today: date) -> bool:
    """True the first time it is asked for a given job and day, then False (remembered in a small json file)."""
    seen = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    key = f"{job}:{today.isoformat()}"
    if key in seen:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: v for k, v in seen.items() if k.endswith(today.isoformat())} | {key: True}), encoding="utf-8")
    return True


def _commit_ledger(run: Callable[[Step], tuple[int, str]], today: date) -> tuple[int, str]:
    rc, out = run(Step(("git", "add", "ledger/ledger.jsonl")))
    if rc:
        return rc, out
    if run(Step(("git", "diff", "--cached", "--quiet")))[0] == 0:
        return 0, "ledger unchanged"
    for argv in (("git", "commit", "-m", f"ledger: scores as of {today.isoformat()} (scheduled run)"), ("git", "push")):
        rc, out = run(Step(argv))
        if rc:
            return rc, out
    return 0, "ledger committed and pushed"


def run_job(job: str, *, now: datetime, final: bool = False, ledger: Ledger | None = None, paper: Journal | None = None,
            run: Callable[[Step], tuple[int, str]] = _run, notify: Callable[[str, str], None] = _notify,
            log: Callable[[str], None] = _log, alerts_path: Path = ALERTS_FILE) -> int:
    today = now.astimezone(EASTERN).date()

    def fail(detail: str) -> int:
        log(f"{job}: FAILED {detail}")
        if _first_failure_today(alerts_path, job, today) or final:
            tail = "LAST attempt today. " if final else "It will retry. "
            notify(f"Tempo {job} FAILED", f"{tail}{_tail(detail)}")
        return 1

    try:
        ledger, paper = ledger or Ledger(), paper or Journal(PAPER_FILE)
        if not is_due(job, now, ledger, paper):
            log(f"{job}: nothing to do")
            return 0
        outputs: list[str] = []
        failures: list[str] = []
        keep_going = job == "evening"   # the evening steps are independent: one failing must not stop scoring or the commit
        for step in steps_for(job, today):
            rc, out = run(step)
            log(f"{job}: {' '.join(step.argv[-3:])} -> rc {rc}\n{_tail(out, 12)}")
            if rc:
                failures.append(f"{' '.join(step.argv[-2:])} exited {rc}\n{_tail(out)}")
                if not keep_going:
                    return fail(failures[0])
            outputs.append(out)
        if job == "evening":
            rc, out = _commit_ledger(run, today)
            log(f"{job}: git -> rc {rc}: {_tail(out, 3)}")
            if rc:
                failures.append(f"git exited {rc}\n{_tail(out)}")
        if failures:
            return fail("\n".join(failures))
        if job in ("entries", "exits"):
            notify(f"Tempo {job} done", _tail(outputs[-1], 3))
        return 0
    except Exception as exc:  # noqa: BLE001 - an unattended job must never die quietly
        return fail(f"{type(exc).__name__}: {exc}")


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in JOBS:
        raise SystemExit(f"usage: python -m tempo.sched {'|'.join(JOBS)} [--final]")
    return run_job(argv[0], now=datetime.now(timezone.utc), final="--final" in argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
