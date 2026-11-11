import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
TESTS = ["tests/test_short_volume.py", "tests/test_ledger.py", "tests/test_snapshots.py"]
SV, SN = "short_volume.py", "snapshots.py"
MUTATIONS = {
    "longs taken from the highest z": (SV, "longs = sorted(z, key=lambda s: (z[s], s))[:per_side]", "longs = sorted(z, key=lambda s: (-z[s], s))[:per_side]"),
    "shorts taken from the lowest z": (SV, "shorts = sorted(z, key=lambda s: (-z[s], s))[:per_side]", "shorts = sorted(z, key=lambda s: (z[s], s))[:per_side]"),
    "thin universe still trades": (SV, "if len(z) < MIN_SCORABLE:", "if len(z) < 0:"),
    "deviation floor removed": (SV, "max(statistics.pstdev(past), SD_FLOOR)", "(statistics.pstdev(past) or 1e-9)"),
    "short baseline accepted": (SV, "len(past) < MIN_BASELINE", "len(past) < 1"),
    "thin volume accepted": (SV, "today[s][1] < MIN_TOTAL_VOLUME", "today[s][1] < 0"),
    "ratio inverted": (SV, "return short / total if total > 0 else None", "return total / short if short > 0 else None"),
    "truncated finra file accepted": (SN, "if len(out) < FINRA_MIN_ROWS:", "if len(out) < 0:"),
    "unexpected finra header accepted": (SN, "if not lines or lines[0].strip() != FINRA_HEADER:", "if not lines:"),
    "malformed download kept": (SN, "parse_short_volume(raw.decode(", "(lambda *a: None)(raw.decode("),
    "ftd period walks forward": (SN, "            m -= 1\n            if m == 0:\n                y, m = y - 1, 12\n    return out", "            m += 1\n            if m == 0:\n                y, m = y - 1, 12\n    return out"),
}

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(SRC / "evidence", WORK / "evidence")
    (WORK / "tests").mkdir()
    for t in TESTS:
        shutil.copy(SRC / t, WORK / t)

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", *TESTS, "-q", "-p", "no:cacheprovider"],
                       cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]

fresh(); print("unmutated copy:", run())
for name, (file, old, new) in MUTATIONS.items():
    fresh()
    f = WORK / "tempo" / file
    text = f.read_text(encoding="utf-8")
    if old not in text:
        print(f"{name:<42} -> NOT FOUND"); continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<42} -> {run()}")
