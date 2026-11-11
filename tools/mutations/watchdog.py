import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
MUTATIONS = {
    "alert on the first failure": ("if failures == ALERT_AFTER:", "if failures == 1:"),
    "maintenance window counted as an outage": ("    if in_maintenance(now):\n        return state, []", "    if False:\n        return state, []"),
    "recovery announced after a mere blip": ('(["recovered"] if state.failures >= ALERT_AFTER else [])', '["recovered"]'),
    "recovery keeps the failure counter": ("return State(), (", "return state, ("),
    "maintenance ends too early": ("t >= MAINTENANCE_START or t < MAINTENANCE_END", "t >= MAINTENANCE_START or t < time(0, 0)"),
    "never restarts": ("if failures == RESTART_AFTER and not restarted:", "if False:"),
}

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_watchdog.py", WORK / "tests" / "test_watchdog.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_watchdog.py", "-q", "-p", "no:cacheprovider"],
                       cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]

fresh(); print("unmutated copy:", run())
for name, (old, new) in MUTATIONS.items():
    fresh()
    f = WORK / "tempo" / "watchdog.py"
    text = f.read_text(encoding="utf-8")
    if old not in text:
        print(f"{name:<42} -> NOT FOUND"); continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<42} -> {run()}")
