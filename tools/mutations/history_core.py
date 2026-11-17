import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
TARGET, TEST = "history_core.py", "test_history_core.py"
M = [
    ("direction ignored", "return direction * (stock_ret - beta * spy_ret)", "return (stock_ret - beta * spy_ret)"),
    ("no beta hedge", "stock_ret - beta * spy_ret", "stock_ret - 0 * spy_ret"),
    ("hedged with beta 1 instead of the stock's", "stock_ret - beta * spy_ret", "stock_ret - 1 * spy_ret"),
    ("entry at the close", "/ stock.open[stock.pos[entry_day]] - 1", "/ stock.close[stock.pos[entry_day]] - 1"),
    ("exit a day early", "exit_day = spy.dates[k + horizon]", "exit_day = spy.dates[k + horizon - 1]"),
    ("spy measured from its close", "spy.close[k + horizon] / spy.open[k] - 1", "spy.close[k + horizon] / spy.close[k] - 1"),
    ("a missing beta is guessed", "    if beta is None:\n        return None\n    stock_ret", "    beta = 1.0 if beta is None else beta\n    stock_ret"),
    ("train years counted", "test = [t for t in trades if t.day[:4] in years]", "test = list(trades)"),
    ("cost not subtracted", "mean_net = gross - cost", "mean_net = gross"),
    ("never kills", "if ci[0] <= 0:", "if ci[0] < -9:"),
    ("t bar ignored", "if t_stat is None or t_stat < T_BAR:", "if t_stat is None:"),
    ("a losing year ignored", "weak = [y for y, (_, m) in year_stats.items() if m <= 0]", "weak = []"),
    ("a missing year ignored", "missing = [y for y in years if y not in year_stats]", "missing = []"),
    ("stress test ignored", "    if stress <= 0:", "    if False:"),
    ("event floor ignored", "    if len(test) < MIN_EVENTS:", "    if False:"),
    ("day floor ignored", "if len(by_day) < MIN_DAYS:", "if False:"),
    ("stress below the registered cost", "stress = gross - STRESS * cost", "stress = gross - cost"),
    ("year stats gross", "year_stats = {y: (len(v), fmean(v) - cost)", "year_stats = {y: (len(v), fmean(v))"),
]


def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / TEST, WORK / "tests" / TEST)


def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", f"tests/{TEST}", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]


fresh()
print("unmutated copy:", run())
for name, old, new in M:
    fresh()
    f = WORK / "tempo" / TARGET
    text = f.read_text(encoding="utf-8").replace("\r\n", "\n")
    if old not in text:
        print(f"{name:<44} -> PATTERN NOT FOUND")
        continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<44} -> {run()}")
