from datetime import date, datetime, timedelta

import pytest

from tempo.earnings_reaction import DayBars
from tempo.history_earnings import (ET, block_filings, earnings_filings, evaluate, events_for_symbol, forward_excess, load_bars, pick_sample,
                                    save_bars, signal_day)

DAYS: list[str] = []
_d = date(2020, 1, 2)
while len(DAYS) < 60:
    if _d.weekday() < 5:
        DAYS.append(_d.isoformat())
    _d += timedelta(days=1)


def spy_flat() -> DayBars:
    return DayBars(DAYS, [100.0] * len(DAYS), [1e9] * len(DAYS))


def at(day: str, hh: int, mm: int = 0) -> datetime:
    return datetime.fromisoformat(f"{day}T{hh:02d}:{mm:02d}:00").replace(tzinfo=ET)


def test_signal_day_before_open_is_that_day_after_close_is_the_next_and_intraday_is_skipped():
    assert signal_day(at(DAYS[30], 7), DAYS) == DAYS[30]
    assert signal_day(at(DAYS[30], 16, 5), DAYS) == DAYS[31]
    assert signal_day(at(DAYS[30], 10), DAYS) is None
    assert signal_day(at(DAYS[30], 9, 30), DAYS) is None
    assert signal_day(at(DAYS[30], 16, 0), DAYS) == DAYS[31]
    friday = next(n for n, d in enumerate(DAYS) if date.fromisoformat(d).weekday() == 4)
    saturday = date.fromisoformat(DAYS[friday]) + timedelta(days=1)
    assert saturday.weekday() == 5
    assert signal_day(at(saturday.isoformat(), 12), DAYS) == DAYS[friday + 1]  # weekend: the next bar
    assert signal_day(at(DAYS[-1], 18), DAYS) is None                          # no later bar known


def test_forward_excess_is_signed_and_subtracts_spy():
    spy = DayBars(DAYS, [100.0 + n for n in range(len(DAYS))], [1e9] * len(DAYS))
    stock = DayBars(DAYS, [50.0] * 40 + [55.0] * 20, [1e7] * len(DAYS))
    i = 37                                                   # five sessions later (index 42) the stock is at 55
    long_ = forward_excess(stock, spy, DAYS[i], 1)
    assert long_ == pytest.approx((55 / 50 - 1) - (spy.close[i + 5] / spy.close[i] - 1))
    assert forward_excess(stock, spy, DAYS[i], -1) == pytest.approx(-long_)


def test_forward_excess_is_none_when_a_bar_is_missing_or_the_future_is_unknown():
    spy = spy_flat()
    keep = [n for n in range(60) if n not in (30, 35)]       # the stock has no bar on sessions 30 and 35
    stock = DayBars([DAYS[n] for n in keep], [10.0] * len(keep), [1e7] * len(keep))
    assert forward_excess(stock, spy, DAYS[30], 1) is None   # start bar missing
    assert forward_excess(stock, spy, DAYS[25], 1) is None   # end bar (session 30) missing
    assert forward_excess(stock, spy, DAYS[26], 1) == 0.0    # both bars exist
    assert forward_excess(stock, spy, DAYS[57], 1) is None   # fewer than 5 sessions left
    assert forward_excess(stock, spy, "1999-01-01", 1) is None


def jump_stock(reaction_idx: int, up: bool) -> DayBars:
    close = [100.0] * len(DAYS)
    for n in range(reaction_idx, len(DAYS)):
        close[n] = 110.0 if up else 90.0
    for n in range(reaction_idx + 1, len(DAYS)):
        close[n] *= 1.02 if up else 0.98                      # the drift after the reaction day
    return DayBars(DAYS, close, [1e6] * len(DAYS))            # adv20 about 1e8 USD: the large band


def test_a_big_upside_reaction_is_a_long_event_in_the_large_band_with_a_positive_drift():
    rows = events_for_symbol("AAA", [("0001", at(DAYS[30], 7))], jump_stock(30, True), spy_flat())
    assert len(rows) == 1 and rows[0]["band"] == "large" and rows[0]["direction"] == 1
    assert rows[0]["reaction"] == pytest.approx(0.10) and rows[0]["drift"] == pytest.approx(0.02)


def test_a_big_downside_reaction_is_a_short_event_and_a_fall_afterwards_is_a_positive_drift():
    rows = events_for_symbol("AAA", [("0001", at(DAYS[30], 7))], jump_stock(30, False), spy_flat())
    assert rows[0]["direction"] == -1 and rows[0]["drift"] == pytest.approx(0.02)


def test_small_moves_intraday_filings_and_illiquid_names_make_no_event():
    quiet = DayBars(DAYS, [100.0] * len(DAYS), [1e6] * len(DAYS))
    assert events_for_symbol("AAA", [("1", at(DAYS[30], 7))], quiet, spy_flat()) == []
    assert events_for_symbol("AAA", [("1", at(DAYS[30], 11))], jump_stock(30, True), spy_flat()) == []
    thin = DayBars(DAYS, jump_stock(30, True).close, [10.0] * len(DAYS))          # about 1,000 USD a day: below both bands
    assert events_for_symbol("AAA", [("1", at(DAYS[30], 7))], thin, spy_flat()) == []


def test_the_small_band_is_used_between_500k_and_5m_of_dollar_volume():
    stock = jump_stock(30, True)
    small_stock = DayBars(DAYS, stock.close, [2e4] * len(DAYS))                    # about 2M USD a day
    assert events_for_symbol("AAA", [("1", at(DAYS[30], 7))], small_stock, spy_flat())[0]["band"] == "small"


def rows_with(drift: float, n_days: int, band: str = "large") -> list[dict]:
    return [{"band": band, "direction": 1, "day": f"d{n:04d}", "drift": drift} for n in range(n_days)]


def test_evaluate_kills_a_band_whose_mean_is_below_cost_and_keeps_one_above():
    assert evaluate(rows_with(0.0005, 60), "large").verdict.startswith("KILL")
    assert evaluate(rows_with(0.02, 60), "large").verdict.startswith("not killed")
    assert evaluate(rows_with(0.004, 60), "large").verdict.startswith("not killed")   # 40 bps against a 20 bps cost
    assert evaluate(rows_with(0.004, 60, "small"), "small").verdict.startswith("KILL")         # 40 bps against a 60 bps cost


def test_evaluate_gives_no_verdict_on_too_few_days_and_ignores_rows_without_a_forward_bar():
    assert evaluate(rows_with(0.02, 5), "large").mean is None
    rows = rows_with(0.02, 60) + [{"band": "large", "direction": 1, "day": "d9999", "drift": None}]
    assert evaluate(rows, "large").events == 60


def test_evaluate_splits_by_direction():
    rows = rows_with(0.03, 40) + [dict(r, direction=-1, drift=-0.01) for r in rows_with(0.0, 40)]
    assert evaluate(rows, "large", 1).mean == pytest.approx(0.03)
    assert evaluate(rows, "large", -1).mean == pytest.approx(-0.01)


def test_block_filings_picks_only_8k_with_item_202_and_converts_to_et():
    block = {"form": ["8-K", "8-K", "10-Q", "8-K"], "items": ["2.02,9.01", "5.02", "", "2.02"], "accessionNumber": ["a", "b", "c", "d"],
             "acceptanceDateTime": ["2020-02-04T21:05:00.000Z", "2020-02-04T21:05:00.000Z", "2020-02-04T21:05:00.000Z",
                                    "2020-07-01T11:00:00.000Z"]}
    got = block_filings(block)
    assert [a for a, _ in got] == ["a", "d"] and got[0][1].hour == 16 and got[1][1].hour == 7
    with pytest.raises(ValueError):
        block_filings({**block, "items": ["2.02"]})


def _one(acc: str, when: str) -> dict:
    return {"form": ["8-K"], "items": ["2.02"], "accessionNumber": [acc], "acceptanceDateTime": [when]}


def test_earnings_filings_follows_older_files_only_when_they_overlap_the_range():
    files = {"o.json": _one("old", "2012-05-01T20:00:00.000Z"), "a.json": _one("ancient", "2001-05-01T20:00:00.000Z")}
    sub = {"filings": {"recent": _one("new", "2024-05-01T20:00:00.000Z"),
                       "files": [{"name": "o.json", "filingFrom": "2010-01-01", "filingTo": "2015-01-01"},
                                 {"name": "a.json", "filingFrom": "1995-01-01", "filingTo": "2005-01-01"}]}}
    fetched: list[str] = []

    def older(name: str) -> dict:
        fetched.append(name)
        return files[name]
    assert [a for a, _ in earnings_filings(sub, older)] == ["old", "new"] and fetched == ["o.json"]
    assert [a for a, _ in earnings_filings(sub, older, first=date(2024, 1, 1))] == ["new"]
    assert [a for a, _ in earnings_filings(sub, older, last=date(2020, 1, 1))] == ["old"]        # the recent block is range-filtered too


def test_bars_round_trip_through_the_cache(tmp_path):
    bars = DayBars(["2020-01-02", "2020-01-03"], [1.5, 2.5], [10.0, 20.0])
    save_bars(tmp_path / "x" / "A.csv", bars)
    assert load_bars(tmp_path / "x" / "A.csv") == bars and load_bars(tmp_path / "none.csv") is None


def test_sample_is_reproducible_and_capped():
    mapping = {str(n): {"cik_str": n, "ticker": "T" + chr(65 + n % 26) + chr(65 + n // 26)} for n in range(300)}
    a, b = pick_sample(mapping, 50), pick_sample(mapping, 50)
    assert a == b and len(a) == 50 and len(pick_sample(mapping, 9999)) == 300
