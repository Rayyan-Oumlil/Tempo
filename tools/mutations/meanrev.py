import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
MUTATIONS = {
    "no trend filter": ("if r[t] is not None and close > slow[t] and r[t] < entry:", "if r[t] is not None and r[t] < entry:"),
    "exit direction flipped": ("elif fast[t] is not None and close > fast[t]:", "elif fast[t] is not None and close < fast[t]:"),
    "next_open uses today's signal (look-ahead)": ("target, price = (signals[t - 1] if t > 0 else 0), opens[t]", "target, price = signals[t], opens[t]"),
    "sma window peeks one day ahead": ("sum(values[t + 1 - n:t + 1]) / n for t", "sum(values[t + 1 - n:t + 1]) / n + 0.0 * values[min(t + 1, len(values) - 1)] + (values[min(t + 1, len(values) - 1)] - values[t]) / n for t"),
    "rsi smoothing ignores the loss": ("avg_loss = (avg_loss * (period - 1) + losses[t - 1]) / period", "avg_loss = avg_loss"),
    "shuffle does nothing": ("    rng.shuffle(shapes)\n", "    pass\n"),
    "IBS entry threshold dropped": ("if pos == 0 and value < entry:", "if pos == 0 and value < 1.0:"),
}

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_meanrev.py", WORK / "tests" / "test_meanrev.py")

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_meanrev.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]

fresh(); print("unmutated copy:", run())
for name, (old, new) in MUTATIONS.items():
    fresh()
    f = WORK / "tempo" / "meanrev.py"
    text = f.read_text(encoding="utf-8")
    assert old in text, name
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<46} -> {run()}")
