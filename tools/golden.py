"""Golden-output (characterization) check for the strategy report runners.

Usage (from the repo root):
  python tools/golden.py snapshot   freeze a copy of data/*.csv into goldens/data, dropping bars dated on or after FREEZE
  python tools/golden.py record     run every runner on the snapshot and save its exact output in goldens/*.txt
  python tools/golden.py check      run them again and compare with the saved outputs; exit 1 on any difference

Why: the runners produced every verdict in docs/research/log.md. Refactoring them is only safe if the numbers they print
stay byte-identical. The snapshot removes the "today's unfinished bar" dependence, so the output does not change from
one day to the next. goldens/data is market data and stays out of git; the saved outputs (goldens/*.txt) are text.
"""
from __future__ import annotations

import csv
import difflib
import importlib
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GOLDEN_DIR = ROOT / "goldens"
SNAPSHOT_DIR = GOLDEN_DIR / "data"
FREEZE = "2026-11-03"  # bars dated on or after this are dropped from the snapshot (the day the goldens were taken)
RUNNERS = {
    "rotation": ("tempo.rotation_report", "report", {}),
    "pairs": ("tempo.pairs_report", "report", {}),
    "overnight": ("tempo.overnight_report", "report", {}),
    "meanrev": ("tempo.meanrev_report", "report", {}),
    "tactical": ("tempo.tactical_report", "report", {}),
    "forward": ("tempo.forward", "report", {"today": date(2026, 11, 4)}),
    "evidence_spy": ("tempo.evidence", "report", {"args": ("SPY", 200)}),
}


def snapshot() -> int:
    source = ROOT / "data"
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    for f in sorted(source.glob("*.csv")):
        with f.open(newline="", encoding="utf-8") as src:
            rows = list(csv.reader(src))
        kept = [rows[0]] + [r for r in rows[1:] if r[0] < FREEZE]
        with (SNAPSHOT_DIR / f.name).open("w", newline="", encoding="utf-8") as dst:
            csv.writer(dst).writerows(kept)
    print(f"snapshot: {len(list(SNAPSHOT_DIR.glob('*.csv')))} files in {SNAPSHOT_DIR}")
    return 0


def run_all() -> dict[str, str]:
    import tempo.data
    tempo.data.DATA_DIR = SNAPSHOT_DIR
    out = {}
    for name, (module, func, opts) in RUNNERS.items():
        fn = getattr(importlib.import_module(module), func)
        result = fn(*opts["args"]) if "args" in opts else fn(**opts)
        out[name] = result[0] if isinstance(result, tuple) else result
    return out


def main(mode: str) -> int:
    if mode == "snapshot":
        return snapshot()
    if not SNAPSHOT_DIR.exists():
        print("no snapshot yet: run `python tools/golden.py snapshot` first", file=sys.stderr)
        return 2
    outputs = run_all()
    GOLDEN_DIR.mkdir(exist_ok=True)
    if mode == "record":
        for name, text in outputs.items():
            (GOLDEN_DIR / f"{name}.txt").write_text(text + "\n", encoding="utf-8", newline="\n")
        print(f"recorded {len(outputs)} outputs in {GOLDEN_DIR}")
        return 0
    if mode == "check":
        bad = 0
        for name, text in outputs.items():
            saved = (GOLDEN_DIR / f"{name}.txt").read_text(encoding="utf-8")
            if saved != text + "\n":
                bad += 1
                print(f"DIFFERENT: {name}")
                print("".join(list(difflib.unified_diff(saved.splitlines(True), (text + "\n").splitlines(True), "saved", "now"))[:40]))
            else:
                print(f"identical: {name}")
        return 1 if bad else 0
    print("usage: python tools/golden.py snapshot|record|check", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
