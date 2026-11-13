"""One email every evening: "all good" or the list of what is not. Silence from this email is itself the alarm.

Usage: python -m tempo.daily_report        (cron, 18:45 ET every day)

Checks (pure function `build`, fed with plain data so it is testable): Gateway heartbeat age, today's scheduled jobs,
evening job finished and pushed (trading days), newest backup age, disk space, and the freshness of every data
collector listed in COLLECTORS. Never trades, never writes anything but the email.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
ET = ZoneInfo("America/New_York")
HEARTBEAT_MAX_AGE_MIN = 30
BACKUP_MAX_AGE_H = 30
DISK_MIN_FREE_SHARE = 0.10
# (folder under data/snapshots, trading days only?, max age in days)
COLLECTORS: tuple[tuple[str, bool, int], ...] = (("finra_short_volume", True, 4), ("fred", False, 4), ("options", True, 4), ("vol_series", True, 4))


@dataclass(frozen=True)
class Facts:
    now: datetime
    trading_day: bool
    heartbeat_age_min: float | None
    heartbeat_ok: bool
    sched_lines_today: tuple[str, ...]
    backup_age_h: float | None
    disk_free_share: float
    collector_age_days: dict[str, float | None]
    ledger_counts: dict[str, int]
    slippage_text: str = ""
    slippage_alarms: tuple[str, ...] = ()


def build(f: Facts) -> tuple[str, str]:
    problems: list[str] = []
    if f.heartbeat_age_min is None or f.heartbeat_age_min > HEARTBEAT_MAX_AGE_MIN:
        problems.append("Gateway watchdog has not reported for over 30 minutes (or ever): the watchdog or the VPS cron is stuck")
    elif not f.heartbeat_ok:
        problems.append("Gateway API is not answering right now")
    failed = [ln for ln in f.sched_lines_today if "FAILED" in ln or re.search(r"-> rc [1-9]", ln)]
    problems += [f"job problem today: {ln[:160]}" for ln in failed]
    for job in ("evening", "late"):
        if f.trading_day and not any(f"{job}: git -> rc 0" in ln for ln in f.sched_lines_today):
            problems.append(f"the {job} job did not finish and push the ledger today")
    if f.backup_age_h is None or f.backup_age_h > BACKUP_MAX_AGE_H:
        problems.append("no backup newer than 30 hours")
    if f.disk_free_share < DISK_MIN_FREE_SHARE:
        problems.append(f"disk is {1 - f.disk_free_share:.0%} full")
    for name, trading_only, max_age in COLLECTORS:
        age = f.collector_age_days.get(name)
        if trading_only and not f.trading_day:
            continue
        if age is None or age > max_age:
            problems.append(f"collector {name}: newest snapshot is {'missing' if age is None else f'{age:.0f} days old'}")
    problems += [f"paper fills vs ledger: {a}" for a in f.slippage_alarms]
    lines = [f"Tempo daily report, {f.now:%Y-%m-%d %H:%M} ET", ""]
    lines += [f"PROBLEM: {p}" for p in problems] or ["Everything checked is fine."]
    lines += ["", "Ledger signals: " + ", ".join(f"{k} {v}" for k, v in sorted(f.ledger_counts.items()))]
    if f.slippage_text:
        lines += ["", "Paper fills vs ledger prices:", f.slippage_text]
    lines.append(f"Backup age: {'none' if f.backup_age_h is None else f'{f.backup_age_h:.0f} h'}; disk free {f.disk_free_share:.0%}")
    subject = f"Tempo daily: {len(problems)} PROBLEM(S)" if problems else "Tempo daily: all good"
    return subject, "\n".join(lines)


def _age_days(folder: Path, now: datetime) -> float | None:
    files = [p for p in folder.glob("*") if p.is_file()] if folder.exists() else []
    return None if not files else (now.timestamp() - max(p.stat().st_mtime for p in files)) / 86400


def gather(now: datetime, root: Path = ROOT) -> Facts:  # pragma: no cover - reads the live box
    from tempo.backup import latest
    from tempo.hours import is_trading_day
    beat = root / "logs" / "heartbeat.json"
    try:
        hb = json.loads(beat.read_text(encoding="utf-8"))
        age, ok = (now.timestamp() - float(hb["ts"])) / 60, bool(hb["ok"])
    except (OSError, ValueError, KeyError):
        age, ok = None, False
    today = f"{now:%Y-%m-%d}"
    log = root / "logs" / "sched.log"
    lines = tuple(ln for ln in log.read_text(encoding="utf-8", errors="replace").splitlines() if ln.startswith(today)) if log.exists() else ()
    newest = latest(root / "backups")
    usage = shutil.disk_usage(root)
    counts: dict[str, int] = {}
    ledger = root / "ledger" / "ledger.jsonl"
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("kind") == "signal":
                counts[rec["source"]] = counts.get(rec["source"], 0) + 1
    try:
        from tempo.slippage import report
        slip_text, slip_alarms = report()
    except Exception as exc:  # noqa: BLE001 - a broken report must be visible in the email, not silent
        slip_text, slip_alarms = "", (f"the slippage report itself failed: {exc!r}",)
    return Facts(now, is_trading_day(now.date()), age, ok, lines,
                 None if newest is None else (now.timestamp() - newest.stat().st_mtime) / 3600,
                 usage.free / usage.total, {n: _age_days(root / "data" / "snapshots" / n, now) for n, _, _ in COLLECTORS}, counts, slip_text, tuple(slip_alarms))


def main() -> int:  # pragma: no cover - entry point
    from dotenv import load_dotenv

    from tempo.notify import notify
    load_dotenv(ROOT / ".env")
    subject, body = build(gather(datetime.now(ET)))
    print(subject)
    notify(subject, body)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
