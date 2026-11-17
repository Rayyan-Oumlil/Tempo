import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ('dedupe ignores symbol', 'news_archive.py', 'return (self.symbol, self.provider, self.article_id)', 'return (self.provider, self.article_id)'),
    ('dedupe loaded wrong key', 'news_archive.py', 'keys.add((r["symbol"], r["provider"], r["article_id"]))', 'keys.add((r["provider"], r["article_id"], r["symbol"]))'),
    ('naive time not utc', 'news_archive.py', 'dt = t if t.tzinfo else t.replace(tzinfo=timezone.utc)', 'dt = t'),
    ('month from wrong slice', 'news_archive.py', 'f"{time_utc[:7]}.jsonl"', 'f"{time_utc[:4]}.jsonl"'),
    ('retry count off by one', 'news_archive.py', 'if attempt < retries - 1:', 'if attempt < retries:'),
    ('failure returned as empty', 'news_archive.py', '            sleep(backoff * (attempt + 1))\n    return None', '            sleep(backoff * (attempt + 1))\n    return []'),
    ('no backoff growth', 'news_archive.py', 'sleep(backoff * (attempt + 1))', 'sleep(backoff)'),
    ('unavailable not listed', 'news_archive.py', '            unavailable.append(s)\n            continue', '            continue'),
    ('coverage inverted', 'news_archive.py', 'return ok / total', 'return 1 - ok / total'),
    ('empty coverage allowed', 'news_archive.py', 'if total <= 0:', 'if total < 0:'),
    ('roundup bar off', 'news_labels.py', 'len(syms) >= min_symbols', 'len(syms) > min_symbols'),
    ('auto before roundup', 'news_labels.py', 'if t in roundups or _ROUNDUP.search(t):', 'if False:'),
    ('analyst skipped', 'news_labels.py', 'if _ANALYST.search(t):', 'if False:'),
    ('filing skipped', 'news_labels.py', 'if _FILING.search(t):', 'if False:'),
    ('press release skipped', 'news_labels.py', 'if t.lower().startswith("press release:"):', 'if False:'),
    ('metadata kept', 'news_labels.py', 'return _META.sub("", headline).strip()', 'return headline.strip()'),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_news_archive.py", WORK / "tests" / "test_news_archive.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_news_archive.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
