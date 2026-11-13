import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ('intraday filings not skipped', 'history_earnings.py', 'if t < large.CLOSE:', 'if False:'),
    ('after-close goes to the same day', 'history_earnings.py', 'later = [d for d in calendar if d > day]', 'later = [d for d in calendar if d >= day]'),
    ('direction sign dropped', 'history_earnings.py', 'return direction * ((s1 / s0 - 1) - (b1 / b0 - 1))', 'return ((s1 / s0 - 1) - (b1 / b0 - 1))'),
    ('benchmark not subtracted', 'history_earnings.py', 'return direction * ((s1 / s0 - 1) - (b1 / b0 - 1))', 'return direction * (s1 / s0 - 1)'),
    ('horizon one session short', 'history_earnings.py', 'end = spy.dates[j + horizon]', 'end = spy.dates[j + horizon - 1]'),
    ('missing end bar guessed', 'history_earnings.py', 'if day not in stock.dates or end not in stock.dates:', 'if day not in stock.dates:'),
    ('kill rule inverted', 'history_earnings.py', '    if mean < cost:', '    if mean > cost:'),
    ('cost of the small band as large', 'history_earnings.py', '"small": small.ROUND_TRIP_COST', '"small": large.ROUND_TRIP_COST'),
    ('no minimum number of days', 'history_earnings.py', 'if len(cohort) < MIN_DAYS:', 'if len(cohort) < 1:'),
    ('ragged columns accepted', 'history_earnings.py', 'if len({len(c) for c in cols}) != 1:', 'if False:'),
    ('item 202 not required', 'history_earnings.py', 'if form == "8-K" and "2.02" in str(items).split(","):', 'if form == "8-K":'),
    ('older files always fetched', 'history_earnings.py', 'if date.fromisoformat(f["filingTo"]) >= first and date.fromisoformat(f["filingFrom"]) <= last:', 'if True:'),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_history_earnings.py", WORK / "tests" / "test_history_earnings.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_history_earnings.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
