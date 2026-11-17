import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
TARGET, TEST = "history_reversal.py", "test_history_reversal.py"
M = [
    ("week ends by ISO year only", "isocalendar()[:2] != date.fromisoformat(b).isocalendar()[:2]", "isocalendar()[:1] != date.fromisoformat(b).isocalendar()[:1]"),
    ("entry on the signal day", "entry = calendar[spy.pos[t] + 1]", "entry = calendar[spy.pos[t]]"),
    ("entries after the cap", "if entry < first or entry > last:", "if entry < first:"),
    ("entries before the start", "if entry < first or entry > last:", "if entry > last:"),
    ("liquidity filter off", 'if liquid(bars, t)["status"] != "ok":', "if False:"),
    ("longs and shorts swapped", "[(s, 1) for s in longs] + [(s, -1) for s in shorts]", "[(s, -1) for s in longs] + [(s, 1) for s in shorts]"),
    ("thin weeks traded", "if not longs:", "if False:"),
    ("unscored counted as scored", 'counts["unscored"] += 1', 'counts["scored"] += 1'),
    ("horizon of one", "gross = trade_excess(universe[symbol], spy, entry, direction, horizon)", "gross = trade_excess(universe[symbol], spy, entry, direction, 1)"),
]


def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / TEST, WORK / "tests" / TEST)


def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", f"tests/{TEST}", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]


fresh()
print("unmutated copy:", run())
for name, old, new in M:
    fresh()
    f = WORK / "tempo" / TARGET
    text = f.read_text(encoding="utf-8").replace("\r\n", "\n")
    if old not in text:
        print(f"{name:<44} -> PATTERN NOT FOUND")
        continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<44} -> {run()}")
