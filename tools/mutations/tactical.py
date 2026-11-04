import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
MUTATIONS = [
    ("trend uses >= instead of >", "tempo/tactical.py", "if c[t] > sum(c[i] for i in window) / months", "if c[t] >= sum(c[i] for i in window) / months"),
    ("window excludes the current month end", "tempo/tactical.py", "window = [i for i in month_ends if i <= t][-months:]", "window = [i for i in month_ends if i < t][-months:]"),
    ("window of 9 instead of 10 months", "tempo/tactical.py", "if len(window) < months:", "if len(window) < months - 1:"),
    ("fixed weights ignore cash share", "tempo/tactical.py", "return lambda t: dict(weights)", "return lambda t: {k: v * 2 for k, v in weights.items()}"),
    ("fills the same day (look-ahead)", "tempo/portfolio.py", "        if target is not None:  # decided at yesterday's close, filled at today's\n            total = cash + sum(shares[s] * px[s] for s in symbols)\n            want = {s: int(total * target", "        if target is not None or t in signal_days:  # MUTATED\n            target = target or weight_fn(t) or {}\n            total = cash + sum(shares[s] * px[s] for s in symbols)\n            want = {s: int(total * target"),
    ("weights over 100% accepted", "tempo/portfolio.py", "or sum(weights.values()) > 1.0 + 1e-9:", "or False:"),
    ("negative weights accepted", "tempo/portfolio.py", "if any(w < 0 for w in weights.values())", "if False"),
    ("sells skip their costs", "tempo/portfolio.py", "                    cost = order_cost(qty, px[s], \"SELL\", costs)\n                    cash += qty * px[s] - cost\n                    shares[s] = want[s]\n                    trades.append(PTrade(t, s, \"SELL\", qty, px[s], cost))\n            for s in symbols:\n                qty = want[s] - shares[s]\n                while", "                    cost = 0.0\n                    cash += qty * px[s] - cost\n                    shares[s] = want[s]\n                    trades.append(PTrade(t, s, \"SELL\", qty, px[s], cost))\n            for s in symbols:\n                qty = want[s] - shares[s]\n                while"),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_tactical.py", WORK / "tests" / "test_tactical.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_tactical.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]

fresh(); print("unmutated copy:", run())
for name, rel, old, new in MUTATIONS:
    fresh()
    f = WORK / rel
    text = f.read_text(encoding="utf-8")
    if old not in text:
        print(f"{name:<42} -> PATTERN NOT FOUND"); continue
    i = text.rfind(old) if name.startswith('sells') else text.find(old)
    f.write_text(text[:i] + new + text[i + len(old):], encoding="utf-8")
    print(f"{name:<42} -> {run()}")
