import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ("hac drops the autocovariance terms", "sequential.py", "s += 2 * (1 - k / (lag + 1))", "s += 0 * (1 - k / (lag + 1))"),
    ("hac lag ignores the horizon", "sequential.py", "lag = max(horizon - 1, 0)", "lag = 0"),
    ("hac weights are flat, not Bartlett", "sequential.py", "2 * (1 - k / (lag + 1))", "2"),
    ("msprt ignores the overlap variance", "sequential.py", "sigma2 = k * hac_variance_of_mean(pre, lag)", "sigma2 = variance(pre)"),
    ("p-value uses the last ratio, not the running max", "sequential.py", "best = max(best, math.exp(min(log_l, 700)))", "best = math.exp(min(log_l, 700))"),
    ("interval uses 1.0 sigma", "sequential.py", "base.mean - 1.96 * se", "base.mean - 1.0 * se"),
    ("cohorts not averaged", "sequential.py", "[(d, mean(v), len(v))", "[(d, v[0], len(v))"),
    ("no deflation for the number of tries", "sequential.py", "sr0 = math.sqrt(variance(sr_all))", "sr0 = 0 * math.sqrt(variance(sr_all))"),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_sequential.py", WORK / "tests" / "test_sequential.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_sequential.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
