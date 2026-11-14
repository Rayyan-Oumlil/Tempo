import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
Q = chr(34)
M = [
    ("window starts too late", "news_split.py", "return (datetime.combine(previous_trading_day(day), CLOSE, tzinfo=ET)", "return (datetime.combine(day, CLOSE, tzinfo=ET)"),
    ("window lower edge exclusive", "news_split.py", "return [h for h in items if lo <= h[0] <= hi]", "return [h for h in items if lo < h[0] <= hi]"),
    ("window upper edge exclusive", "news_split.py", "return [h for h in items if lo <= h[0] <= hi]", "return [h for h in items if lo <= h[0] < hi]"),
    ("earnings item ignored", "news_split.py", "if " + Q + "2.02" + Q + " in f.items and lo <= f.accepted <= hi", "if lo <= f.accepted <= hi"),
    ("earnings window unbounded", "news_split.py", "and lo <= f.accepted <= hi and f.cik in tickers", "and f.cik in tickers"),
    ("earnings not first", "news_split.py", "    if has_earnings:\n        return " + Q + "earnings" + Q, "    if False:\n        return " + Q + "earnings" + Q),
    ("drift direction flipped", "news_split.py", "return DRIFT, direction", "return DRIFT, -direction"),
    ("fade direction not flipped", "news_split.py", "return FADE, -direction", "return FADE, direction"),
    ("residual sign ignored", "news_split.py", "if residual * direction >= RESIDUAL:", "if abs(residual) >= RESIDUAL:"),
    ("residual bar exclusive", "news_split.py", "if residual * direction >= RESIDUAL:", "if residual * direction > RESIDUAL:"),
    ("missing sector bars treated as sympathy", "news_split.py", "if residual is None:\n        return " + Q + "no_sector_bars" + Q, "if residual is None:\n        return " + Q + "sympathy" + Q),
    ("news before the day counts only strictly", "news_split.py", "if n_headlines > 0:", "if n_headlines > 1:"),
    ("residual is stock minus nothing", "news_split.py", "else s - e", "else s"),
    ("vix on the day itself", "news_split.py", "if date.fromisoformat(d) < day:", "if date.fromisoformat(d) <= day:"),
    ("failed share bar off", "news_split.py", "return movers > 0 and failed / movers > MAX_FAILED_SHARE", "return movers > 0 and failed / movers >= MAX_FAILED_SHARE"),
    ("resignal window ignored", "news_split.py", "        if h[" + Q + "symbol" + Q + "] in recent:\n            continue", "        if False:\n            continue"),
    ("fade features missing", "news_split.py", "if source == FADE:", "if False:"),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(SRC / "evidence", WORK / "evidence", ignore=shutil.ignore_patterns("*.json"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_news_split.py", WORK / "tests" / "test_news_split.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_news_split.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
