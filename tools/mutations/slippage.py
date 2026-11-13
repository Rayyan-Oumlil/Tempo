import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ('late entries not separated', 'slippage.py', '"late": delay > LATE_AFTER_MIN,', '"late": False,'),
    ('late threshold inverted', 'slippage.py', '"late": delay > LATE_AFTER_MIN,', '"late": delay < LATE_AFTER_MIN,'),
    ('delay from the wrong reference', 'slippage.py', 'REFERENCE = time(9, 40)', 'REFERENCE = time(15, 0)'),
    ('long sign flipped', 'slippage.py', 'entry_gap = _bps(d * (t["fill_price"] - score["entry_px"]) / score["entry_px"])', 'entry_gap = _bps(-d * (t["fill_price"] - score["entry_px"]) / score["entry_px"])'),
    ('exit sign same as entry', 'slippage.py', 'exit_gap = None if not exit_fill else _bps(-d *', 'exit_gap = None if not exit_fill else _bps(d *'),
    ('alarm uses the signed gap', 'slippage.py', 'sum(abs(x) for x in last) / len(last)', 'sum(last) / len(last)'),
    ('alarm needs no minimum', 'slippage.py', 'if len(entry) >= ALARM_MIN_TRADES else None', 'if True else None'),
    ('alarm limit ignored', 'slippage.py', 's["last_abs"] > ALARM_BPS]', 's["last_abs"] > 0]'),
    ('unknown source treated as pending', 'slippage.py', '            unknown.add(source)\n            continue', '            continue'),
    ('wrong horizon score accepted', 'slippage.py', 'score = by_signal.get((sid, HORIZONS[source]))', 'score = next((v for (k, h), v in by_signal.items() if k == sid), None)'),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_slippage.py", WORK / "tests" / "test_slippage.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_slippage.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
