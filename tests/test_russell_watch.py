import pytest

from tempo import russell_watch as rw
from tempo.data import Bars
from tempo.exec_score import Intraday

DAYS = ["2026-11-13", "2026-12-10", "2026-12-11", "2026-12-14"]


def bars(opens, closes):
    return Bars(DAYS, opens, [max(o, c) for o, c in zip(opens, closes)], [min(o, c) for o, c in zip(opens, closes)], closes)


def test_list_loading_refuses_bad_files(tmp_path):
    p = tmp_path / "l.csv"
    with pytest.raises(rw.ListError):
        rw.load_list(p)
    for text in ("symbol,action\n", "symbol,action\nAAA,buy\n", "symbol,action\nAAA,add\nAAA,delete\n", "symbol,action\n,add\n"):
        p.write_text(text)
        with pytest.raises(rw.ListError):
            rw.load_list(p)
    p.write_text("symbol,action\n aaa , ADD\nBBB,delete\nAAA,add\n")
    assert rw.load_list(p) == {"AAA": "add", "BBB": "delete"}


def test_window_returns_use_the_right_bars():
    daily = bars([100, 100, 110, 112], [100, 105, 111, 114.0])
    intra = Intraday({("2026-12-11", "15:55"): 110.5})
    r = rw.window_returns(daily, intra, "2026-12-11")
    assert r["runup"] == pytest.approx(105 / 100 - 1)             # announce close -> close the day before the event
    assert r["day"] == pytest.approx(110.5 / 110 - 1)
    assert r["last5"] == pytest.approx(111 / 110.5 - 1)
    assert r["reverse"] == pytest.approx(114 / 111 - 1)


def test_a_missing_bar_gives_none_not_a_guess():
    daily = bars([100, 100, 110, 112], [100, 105, 111, 114.0])
    r = rw.window_returns(daily, Intraday({}), "2026-12-11")
    assert r["day"] is None and r["last5"] is None and r["runup"] is not None
    assert all(v is None for v in rw.window_returns(None, None, "2026-12-11").values())


def test_signed_excess_flips_for_deletions_and_subtracts_the_benchmark():
    stock = {"runup": 0.05, "day": 0.01, "last5": -0.02, "reverse": None}
    bench = {"runup": 0.02, "day": 0.00, "last5": 0.00, "reverse": 0.01}
    add, dele = rw.measure("add", stock, bench), rw.measure("delete", stock, bench)
    assert add["runup"] == pytest.approx(0.03) and dele["runup"] == pytest.approx(-0.03)
    assert add["last5"] == pytest.approx(-0.02) and dele["last5"] == pytest.approx(0.02) and add["reverse"] is None


def test_run_skips_names_with_no_data_and_summary_counts_only_real_values():
    daily = bars([100, 100, 110, 112], [100, 105, 111, 114.0])
    intra = Intraday({("2026-12-11", "15:55"): 110.5})
    rows, missing = rw.run({"AAA": "add", "ZZZ": "delete"}, lambda s: None if s == "ZZZ" else daily, lambda s: intra)
    assert missing == ["ZZZ"] and [r["symbol"] for r in rows] == ["AAA"]
    s = rw.summarize(rows)
    assert s["add"]["runup"][0] == 1 and s["delete"]["runup"] == (0, None)
    assert "n" in rw.render(s) or "(" in rw.render(s)
