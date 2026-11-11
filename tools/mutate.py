"""Mutation check: break the code on purpose and make sure the tests notice.

Usage (from the repo root):
  python tools/mutate.py              run every module's mutations
  python tools/mutate.py ledger insider   run only those

Each file in tools/mutations/ copies the project to a temporary folder, applies one deliberate bug at a time
(look-ahead, a dropped cost, a flipped sign, a removed guard...), runs that module's tests, and prints whether the
tests failed (good: the bug was caught) or still passed (a SURVIVOR: the tests cannot see that bug). The project's own
files are never modified.

Exit code 1 if any mutation survived, except the ones listed in EQUIVALENT below: those change nothing a test could
observe (written down with the reason), so a survivor there is expected.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

MUTATIONS = Path(__file__).resolve().parent / "mutations"

# Mutants that cannot be killed by any real input, with the reason.
EQUIVALENT = {
    "DTD check removed": "the XML is sliced from <ownershipDocument> on, so a DOCTYPE never reaches the parser; the check is defence in depth",
}


def run_one(name: str) -> tuple[int, list[str]]:
    result = subprocess.run([sys.executable, str(MUTATIONS / f"{name}.py")], capture_output=True, text=True, timeout=1800)
    survivors = []
    if result.returncode != 0 or "unmutated copy:" not in result.stdout:
        survivors.append(f"MUTATION SCRIPT CRASHED (exit {result.returncode}): {(result.stderr or result.stdout).strip()[-200:]}")
    for line in result.stdout.splitlines():
        label, _, outcome = line.partition(" -> ")
        label = label.strip()
        if not outcome or label == "unmutated copy:":
            if line.startswith("unmutated copy:") and "failed" in line:
                survivors.append(f"BASELINE ALREADY FAILING: {line}")
            continue
        if "failed" not in outcome and "NOT FOUND" not in outcome:
            survivors.append(label)
        elif "NOT FOUND" in outcome:
            survivors.append(f"{label} (pattern no longer matches the code: update the mutation)")
        print(f"  {line}")
    return len(survivors), survivors


def main(names: list[str]) -> int:
    names = names or sorted(p.stem for p in MUTATIONS.glob("*.py"))
    unexpected = 0
    for name in names:
        print(f"== {name}")
        count, survivors = run_one(name)
        for s in survivors:
            if s in EQUIVALENT:
                print(f"  expected survivor: {s} ({EQUIVALENT[s]})")
            else:
                unexpected += 1
                print(f"  SURVIVOR: {s}")
    print(f"\n{'all mutations caught' if not unexpected else str(unexpected) + ' unexpected survivor(s)'}")
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
