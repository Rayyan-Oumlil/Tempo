import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
TESTS = ["tests/test_earnings_reaction_small.py", "tests/test_earnings_reaction.py", "tests/test_ledger.py"]
ES = "earnings_reaction_small.py"
MUTATIONS = {
    "upper band edge inclusive": (ES, "MIN_ADV <= m[\"adv20\"] < MAX_ADV", "MIN_ADV <= m[\"adv20\"] <= MAX_ADV"),
    "lower band edge exclusive": (ES, "MIN_ADV <= m[\"adv20\"] < MAX_ADV", "MIN_ADV < m[\"adv20\"] < MAX_ADV"),
    "price floor removed": (ES, "m[\"close\"] >= MIN_PRICE and", ""),
    "large-cap band used": (ES, "MAX_ADV = LARGE_MIN_ADV", "MAX_ADV = 1e12"),
    "large-cap cost used": (ES, "ROUND_TRIP_COST = 0.006", "ROUND_TRIP_COST = 0.002"),
    "short side dropped": (ES, 'if m["reaction"] <= -THRESHOLD:', "if False:"),
    "no repeat guard": (ES, 'if h["symbol"] in recent:', "if False:"),
    "threshold ignored": (ES, "if m[\"reaction\"] >= THRESHOLD:", "if m[\"reaction\"] >= 0:"),
}

def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(SRC / "evidence", WORK / "evidence")
    (WORK / "tests").mkdir()
    for t in TESTS:
        shutil.copy(SRC / t, WORK / t)

def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", *TESTS, "-q", "-p", "no:cacheprovider"],
                       cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]

fresh(); print("unmutated copy:", run())
for name, (file, old, new) in MUTATIONS.items():
    fresh()
    f = WORK / "tempo" / file
    text = f.read_text(encoding="utf-8")
    if old not in text:
        print(f"{name:<42} -> NOT FOUND"); continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<42} -> {run()}")
