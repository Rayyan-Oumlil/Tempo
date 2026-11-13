import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
TESTS = ["tests/test_champion.py", "tests/test_autopsy.py", "tests/test_short_volume.py", "tests/test_ledger.py"]
CH, AU = "champion.py", "autopsy.py"
MUTATIONS = {
    "registered on the day still valid": (CH, "pair.registered >= date.fromisoformat(first_challenger_signal)", "pair.registered > date.fromisoformat(first_challenger_signal)"),
    "too early check removed": (CH, "if len(days) < pair.min_days:", "if len(days) < 1:"),
    "margin ignored": (CH, "mean >= pair.margin", "mean >= 0"),
    "t bar ignored": (CH, "t >= pair.t_min", "t >= 0"),
    "halves ignored": (CH, "first > 0 and second > 0", "first + second > 0"),
    "challenger own return ignored": (CH, "own > 0}", "True}"),
    "pairing uses all days not common days": (CH, "days = sorted(set(champ) & set(chall))", "days = sorted(set(champ) | set(chall))"),
    "difference reversed": (CH, "diffs = [chall[d] - champ[d] for d in days]", "diffs = [champ[d] - chall[d] for d in days]"),
    "same-day registration allowed for collectors": (CH, "if pair.registered >= today:", "if pair.registered > today:"),
    "short registry rule accepted": (CH, "pair.min_days < 30 or", "pair.min_days < 0 or"),
    "wrong horizon scores used": (CH, 'if sc["horizon"] == horizon and', 'if sc["horizon"] != horizon and'),
    "loss with right idea and big slippage not execution": (AU, 'return "execution" if t.entry_slip > SLIP_TOL else "timing"', 'return "timing"'),
    "lucky win not flagged": (AU, 'return "win" if t.ledger_ret is None or t.ledger_ret > 0 else "lucky win"', 'return "win"'),
    "short slippage sign wrong": (AU, 'd * (st["fill_price"] / st["ref_price"] - 1)', '(st["fill_price"] / st["ref_price"] - 1)'),
    "paper return ignores direction": (AU, 'd * (st["exit_fill_price"] / st["fill_price"] - 1)', '(st["exit_fill_price"] / st["fill_price"] - 1)'),
    "no multiple comparison correction": (AU, "limit = bh_threshold([p_value(t) for t in ts])", "limit = 0.05"),
    "bh bound ignores the rank (Bonferroni)": (AU, "p <= k * q / m", "p <= q / m"),
    "bh uses the largest passing p wrongly (smallest)": (AU, "return max(passing) if passing else None", "return min(passing) if passing else None"),
    "bh underflowed p-value treated as nothing": (AU, "return max(passing) if passing else None", "return max(passing) or None"),
    "p-value one-sided": (AU, "return 2 * (1 - statistics.NormalDist().cdf(abs(t)))", "return 1 - statistics.NormalDist().cdf(abs(t))"),
    "tiny cells examined": (AU, "eligible = [c for c in cells if len(c[2]) >= MIN_CELL]", "eligible = [c for c in cells if len(c[2]) >= 2]"),
    "vix history ignored": (AU, "if len(past) < VIX_MIN_HISTORY:", "if len(past) < 0:"),
    "variant min z ignored": ("short_volume.py", 'and -z[s] >= variant.min_abs_z]', ']'),
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
