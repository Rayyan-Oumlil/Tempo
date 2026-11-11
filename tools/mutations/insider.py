import shutil, subprocess, sys, tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parents[2]
WORK = Path(tempfile.mkdtemp(prefix="tempo-mutate-")) / "copy"
M = [
    ("any transaction code counts", 'if _text(tx, "transactionCoding/transactionCode") != "P" or', 'if False or'),
    ("disposals count", '_text(tx, "transactionAmounts/transactionAcquiredDisposedCode/value") != "A":', 'False:'),
    ("10b5-1 flag ignored", 'or _text(root, "aff10b5One").lower() in ("1", "true"):', ':'),
    ("10b5-1 flag spelled true ignored", 'in ("1", "true"):  # both spellings occur', '== "1":'),
    ("routine roles: ten-percent owners counted", 'for flag in ("isDirector", "isOfficer")', 'for flag in ("isDirector", "isOfficer", "isTenPercentOwner")'),
    ("window includes day 8", "if start < b[\"filing_date\"] <= asof.isoformat():", "if (asof - timedelta(days=window_days + 1)).isoformat() < b[\"filing_date\"] <= asof.isoformat():"),
    ("future filings included", "<= asof.isoformat():", "<= '9999-12-31':"),
    ("one insider is enough", "if len(owners) >= min_owners and", "if len(owners) >= 1 and"),
    ("money threshold strict", "value >= min_value and", "value > min_value and"),
    ("price threshold ignored", "and vwap >= min_price:", ":"),
    ("vwap unweighted", "vwap = value / shares", "vwap = sum(r['price'] for r in rows) / len(rows)"),
    ("amendments included", 'INDEX_ROW = re.compile(r"^4\\s+', 'INDEX_ROW = re.compile(r"^4(?:/A)?\\s+'),
    ("duplicates in the index not merged", "if accession in seen:\n            continue\n        seen.add(accession)", "seen.add(accession)"),
    ("resignal window ignored", "if c[\"symbol\"] in recent:", "if False:"),
    ("DTD check removed", '"<!DOCTYPE" in document.upper() or "<!ENTITY" in document.upper()', "False"),
    ("size limit removed", "len(document) > MAX_DOCUMENT_CHARS or", "False or"),
    ("cost assumption dropped", '"round_trip_cost": ROUND_TRIP_COST, ', ""),
    ("odd symbols allowed", 'SYMBOL = re.compile(r"^[A-Z]{1,5}$")', 'SYMBOL = re.compile(r".*")'),
]


def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    shutil.copytree(SRC / "tempo", WORK / "tempo", ignore=shutil.ignore_patterns("__pycache__"))
    (WORK / "tests").mkdir()
    shutil.copy(SRC / "tests" / "test_insider.py", WORK / "tests" / "test_insider.py")


def run():
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tests/test_insider.py", "-q", "-p", "no:cacheprovider"], cwd=WORK, capture_output=True, text=True)
    return r.stdout.strip().splitlines()[-1]


fresh()
print("unmutated copy:", run())
for name, old, new in M:
    fresh()
    f = WORK / "tempo" / "insider.py"
    text = f.read_text(encoding="utf-8")
    if old not in text:
        print(f"{name:<38} -> PATTERN NOT FOUND")
        continue
    f.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"{name:<38} -> {run()}")
