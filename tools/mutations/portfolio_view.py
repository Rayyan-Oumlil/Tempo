import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ('trade not spread over its days', 'portfolio_view.py', 's["net_excess"] / len(days)', 's["net_excess"]'),
    ('overlap summed instead of averaged', 'portfolio_view.py', '{d: fmean(v) for d, v in sorted(by_day.items())}', '{d: sum(v) for d, v in sorted(by_day.items())}'),
    ('weights not inverse volatility', 'portfolio_view.py', 'inv = {s: 1 / pstdev(list(r.values()))', 'inv = {s: pstdev(list(r.values()))'),
    ('weights not normalised', 'portfolio_view.py', 'weights = {s: v / total for s, v in inv.items()}', 'weights = {s: v for s, v in inv.items()}'),
    ('short sources blended', 'portfolio_view.py', 'if len(r) >= MIN_DAYS and pstdev', 'if len(r) >= 1 and pstdev'),
    ('overlap minimum ignored', 'portfolio_view.py', 'if len(common) < MIN_OVERLAP:', 'if len(common) < 1:'),
    ('effective bets assumes zero for a missing pair', 'portfolio_view.py', '        if r is None:\n            return None\n', '        r = 0.0 if r is None else r\n'),
    ('effective bets uses signed correlation', 'portfolio_view.py', 'total += 2 * r * r', 'total += 2 * r'),
    ('empty span accepted', 'portfolio_view.py', 'if not days:', 'if False:'),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_portfolio_view.py", WORK / "tests" / "test_portfolio_view.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_portfolio_view.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
