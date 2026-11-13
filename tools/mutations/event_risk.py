import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ('probe words lost', 'event_risk.py', '"probe": (r"SEC', '"probe": (r"XXSEC'),
    ('substring matching', 'event_risk.py', 'r"' + chr(92) + 'b(?:" + "|".join(words) + r")' + chr(92) + 'b"', 'r"(?:" + "|".join(words) + r")"'),
    ('case sensitive', 'event_risk.py', 're.IGNORECASE)', '0)'),
    ('old news flagged', 'event_risk.py', 'or when < cutoff or key in seen:', 'or key in seen:'),
    ('seen not respected', 'event_risk.py', 'or when < cutoff or key in seen:', 'or when < cutoff:'),
    ('seen not updated', 'event_risk.py', '            seen.add(key)\n', '            pass\n'),
    ('failed news treated as clean', 'event_risk.py', '            if sym not in failed:\n                failed.append(sym)\n', '            pass\n'),
    ('key ignores the signal', 'event_risk.py', 'f"{signal_id}|{_TAG.sub', 'f"{_TAG.sub'),
    ('exited positions held', 'event_risk.py', 't.get("status") == "entered"', 't.get("status") in ("entered", "exited")'),
    ('failure share threshold off', 'event_risk.py', '> MAX_FAILED_SHARE', '> 1.0'),
    ('insider purchases read as M&A', 'event_risk.py', 'r"acquires(?! [\d,]+ of)"', 'r"acquires"'),
]

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_event_risk.py", WORK / "tests" / "test_event_risk.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_event_risk.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
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
