import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
TESTS = ("test_insider_opp.py", "test_insider_history.py")
M = [
    ("insider_opp.py", "stale purchases not skipped", " or not actionable(b):", ":"),
    ("insider_opp.py", "lag limit removed", "<= MAX_TRADE_LAG_DAYS", "<= 99999"),
    ("insider_opp.py", "lag limit a year and a day", "MAX_TRADE_LAG_DAYS = 365", "MAX_TRADE_LAG_DAYS = 366"),
    ("insider_opp.py", "mistyped future dates kept", "return 0 <= (date.fromisoformat", "return -99999 <= (date.fromisoformat"),
    ("insider_opp.py", "trade date ignored for the lag", '    trade = date.fromisoformat((b.get("trade_date") or b["filing_date"])[:10])\n    return 0', '    trade = date.fromisoformat(b["filing_date"][:10])\n    return 0'),
    ("insider_history.py", "default build back to three years", "range(YEARS_BACK + 1, 0, -1)", "range(YEARS_BACK, 0, -1)"),
    ("insider_history.py", "default build counts forward", "today.year - k for k in", "today.year + k for k in"),
]


def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    for t in TESTS:
        shutil.copy(SRC / "tests" / t, WORK / "tests" / t)


def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", *[f"tests/{t}" for t in TESTS], "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]


fresh()
print("unmutated copy:", run())
for target, name, old, new in M:
    fresh()
    f = WORK / "tempo" / target
    text = f.read_text(encoding="utf-8").replace("\r\n", "\n")
    if old not in text:
        print(f"{name:<44} -> PATTERN NOT FOUND")
        continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<44} -> {run()}")
