"""Evaluate measured results against the pre-registered criteria in evidence/gate.json.

The criteria were written before any result existed and must not be edited to fit a result (change them only
with a new dated entry in docs/research/log.md saying why). A missing metric fails: no data is not a pass.

Usage: python -m tempo.gate metrics.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tempo.health import Check

GATE_FILE = Path(__file__).resolve().parents[1] / "evidence" / "gate.json"

# criterion -> (section, metric name, comparison)
RULES = {
    "min_round_trips": ("paper", "round_trips", "ge"),
    "min_trading_days": ("paper", "trading_days", "ge"),
    "min_net_pnl_usd": ("paper", "net_pnl_usd", "ge"),
    "max_process_error_share": ("paper", "process_error_share", "le"),
    "min_years": ("backtest", "years", "ge"),
    "min_shuffle_beat_pct": ("backtest", "shuffle_beat_pct", "ge"),
    "max_variants_tried": ("backtest", "variants_tried", "le"),
}


def evaluate(metrics: dict, gate: dict) -> list[Check]:
    checks = []
    for name, (section, key, op) in RULES.items():
        if name not in gate.get(section, {}):
            continue
        limit, value = gate[section][name], metrics.get(key)
        if value is None:
            checks.append(Check(name, False, f"{key} not measured (required {'>=' if op == 'ge' else '<='} {limit})"))
            continue
        ok = value >= limit if op == "ge" else value <= limit
        checks.append(Check(name, ok, f"{key} = {value:g} (required {'>=' if op == 'ge' else '<='} {limit})"))
    done = metrics.get("checklist", {})
    for item in gate.get("checklist", []):
        checks.append(Check(item, done.get(item) is True, "done" if done.get(item) is True else "not done"))
    return checks


def main(metrics_path: str) -> int:
    gate = json.loads(GATE_FILE.read_text(encoding="utf-8"))
    metrics = json.loads(Path(metrics_path).read_text(encoding="utf-8"))
    checks = evaluate(metrics, gate)
    for c in checks:
        print(f"[{'PASS' if c.ok else 'FAIL'}] {c.name:<28} {c.detail}")
    return 0 if all(c.ok for c in checks) else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m tempo.gate metrics.json", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
