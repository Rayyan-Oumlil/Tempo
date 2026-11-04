import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ("late entries allowed", "elif entry_day < today:\n                out[\"missed\"].append(s)", "elif entry_day < today:\n                out[\"enter\"].append(s)"),
    ("early entries allowed", "if entry_day == today:", "if entry_day <= today + timedelta(days=1):"),
    ("exit a day early", "exit_day <= today:", "exit_day <= today + timedelta(days=1):"),
    ("exit never due", "known[\"status\"] == \"entered\" and exit_day <= today:", "known[\"status\"] == \"entered\" and exit_day < today:"),
    ("all sources traded", "horizon = HORIZONS.get(s[\"source\"])\n        if horizon is None:\n            continue", "horizon = HORIZONS.get(s[\"source\"], 5)"),
    ("shorts bought", 'MarketOrder("BUY" if s["direction"] == 1 else "SELL", qty,', 'MarketOrder("BUY", qty,'),
    ("exit side not flipped", 'MarketOrder("SELL" if entry["direction"] == 1 else "BUY", entry["qty"],', 'MarketOrder("BUY" if entry["direction"] == 1 else "SELL", entry["qty"],'),
    ("refusal crashes instead of skipping", "        except OrderRefused as exc:\n            _skip(paper, s, f\"order door refused: {exc}\", say)\n            continue", "        except KeyError as exc:\n            continue"),
    ("size too large", "NOTIONAL_PCT = 0.5", "NOTIONAL_PCT = 5.0"),
    ("entry delay removed", "_minutes_into_session(now) >= ENTRY_DELAY_MINUTES", "True"),
    ("exit lead removed", "minute >= close_min - EXIT_LEAD_MINUTES", "minute >= 0"),
    ("horizon off by one", "add_trading_days(entry, horizon - 1)", "add_trading_days(entry, horizon)"),
    ("unqualified symbols traded", "if not ib.qualifyContracts(contract):", "if False:"),
    ("zero-size positions traded", "if qty < 1:", "if qty < 0:"),
    ("duplicate entries allowed", "if known is None:", "if known is None or True:"),
    ("preflight mode check inverted", 'Check("mode normal", mode == "normal"', 'Check("mode normal", mode != "normal"'),
    ("preflight orders-enabled inverted", 'Check("orders enabled", not readonly', 'Check("orders enabled", readonly'),
    ("dry run records outcomes", 'if not getattr(trade, "dry_run", False):', "if True:"),
    ("dry run skips the door checks", "    if not exit_order:\n        _check_entry(", "    if False:\n        _check_entry("),
    ("dry run skips whatIf", "state = ib.whatIfOrder(contract, probe)", "state = None"),
    ("dry run forgets the tif", 'probe.tif = "DAY"', "pass"),
]


def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(SRC / "tests", WORK / "tests", ignore=shutil.ignore_patterns("__pycache__", "live"))


def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_paper_run.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]


fresh()
print("unmutated copy:", run())
for name, old, new in M:
    fresh()
    f = WORK / "tempo" / "paper_run.py"
    text = f.read_text(encoding="utf-8")
    if old not in text:
        print(f"{name:<38} -> PATTERN NOT FOUND")
        continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<38} -> {run()}")
