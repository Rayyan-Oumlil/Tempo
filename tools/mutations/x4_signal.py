import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
MUTATIONS = {
    "open day kept": ("s = s[s.index < pd.Timestamp(today)]", "s = s"),
    "wrong hourly bar": ("dt.time(23)", "dt.time(22)"),
    "empty hourly close accepted": ("if close is None:", "if False:"),
    "substitution not recorded": ("filled.attrs[SOURCE_ATTR] = HOURLY_SOURCE", "filled.attrs[SOURCE_ATTR] = DAILY_SOURCE"),
    "source dropped from the signal": ("close_source=close.attrs.get(SOURCE_ATTR, DAILY_SOURCE)", "close_source=DAILY_SOURCE"),
}

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_x4_signal.py", WORK / "tests" / "test_x4_signal.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_x4_signal.py", "-q", "-p", "no:cacheprovider"],
                       cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]

fresh(); print("unmutated copy:", run())
for name, (old, new) in MUTATIONS.items():
    fresh()
    f = WORK / "tempo" / "x4_signal.py"
    text = f.read_text(encoding="utf-8")
    if old not in text:
        print(f"{name:<42} -> NOT FOUND"); continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<42} -> {run()}")
