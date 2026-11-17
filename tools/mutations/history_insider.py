import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
TARGET, TEST = "history_insider.py", "test_history_insider.py"
M = [
    ("amendments counted", 'r["DOCUMENT_TYPE"] == "4"', 'r["DOCUMENT_TYPE"] in ("4", "4/A")'),
    ("10b5-1 flag ignored", 'r.get("AFF10B5ONE", "").strip().lower() not in ("1", "true")', 'True'),
    ("odd symbols allowed", "and cluster_rule.SYMBOL.match(symbol) and symbol not in cluster_rule.PLACEHOLDER_SYMBOLS", ""),
    ("placeholder symbols allowed", "and symbol not in cluster_rule.PLACEHOLDER_SYMBOLS", ""),
    ("any transaction code counts", 'or r["TRANS_CODE"] != "P"', "or False"),
    ("dispositions count", 'or r["TRANS_ACQUIRED_DISP_CD"] != "A"', ""),
    ("officers and directors not told apart", 'if "Officer" in r["RPTOWNER_RELATIONSHIP"] or "Director" in r["RPTOWNER_RELATIONSHIP"]:', "if True:"),
    ("late filings kept", "<= MAX_LAG_DAYS:", "<= 99999:"),
    ("typo dates kept", "if 0 <= (date.fromisoformat", "if -99999 <= (date.fromisoformat"),
    ("entry on the signal day", "asof, entry = calendar[k], calendar[k + 1]", "asof, entry = calendar[k], calendar[k]"),
    ("entries after the cap", "if entry < first or entry > last:", "if entry < first:"),
    ("entries before the start", "if entry < first or entry > last:", "if entry > last:"),
    ("window of one day", "for n in range(WINDOW_DAYS)", "for n in range(1)"),
    ("resignal ignored", "< cluster_rule.RESIGNAL_DAYS:", "< 0:"),
    ("resignal clock not reset", "last_signal[source][c[\"symbol\"]] = date.fromisoformat(entry)", "pass"),
    ("unscored trades counted as scored", 'counts["unscored"] += 1', 'counts["scored"] += 1'),
    ("direction short", "gross = trade_excess(stock, spy, entry, 1, horizon)", "gross = trade_excess(stock, spy, entry, -1, horizon)"),
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
