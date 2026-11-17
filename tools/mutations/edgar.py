import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ("timeouts are not retried", "raise EdgarError(url, repr(exc), retryable=True) from exc", "raise EdgarError(url, repr(exc)) from exc"),
    ("server errors are not retried", "retryable=exc.code in RETRYABLE_HTTP)", "retryable=False)"),
    ("403 and 404 are retried too", "retryable=exc.code in RETRYABLE_HTTP)", "retryable=True)"),
    ("retries without a limit", "for delay in (*RETRY_DELAYS, None):", "for delay in (*RETRY_DELAYS, *RETRY_DELAYS, 1.0):"),
    ("no wait between tries", "            sleep(delay)\n", "            pass\n"),
    ("final failure swallowed", "            if delay is None or not err.retryable:\n                raise", "            if not err.retryable:\n                raise"),
    ("throttle slot not reserved", "            self._last = slot\n", "            pass\n"),
]


def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_edgar.py", WORK / "tests" / "test_edgar.py")


def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_edgar.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]


fresh()
print("unmutated copy:", run())
for name, old, new in M:
    fresh()
    f = WORK / "tempo" / "edgar.py"
    text = f.read_text(encoding="utf-8").replace("\r\n", "\n")
    if old not in text:
        print(f"{name:<38} -> PATTERN NOT FOUND")
        continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<38} -> {run()}")
