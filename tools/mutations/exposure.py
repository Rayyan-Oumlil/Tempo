import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ('net cap one-sided', 'exposure.py', 'return abs(net(book)) <= equity', 'return net(book) <= equity'),
    ('net cap boundary exclusive', 'exposure.py', '<= equity * MAX_NET_PCT / 100', '< equity * MAX_NET_PCT / 100'),
    ('beta ignored', 'exposure.py', 'sum(p["notional"] * p["beta"] for p in book)', 'sum(p["notional"] for p in book)'),
    ('hedge side inverted', 'exposure.py', 'Hedge("SELL" if exposure > 0 else "BUY", abs(exposure))', 'Hedge("BUY" if exposure > 0 else "SELL", abs(exposure))'),
    ('no minimum ticket', 'exposure.py', 'if abs(exposure) < equity * MIN_HEDGE_PCT / 100:', 'if abs(exposure) < 0:'),
    ('hedge size not full', 'exposure.py', 'abs(exposure))\n\n\ndef check', 'abs(exposure) / 2)\n\n\ndef check'),
    ('sector share of net not gross', 'exposure.py', 'by[p["sector"]] = by.get(p["sector"], 0.0) + abs(p["notional"])', 'by[p["sector"]] = by.get(p["sector"], 0.0) + p["notional"]'),
    ('sector cap boundary', 'exposure.py', 'if v / total > MAX_SECTOR_SHARE', 'if v / total >= MAX_SECTOR_SHARE'),
    ('missing beta defaulted', 'exposure.py', 'if p.get(key) is None:', 'if False:'),
    ('non-finite accepted', 'exposure.py', 'if not (math.isfinite(p["notional"]) and math.isfinite(p["beta"])):', 'if False:'),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_exposure.py", WORK / "tests" / "test_exposure.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_exposure.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
