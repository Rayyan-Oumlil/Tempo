import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
TESTS = ["tests/test_analyst_actions.py", "tests/test_weekly_reversal.py"]
AA, WR, DB = "analyst_actions.py", "weekly_reversal.py", "daybars.py"
MUTATIONS = {
    "upgrade traded as a short": (AA, '1 if m.group("action") == "upgraded" else -1', '-1 if m.group("action") == "upgraded" else 1'),
    "window ignores the previous close": (AA, "start < _as_utc(stamp) <= end", "_as_utc(stamp) <= end"),
    "window ignores today's close": (AA, "start < _as_utc(stamp) <= end", "start < _as_utc(stamp)"),
    "conflicting actions still trade": (AA, "return found.pop() if len(found) == 1 else None", "return found.pop() if found else None"),
    "news timeout read as empty": (AA, "        return None\n\n\ndef record_signals", "        return []\n\n\ndef record_signals"),
    "liquidity needs only one of price or volume": (DB, "close >= MIN_PRICE and adv >= MIN_ADV", "close >= MIN_PRICE or adv >= MIN_ADV"),
    "week end test ignores later trading days": (WR, "        if is_trading_day(d):\n            return False", "        if is_trading_day(d):\n            return True"),
    "SPY return added instead of subtracted": (WR, "- (spy.close[j] / spy.close[k] - 1)", "+ (spy.close[j] / spy.close[k] - 1)"),
    "longs taken from the winners": (WR, "longs = ranked[:n]", "longs = ranked[-n:]"),
    "thin universe still trades": (WR, "if len(moves) < MIN_SCORABLE:", "if len(moves) < 0:"),
}

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(SRC / "evidence", WORK / "evidence")
    (WORK / "tests").mkdir()
    for t in TESTS:
        shutil.copy(SRC / t, WORK / t)

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", *TESTS, "-q", "-p", "no:cacheprovider"],
                       cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]

fresh(); print("unmutated copy:", run())
for name, (file, old, new) in MUTATIONS.items():
    fresh()
    f = WORK / "tempo" / file
    text = f.read_text(encoding="utf-8")
    if old not in text:
        print(f"{name:<42} -> NOT FOUND"); continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<42} -> {run()}")
