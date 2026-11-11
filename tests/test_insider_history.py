import io
import zipfile

import pytest

from tempo.insider_history import HistoryMissing, build_index, is_routine, purchase_months_from_zip

SUB = "ACCESSION_NUMBER\tFILING_DATE\tDOCUMENT_TYPE\tISSUERCIK\tISSUERTRADINGSYMBOL\tAFF10B5ONE\n"
OWN = "ACCESSION_NUMBER\tRPTOWNERCIK\tRPTOWNER_RELATIONSHIP\n"
TRX = "ACCESSION_NUMBER\tTRANS_DATE\tTRANS_CODE\tTRANS_SHARES\tTRANS_PRICEPERSHARE\tTRANS_ACQUIRED_DISP_CD\n"


def make_zip(subs, owners, trans) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("SUBMISSION.tsv", SUB + "".join("\t".join(r) + "\n" for r in subs))
        z.writestr("REPORTINGOWNER.tsv", OWN + "".join("\t".join(r) + "\n" for r in owners))
        z.writestr("NONDERIV_TRANS.tsv", TRX + "".join("\t".join(r) + "\n" for r in trans))
    return buf.getvalue()


def sub(acc, doc="4", symbol="ACME", aff="0"):
    return (acc, "01-NOV-2025", doc, "0000555", symbol, aff)


def test_counted_officer_and_director_purchases_give_owner_months():
    raw = make_zip(
        subs=[sub("A1"), sub("A2")],
        owners=[("A1", "0000000011", "Director"), ("A1", "0000000012", "TenPercentOwner"), ("A2", "0000000013", "Director,Officer")],
        trans=[("A1", "03-NOV-2025", "P", "100", "10", "A"), ("A2", "15-FEB-2025", "P", "5", "20", "A")])
    assert purchase_months_from_zip(raw) == {"11": {"2025-11"}, "13": {"2025-02"}}   # CIKs without leading zeros


@pytest.mark.parametrize("acc_sub, owner, tx", [
    (sub("A1", doc="4/A"), ("A1", "1", "Director"), ("A1", "03-NOV-2025", "P", "1", "1", "A")),      # amendment
    (sub("A1", aff="1"), ("A1", "1", "Director"), ("A1", "03-NOV-2025", "P", "1", "1", "A")),        # 10b5-1
    (sub("A1", aff="true"), ("A1", "1", "Director"), ("A1", "03-NOV-2025", "P", "1", "1", "A")),     # 10b5-1 spelled true
    (sub("A1", symbol="BRK-B"), ("A1", "1", "Director"), ("A1", "03-NOV-2025", "P", "1", "1", "A")), # odd symbol
    (sub("A1"), ("A1", "1", "TenPercentOwner"), ("A1", "03-NOV-2025", "P", "1", "1", "A")),          # not officer/director
    (sub("A1"), ("A1", "1", "Director"), ("A1", "03-NOV-2025", "S", "1", "1", "D")),                 # a sale
    (sub("A1"), ("A1", "1", "Director"), ("A1", "03-NOV-2025", "P", "1", "0", "A")),                 # unpriced
])
def test_uncounted_rows_are_ignored(acc_sub, owner, tx):
    assert purchase_months_from_zip(make_zip([acc_sub], [owner], [tx])) == {}


def index_with(owner_months, years=(2023, 2024, 2025)):
    return {"years": list(years), "owners": {k: sorted(v) for k, v in owner_months.items()}}


def test_routine_means_the_same_month_in_each_of_the_three_previous_years():
    idx = index_with({"11": {"2023-11", "2024-11", "2025-11"}, "12": {"2023-11", "2025-11"}, "13": {"2024-11", "2025-11", "2025-03"}})
    assert is_routine("0000000011", 2026, 11, idx) is True
    assert is_routine("0000000012", 2026, 11, idx) is False      # missed 2024
    assert is_routine("0000000013", 2026, 11, idx) is False      # missed 2023
    assert is_routine("99", 2026, 11, idx) is False              # no history: opportunistic (registered rule)
    assert is_routine("0000000011", 2026, 10, idx) is False      # another month


def test_history_that_does_not_cover_the_three_years_fails_loudly():
    with pytest.raises(HistoryMissing, match="2023"):
        is_routine("11", 2026, 11, index_with({}, years=(2024, 2025)))


def test_build_index_merges_quarters_and_records_the_years_covered():
    q1 = make_zip([sub("A1")], [("A1", "0000000011", "Officer")], [("A1", "03-NOV-2023", "P", "1", "1", "A")])
    q2 = make_zip([sub("B1")], [("B1", "0000000011", "Officer")], [("B1", "04-NOV-2024", "P", "1", "1", "A")])
    fetched = []

    def fetch(quarter):
        fetched.append(quarter)
        return {"2023q4": q1, "2024q4": q2}.get(quarter, make_zip([], [], []))

    idx = build_index([2023, 2024], fetch)
    assert idx["years"] == [2023, 2024] and idx["owners"] == {"11": ["2023-11", "2024-11"]}
    assert fetched == [f"{y}q{q}" for y in (2023, 2024) for q in (1, 2, 3, 4)]
