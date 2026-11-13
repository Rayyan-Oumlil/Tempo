import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ("cap removed", "sizing.py", "notional = min(wanted, cap)", "notional = wanted"),
    ("floor ignored (shrunk into the trap)", "sizing.py", "if shares == 0 or value < equity * rules.floor_pct / 100:", "if shares == 0:"),
    ("risk not divided by volatility", "sizing.py", "wanted = equity * rules.target_risk_pct / 100 / sigma20", "wanted = equity * rules.target_risk_pct / 100 / 0.02"),
    ("percent treated as fraction", "sizing.py", "wanted = equity * rules.target_risk_pct / 100 / sigma20", "wanted = equity * rules.target_risk_pct / sigma20"),
    ("bad volatility accepted", "sizing.py", "for v in (equity, price, sigma20))", "for v in (equity, price))"),
    ("shares rounded up", "sizing.py", "shares = int(notional // price)", "shares = math.ceil(notional / price)"),
    ("capped status never reported", "sizing.py", '"capped" if wanted >= cap else "sized"', '"sized"'),
    ("rules check dropped", "sizing.py", "if not (0 < self.target_risk_pct and", "if False and not (0 < self.target_risk_pct and"),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_sizing.py", WORK / "tests" / "test_sizing.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_sizing.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
