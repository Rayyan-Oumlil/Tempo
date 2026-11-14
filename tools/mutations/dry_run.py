import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ("missing vol20 not skipped", "dry_run.py", 'if r.get("vol20") is None or r.get("price") is None:', "if False:"),
    ("skip reason swapped", "dry_run.py", '"no vol20" if r.get("vol20") is None else "no price"', '"no price"'),
    ("sizing skip dropped", "dry_run.py", "if s.shares == 0:", "if False:"),
    ("direction ignored", "dry_run.py", '"notional": r["direction"] * s.notional', '"notional": s.notional'),
    ("net cap not checked", "dry_run.py", "net_within_cap(book, equity) if book else True", "True"),
    ("hedge dropped", "dry_run.py", "hedge_order(book, equity), net_within_cap", "None, net_within_cap"),
    ("cap warning hidden", "dry_run.py", '"net within cap" if plan.net_ok else "NET EXPOSURE ABOVE CAP"', '"net within cap"'),
    ("no beta defaulted to 1", "dry_run.py", "beta = beta_of(s[" + chr(34) + "symbol" + chr(34) + "])", "beta = beta_of(s[" + chr(34) + "symbol" + chr(34) + "]) or 1.0"),
    ("vol20 read from the wrong key", "dry_run.py", 's.get("features", {}).get("vol20")', 's.get("features", {}).get("vol")'),
    ("direction dropped", "dry_run.py", '"direction": s["direction"]', '"direction": 1'),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_dry_run.py", WORK / "tests" / "test_dry_run.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_dry_run.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
