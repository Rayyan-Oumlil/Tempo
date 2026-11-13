import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ('intraday release ignored', 'earnings_guard.py', 'return reaction_day(accepted) or accepted.astimezone(ET).date()', 'return reaction_day(accepted)'),
    ('window start exclusive', 'earnings_guard.py', 'lo <= effective_day(a) <= hi', 'lo < effective_day(a) <= hi'),
    ('window end exclusive', 'earnings_guard.py', 'lo <= effective_day(a) <= hi', 'lo <= effective_day(a) < hi'),
    ('earnings sources included', 'earnings_guard.py', 'if s["source"] in EXCLUDED_SOURCES:', 'if False:'),
    ('unknown symbol read as no earnings', 'earnings_guard.py', 'filings_by_symbol[s["symbol"]]', 'filings_by_symbol.get(s["symbol"], [])'),
    ('kept arm is the earnings arm', 'earnings_guard.py', 'kept = [r["net_excess"] for r in rs if not r["earnings"]]', 'kept = [r["net_excess"] for r in rs if r["earnings"]]'),
    ('verdict inverted', 'earnings_guard.py', 'return "variance falls: keep the guard" if s["sd_kept"] < s["sd"]', 'return "variance falls: keep the guard" if s["sd_kept"] > s["sd"]'),
    ('small arms accepted', 'earnings_guard.py', 'if s["n_earnings"] < MIN_PER_ARM or s["n"] - s["n_earnings"] < MIN_PER_ARM:', 'if False:'),
    ('no pooled row', 'earnings_guard.py', '        groups[f"ALL h{r[\'horizon\']}"].append(r)\n', ''),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_earnings_guard.py", WORK / "tests" / "test_earnings_guard.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_earnings_guard.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
