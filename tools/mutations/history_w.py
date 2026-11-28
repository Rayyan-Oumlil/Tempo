import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
MUTATIONS = {
    "vix filter inverted": ("(vix.reindex(index) < vix3m.reindex(index))", "(vix.reindex(index) > vix3m.reindex(index))"),
    "latest month not skipped": ("month_end.shift(1) / month_end.shift(12)", "month_end / month_end.shift(12)"),
    "worst sectors picked": ("ascending=False", "ascending=True"),
    "gold lookback changed": ("GOLD_LOOKBACK = 63", "GOLD_LOOKBACK = 62"),
    "one benchmark is enough": ("all(excess >= b for b in bench_excess)", "any(excess >= b for b in bench_excess)"),
    "deflated sharpe ignored": ("dsr >= 0.95,", "True,"),
    "drawdown ignored": ("dd > bench_dd,", "True,"),
    "losing sub-period accepted": ("all(c > 0 for c in subs)", "True"),
    "cost stress ignored": ("stress_excess >= 0.30,", "True,"),
    "own trials dropped": ("for sr, per in Z_LOGGED] + own_daily", "for sr, per in Z_LOGGED]"),
}

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_history_w.py", WORK / "tests" / "test_history_w.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_history_w.py", "-q", "-p", "no:cacheprovider"],
                       cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]

fresh(); print("unmutated copy:", run())
for name, (old, new) in MUTATIONS.items():
    fresh()
    f = WORK / "tempo" / "history_w.py"
    text = f.read_text(encoding="utf-8")
    if old not in text:
        print(f"{name:<42} -> NOT FOUND"); continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<42} -> {run()}")
