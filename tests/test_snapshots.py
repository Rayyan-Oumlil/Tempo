import gzip
from datetime import date

import pytest

from tempo import snapshots as sn


def finra_text(n=4100, header=sn.FINRA_HEADER):
    return header + "\n" + "\n".join(f"20261110|S{i}|{100 + i}|0|{300 + i}|B,Q,N" for i in range(n)) + "\n4100\n"


def test_parse_short_volume_reads_rows_and_ignores_the_trailer():
    rows = sn.parse_short_volume(finra_text())
    assert rows["S5"] == (105.0, 305.0) and len(rows) == 4100


@pytest.mark.parametrize("text", ["", "wrong|header\n1|2", finra_text(n=10), finra_text().replace("|105|", "|abc|"), finra_text(header="Date|Symbol|Short|Total")],
                         ids=["empty", "header", "truncated", "bad-number", "full-size-wrong-header"])
def test_parse_refuses_a_changed_or_truncated_file(text):
    with pytest.raises(sn.SnapshotError):
        sn.parse_short_volume(text)


def test_finra_collection_saves_once_and_reports_unpublished(tmp_path):
    calls = []

    def fetch(url):
        calls.append(url)
        if "20261111" in url:
            raise sn.NotPublished("404")
        return finra_text().encode()

    first = sn.collect_finra(date(2026, 11, 11), fetch, tmp_path, backfill=3)
    assert first["not_published"] == ["2026-11-11"] and len(first["saved"]) == 2
    n = len(calls)
    second = sn.collect_finra(date(2026, 11, 11), fetch, tmp_path, backfill=3)
    assert len(second["have"]) == 2 and len(calls) == n + 1          # only the unpublished day is asked again
    assert sn.load_short_volume(date(2026, 11, 10), tmp_path)["S1"] == (101.0, 301.0)
    assert gzip.decompress((tmp_path / "finra_short_volume" / "20261110.txt.gz").read_bytes()).startswith(b"Date|")


def test_a_malformed_download_is_not_kept(tmp_path):
    with pytest.raises(sn.SnapshotError):
        sn.collect_finra(date(2026, 11, 11), lambda u: b"<html>oops</html>", tmp_path, backfill=1)
    assert not list((tmp_path / "finra_short_volume").glob("*.gz"))


def test_fred_requires_a_plausible_file(tmp_path):
    good = ("observation_date,VIXCLS\n" + "\n".join(f"2020-01-{i % 28 + 1:02d},1" for i in range(600))).encode()
    assert sn.collect_fred(lambda u: good, tmp_path) == ["VIXCLS", "VXVCLS"]
    with pytest.raises(sn.SnapshotError):
        sn.collect_fred(lambda u: b"observation_date,VIXCLS\n2020-01-01,1", tmp_path)


def test_ftd_periods_walk_back_half_months():
    assert sn.ftd_periods(date(2026, 11, 11), 3) == [("202610", "b"), ("202610", "a"), ("202609", "b")]
    assert sn.ftd_periods(date(2026, 11, 20), 2) == [("202611", "a"), ("202610", "b")]
    assert sn.ftd_periods(date(2026, 1, 5), 2) == [("202512", "b"), ("202512", "a")]


def test_ftd_must_be_a_zip(tmp_path):
    with pytest.raises(sn.SnapshotError):
        sn.collect_ftd(date(2026, 11, 11), lambda u: b"<html>", tmp_path)
    got = sn.collect_ftd(date(2026, 11, 11), lambda u: b"PK\x03\x04data", tmp_path)
    assert len(got["saved"]) == 4
