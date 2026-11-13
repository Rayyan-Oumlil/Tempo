import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ("entry on the signal date (look-ahead)", "exec_score.py", "d > signal[\"date_et\"]), None)", "d >= signal[\"date_et\"]), None)"),
    ("beta uses the entry day (look-ahead)", "exec_score.py", "if d < before)", "if d <= before)"),
    ("beta not shrunk toward one", "exec_score.py", "return SHRINK * raw + (1 - SHRINK)", "return raw"),
    ("hedge not scaled by beta", "exec_score.py", "bench_ret = beta * d * (", "bench_ret = d * ("),
    ("hedge ignores direction", "exec_score.py", "bench_ret = beta * d * (", "bench_ret = beta * ("),
    ("stock direction not applied", "exec_score.py", "ret = d * (exit_px / entry_px - 1)", "ret = (exit_px / entry_px - 1)"),
    ("net excess ignores the cost", "exec_score.py", "\"net_excess\": ret - bench_ret - cost,", "\"net_excess\": ret - bench_ret,"),
    ("per-source cost ignored", "exec_score.py", "cost = signal[\"features\"].get(\"round_trip_cost\", ROUND_TRIP_COST)", "cost = ROUND_TRIP_COST"),
    ("exit at the close, not 15 minutes before", "exec_score.py", "EXIT_MINUTES_BEFORE_CLOSE = 15", "EXIT_MINUTES_BEFORE_CLOSE = 0"),
    ("entry at the open, not 09:40", "exec_score.py", "ENTRY_HHMM = \"09:40\"", "ENTRY_HHMM = \"09:30\""),
    ("a missing bar is guessed", "exec_score.py", "if any(p is None for p in px):", "if False:"),
    ("a short history still gets a beta", "exec_score.py", "MIN_BETA_DAYS = 40", "MIN_BETA_DAYS = 1"),
    ("exit one day late", "exec_score.py", "daily.dates[entry + horizon - 1]", "daily.dates[entry + horizon]"),
    ("score not stamped with the method", "exec_score.py", "\"method\": METHOD, ", ""),
    ("legacy rows counted as current", "ledger.py", "and (method is None or r.get(\"method\") == method)]", "and True]"),
    ("legacy rows mark v2 as done", "ledger.py", "if r[\"kind\"] == \"score\" and r.get(\"method\") == METHOD}", "if r[\"kind\"] == \"score\"}"),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_exec_score.py", WORK / "tests" / "test_exec_score.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_exec_score.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
