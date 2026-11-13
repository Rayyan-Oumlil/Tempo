import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ('no clipping', 'beta_compare.py', 'return [min(max(r, lo), hi) for r in returns]', 'return list(returns)'),
    ('clip at wrong end', 'beta_compare.py', 'lo, hi = s[int(clip * (len(s) - 1))], s[int(round((1 - clip) * (len(s) - 1)))]', 'lo, hi = s[0], s[-1]'),
    ('empty series crashes', 'beta_compare.py', 'if not returns:', 'if False:'),
    ('window too long', 'beta_compare.py', 'window = days[-(BETA_DAYS + 1):]', 'window = days'),
    ('future days used', 'beta_compare.py', 'if d < before)\n    window', "if d <= '9999')\n    window"),
    ('spy leg not rescaled', 'beta_compare.py', 'score["bench_ret"] * beta_alt / score["beta"]', 'score["bench_ret"]'),
    ('cost dropped', 'beta_compare.py', '- score["round_trip_cost"]', '- 0'),
    ('zero beta accepted', 'beta_compare.py', 'if score["beta"] == 0:', 'if False:'),
    ('shift sign lost', 'beta_compare.py', 'fmean(r["beta_alt"] - r["beta"] for r in v)', 'fmean(abs(r["beta_alt"] - r["beta"]) for r in v)'),
    ('big shift threshold off', 'beta_compare.py', '> BIG_SHIFT', '> 5'),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_beta_compare.py", WORK / "tests" / "test_beta_compare.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_beta_compare.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
