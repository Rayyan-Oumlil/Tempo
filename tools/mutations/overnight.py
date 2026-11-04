import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
MUTATIONS = {
    "sell at the close instead of the open": ("cash += shares * opens[t] - cost", "cash += shares * closes[t] - cost"),
    "buy on the last day too": ("if t < len(closes) - 1:  # buy", "if True:  # buy"),
    "free sells": ('cost = order_cost(shares, opens[t], "SELL", costs)', "cost = 0.0"),
    "bisection direction flipped": ("lo, hi = (mid, hi) if net(mid) > 0 else (lo, mid)", "lo, hi = (lo, mid) if net(mid) > 0 else (mid, hi)"),
}

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_overnight.py", WORK / "tests" / "test_overnight.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_overnight.py", "-q", "-p", "no:cacheprovider"],
                       cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]

fresh(); print("unmutated copy:", run())
for name, (old, new) in MUTATIONS.items():
    fresh()
    f = WORK / "tempo" / "overnight.py"
    text = f.read_text(encoding="utf-8")
    assert old in text, name
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<42} -> {run()}")
