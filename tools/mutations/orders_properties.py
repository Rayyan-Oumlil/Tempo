import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ("position cap dropped", "if order.totalQuantity * worst_price > cap:", "if False:"),
    ("cap uses reference price only", "worst_price = max(p for p in (ref_price, limit, stop) if p)", "worst_price = ref_price"),
    ("exit may exceed what is held", "return held > 0 and qty <= held - committed", "return held > 0"),
    ("short exit may exceed what is held", "return held < 0 and qty <= -held - committed", "return held < 0"),
    ("resting orders ignored", "return held > 0 and qty <= held - committed", "return held > 0 and qty <= held"),
    ("oca legs summed", "groups[t.order.ocaGroup] = max(groups.get(t.order.ocaGroup, 0.0), remaining)", "loose += remaining"),
    ("entry allowed when closed", 'raise OrderRefused("market is closed (entries need regular hours or outsideRth=True)")', "pass"),
    ("reduce_only ignored", 'if get_mode(state_path) != "normal":', "if False:"),
    ("unknown equity allowed", "if not equity_usd or equity_usd <= 0:", "if False:"),
    ("unknown price allowed", "if not ref_price or ref_price <= 0:", "if False:"),
    ("buy price band dropped", 'if limit and order.action == "BUY" and limit > ref_price * (1 + band):', "if False:"),
    ("sell price band dropped", 'if limit and order.action == "SELL" and limit < ref_price * (1 - band):', "if False:"),
    ("duplicate check dropped", "_check_duplicate(contract, order, journal, limits.duplicate_window_s)", "pass"),
    ("live account allowed", "assert_paper(accounts[0] if accounts else \"none\")", "pass"),
]
TEST_FILES = ["tests/invariants/test_properties.py", "tests/fakes.py"]


def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests" / "invariants").mkdir(parents=True)
    for f in TEST_FILES:
        shutil.copy(SRC / f, WORK / f)
    shutil.copy(SRC / "pytest.ini", WORK / "pytest.ini")
    for extra in ("rules.json",):
        if (SRC / extra).exists():
            shutil.copy(SRC / extra, WORK / extra)


def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/invariants/test_properties.py", "-q", "-p", "no:cacheprovider"],
                       cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]


fresh()
print("unmutated copy:", run())
for name, old, new in M:
    fresh()
    target = WORK / "tempo/orders.py"
    text = target.read_text(encoding="utf-8")
    if old not in text:
        print(f"{name:<44} -> PATTERN NOT FOUND")
        continue
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<44} -> {run()}")
