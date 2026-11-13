import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ("entry on the signal date (look-ahead)", "next((i for i, d in enumerate(bars.dates) if d > signal[\"date_et\"]), None)", "next((i for i, d in enumerate(bars.dates) if d >= signal[\"date_et\"]), None)"),
    ("duplicate check removed", "if any(r.get(\"signal_id\") == signal_id for r in self.journal.records() if r[\"kind\"] == \"signal\"):", "if False:"),
    ("date taken in UTC", "datetime.fromtimestamp(self.journal.now(), NEW_YORK).date().isoformat()", "datetime.utcfromtimestamp(self.journal.now()).date().isoformat()"),
    ("direction not applied to returns", "ret = d * (bars.close[exit_] / bars.open[entry] - 1)", "ret = (bars.close[exit_] / bars.open[entry] - 1)"),
    ("benchmark direction not applied", "bench_ret = d * (bench.close", "bench_ret = (bench.close"),
    ("net excess ignores the cost", "\"net_excess\": ret - bench_ret - cost, \"round_trip_cost\": cost}", "\"net_excess\": ret - bench_ret, \"round_trip_cost\": cost}"),
    ("per-source cost ignored", "cost = signal[\"features\"].get(\"round_trip_cost\", ROUND_TRIP_COST)", "cost = ROUND_TRIP_COST"),
    ("scores not idempotent", "fresh = [s for s in scores if (s[\"signal_id\"], s[\"horizon\"], s.get(\"method\")) not in done]", "fresh = list(scores)"),
    ("verdict allowed too early", "if n < MIN_SCORED else", "if n < 1 else"),
    ("backfill not excluded", "(include_backfill or not r[\"backfill\"])", "True"),
    ("exit on the entry day", "exit_ = entry + horizon - 1", "exit_ = entry + horizon"),
    ("any direction accepted", "if direction not in (1, -1):", "if False:"),
    ("hit rate counts zero as a win", "sum(1 for v in values if v > 0) / n", "sum(1 for v in values if v >= 0) / n"),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_ledger.py", WORK / "tests" / "test_ledger.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_ledger.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]

fresh(); print("unmutated copy:", run())
for name, old, new in M:
    fresh()
    f = WORK / "tempo" / "ledger.py"
    text = f.read_text(encoding="utf-8")
    if old not in text:
        print(f"{name:<42} -> PATTERN NOT FOUND"); continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<42} -> {run()}")
