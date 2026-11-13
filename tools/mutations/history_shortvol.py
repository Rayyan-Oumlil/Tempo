import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ('entry at the signal day open', 'history_shortvol.py', 'spy.dates[j + 1], spy.dates[j + horizon]', 'spy.dates[j], spy.dates[j + horizon]'),
    ('exit one session early', 'history_shortvol.py', 'spy.dates[j + 1], spy.dates[j + horizon]', 'spy.dates[j + 1], spy.dates[j + horizon - 1]'),
    ('benchmark not subtracted', 'history_shortvol.py', 'return direction * ((s1 / s0 - 1) - (b1 / b0 - 1))', 'return direction * (s1 / s0 - 1)'),
    ('direction ignored', 'history_shortvol.py', 'return direction * ((s1 / s0 - 1) - (b1 / b0 - 1))', 'return ((s1 / s0 - 1) - (b1 / b0 - 1))'),
    ('exit missing bar guessed', 'history_shortvol.py', 'if entry not in stock.dates or exit_ not in stock.dates:', 'if entry not in stock.dates:'),
    ('gap bridged in the baseline', 'history_shortvol.py', '            window.clear()', '            pass'),
    ('baseline not required', 'history_shortvol.py', 'and len(window) == BASELINE_DAYS:', 'and len(window) >= 0:'),
    ('no-bar names kept', 'history_shortvol.py', '            if b is None:\n                counts["no_bars"] += 1\n                continue', '            if b is None:\n                counts["no_bars"] += 1'),
    ('liquidity filter skipped', 'history_shortvol.py', 'if liquid(b.daybars(), day)["status"] != "ok":', 'if False:'),
    ('legs swapped', 'history_shortvol.py', '(("long", 1), ("short", -1))', '(("long", -1), ("short", 1))'),
    ('both-legs rule becomes any', 'history_shortvol.py', 'both = all(v[4].startswith("KILL") for v in verdicts.values())', 'both = any(v[4].startswith("KILL") for v in verdicts.values())'),
    ('membership uses the future', 'history_shortvol.py', 'current = [t for d, t in history if d <= day]', 'current = [t for d, t in history]'),
    ('unsorted membership accepted', 'history_shortvol.py', 'if [d for d, _ in out] != sorted(d for d, _ in out):', 'if False:'),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_history_shortvol.py", WORK / "tests" / "test_history_shortvol.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_history_shortvol.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]

fresh(); print("unmutated copy:", run())
for name, fname, old, new in M:
    fresh()
    f = WORK / "tempo" / fname
    text = f.read_text(encoding="utf-8")
    if old not in text:
        print(f"{name:<42} -> PATTERN NOT FOUND"); continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<42} -> {run()}")
