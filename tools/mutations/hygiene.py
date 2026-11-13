import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ('spac suffix W ignored', 'hygiene.py', 'symbol[-1] in "UW"', 'symbol[-1] in "U"'),
    ('spac length not checked', 'hygiene.py', 'len(symbol) == 5 and', 'True and'),
    ('placeholder symbols ignored', 'hygiene.py', 'symbol in PLACEHOLDER_SYMBOLS or', 'False or'),
    ('one insider is enough', 'hygiene.py', 'MIN_INSIDERS = 3', 'MIN_INSIDERS = 1'),
    ('whole dollar tolerance too wide', 'hygiene.py', 'WHOLE_DOLLAR_TOL = 0.005', 'WHOLE_DOLLAR_TOL = 0.5'),
    ('whole dollar needs no insiders count', 'hygiene.py', 'n >= MIN_INSIDERS and', 'True and'),
    ('opportunistic count ignored', 'hygiene.py', 'f.get("n_insiders", f.get("n_opportunistic"))', 'f.get("n_insiders")'),
    ('other sources judged', 'hygiene.py', 'if signal["source"] not in SOURCES:', 'if False:'),
    ('contaminated kept in clean view', 'hygiene.py', 'if sig["source"] in SOURCES and contamination(sig) is None:', 'if sig["source"] in SOURCES:'),
    ('clean view not relabelled', 'hygiene.py', 'out.append({**r, "source": r["source"] + SUFFIX})', 'out.append(r)'),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_hygiene.py", WORK / "tests" / "test_hygiene.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_hygiene.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
