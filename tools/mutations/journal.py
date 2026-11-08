import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ("torn tail never skipped", "if n == len(lines):", "if False:"),
    ("every bad line skipped", "if n == len(lines):", "if True:"),
    ("torn tail not repaired on append", "        self._repair_tail()\n", ""),
    ("complete record without newline discarded", "            complete = True  # a whole record", "            complete = False  # a whole record"),
    ("torn fragment not kept", 'torn.write(fragment + b"\\n")', 'torn.write(b"")'),
    ("fragment not removed", "                f.truncate(cut)", "                pass"),
    ("healthy files rewritten", 'if f.read(1) == b"\\n":', "if False:"),
    ("lock not taken by the test helper", "        with journal.lock():\n            value = int(", "        if True:\n            value = int("),
    ("lock never acquired", "                    _try_lock(handle)\n", "                    pass\n"),
]
TEST_FILES = ["tests/test_journal_crash.py", "tests/test_journal_state.py", "tests/journal_worker.py", "tests/fakes.py"]


def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    for f in TEST_FILES:
        shutil.copy(SRC / f, WORK / f)
    shutil.copy(SRC / "pytest.ini", WORK / "pytest.ini")
    for extra in ("rules.json",):
        if (SRC / extra).exists():
            shutil.copy(SRC / extra, WORK / extra)


def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_journal_crash.py", "tests/test_journal_state.py", "-q", "-p", "no:cacheprovider"],
                       cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]


fresh()
print("unmutated copy:", run())
for name, old, new in M:
    fresh()
    target = WORK / ("tests/journal_worker.py" if name.startswith("lock not taken") else "tempo/journal.py")
    text = target.read_text(encoding="utf-8")
    if old not in text:
        print(f"{name:<44} -> PATTERN NOT FOUND")
        continue
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<44} -> {run()}")
