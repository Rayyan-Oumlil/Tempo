from datetime import date, datetime, timezone

import pytest

from tempo.daybars import DayBars
from tempo.earnings_reaction import ET, Filing
from tempo.news_split import (DRIFT, FADE, RESIDUAL, classify, earnings_symbols, headlines_in_window, load_sector_map, raw_return,
                              sector_residual, too_many_failed, vix_asof, window)

DAY = date(2026, 11, 17)          # Tuesday; previous session Monday 2026-11-16


def at(d, hh, mm=0, tz=ET):
    return datetime.fromisoformat(f"{d}T{hh:02d}:{mm:02d}:00").replace(tzinfo=tz)


def test_window_runs_from_the_previous_close_to_todays_close_and_skips_weekends():
    lo, hi = window(DAY)
    assert lo == at("2026-11-16", 16) and hi == at("2026-11-17", 16)
    assert window(date(2026, 11, 16))[0] == at("2026-11-13", 16)          # Monday: Friday's close


def test_headlines_inside_the_window_count_and_the_edges_are_inclusive():
    items = [(at("2026-11-16", 15, 59), "BRFG", "before"), (at("2026-11-16", 16), "BRFG", "edge lo"), (at("2026-11-17", 10), "DJ-N", "mid"),
             (at("2026-11-17", 16), "DJ-N", "edge hi"), (at("2026-11-17", 16, 1), "DJ-N", "after")]
    assert [h[2] for h in headlines_in_window(items, DAY)] == ["edge lo", "mid", "edge hi"]


def test_provider_times_are_utc_and_compared_in_new_york_time():
    utc = datetime(2026, 11, 17, 15, 0, tzinfo=timezone.utc)               # 10:00 ET: inside
    late = datetime(2026, 11, 17, 21, 30, tzinfo=timezone.utc)              # 16:30 ET: outside
    assert len(headlines_in_window([(utc, "BRFG", "x"), (late, "BRFG", "y")], DAY)) == 1


def filing(cik, items, accepted):
    return Filing(cik, "acc-" + cik, items, accepted)


def test_earnings_filings_in_the_window_exclude_a_symbol_at_any_hour():
    fs = [filing("1", ("2.02",), at("2026-11-16", 16, 30)), filing("2", ("2.02",), at("2026-11-17", 11)),
          filing("3", ("8.01",), at("2026-11-17", 7)), filing("4", ("2.02",), at("2026-11-13", 17)),
          filing("5", ("2.02",), at("2026-11-17", 7))]
    tickers = {"1": "AAA", "2": "BBB", "3": "CCC", "4": "DDD"}                  # 5 has no ticker
    assert earnings_symbols(fs, tickers, DAY) == {"AAA", "BBB"}


def test_classify_follows_news_fades_the_unexplained_and_skips_sympathy_and_earnings():
    assert classify(1, None, True, 3) == "earnings"                           # earnings beat everything
    assert classify(1, 0.0, False, 1) == (DRIFT, 1) and classify(-1, 0.0, False, 2) == (DRIFT, -1)
    assert classify(1, 0.06, False, 0) == (FADE, -1) and classify(-1, -0.06, False, 0) == (FADE, 1)
    assert classify(1, RESIDUAL, False, 0) == (FADE, -1)                      # exactly the bar counts
    assert classify(1, RESIDUAL - 0.001, False, 0) == "sympathy"
    assert classify(1, -0.05, False, 0) == "sympathy"                         # the sector moved the other way: residual has the wrong sign
    assert classify(1, None, False, 0) == "no_sector_bars"                    # unknown is never "no residual needed"


def bars(closes):
    return DayBars([f"2026-11-{d:02d}" for d in range(1, len(closes) + 1)], list(closes), [1e6] * len(closes))


def test_raw_return_and_sector_residual():
    stock, etf = bars([100.0, 110.0]), bars([50.0, 51.0])
    assert raw_return(stock, "2026-11-02") == pytest.approx(0.10)
    assert raw_return(stock, "2026-11-01") is None and raw_return(stock, "2026-12-01") is None
    assert sector_residual(stock, etf, "2026-11-02") == pytest.approx(0.08)
    assert sector_residual(stock, bars([50.0]), "2026-11-02") is None


def test_sector_map_is_the_frozen_file_and_covers_every_universe_symbol():
    m = load_sector_map()
    assert m["AMD"] == "XLK" and m["XOM"] == "XLE" and len(m) == 501
    from tempo.daybars import load_universe
    from tempo.news_split import UNIVERSE
    assert set(load_universe(UNIVERSE)) <= set(m)
    with pytest.raises(FileNotFoundError):
        load_sector_map(load_sector_map.__globals__["ROOT"] / "nope.csv")


def test_vix_is_the_last_close_before_the_day_and_none_when_unknown(tmp_path):
    f = tmp_path / "VIXCLS.csv"
    f.write_text("observation_date,VIXCLS\n2026-11-12,18.5\n2026-11-13,.\n2026-11-16,20.1\n2026-11-17,22.0\n")
    assert vix_asof(DAY, f) == 20.1                                          # 11-17 itself is not before
    assert vix_asof(date(2026, 11, 14), f) == 18.5                            # a missing value is skipped, not read as zero
    assert vix_asof(date(2026, 11, 1), f) is None and vix_asof(DAY, tmp_path / "none.csv") is None


def test_too_many_failed_news_lookups_fail_the_run():
    assert too_many_failed(2, 10) is False and too_many_failed(3, 10) is True and too_many_failed(0, 0) is False


def hit(symbol, direction, **kw):
    base = {"symbol": symbol, "direction": direction, "day": "2026-11-17", "reaction": 0.07, "close": 50.0, "adv20": 9e6, "vol20": 0.02,
            "headlines": 2, "providers": ["BRFG", "DJ-N"], "sector_etf": "XLK", "residual": 0.055}
    return {**base, **kw}


def test_signals_carry_the_move_the_news_and_the_vix_and_the_fade_also_its_sector_residual(tmp_path):
    from tempo.ledger import Ledger
    from tempo.news_split import record_signals
    ledger = Ledger(tmp_path / "l.jsonl", clock=lambda: at("2026-11-17", 16, 30).timestamp())
    drift = record_signals([hit("AAA", 1)], DRIFT, ledger, None, 21.5)[0]
    assert drift["source"] == DRIFT and drift["direction"] == 1 and drift["event_id"] == "20261117"
    f = drift["features"]
    assert f["headlines"] == 2 and f["providers"] == ["BRFG", "DJ-N"] and f["vix"] == 21.5 and f["vol20"] == 0.02
    assert f["round_trip_cost"] == 0.002 and "residual" not in f
    fade = record_signals([hit("BBB", -1, headlines=0, providers=[])], FADE, ledger, None, None)[0]
    assert fade["features"]["sector_etf"] == "XLK" and fade["features"]["residual"] == 0.055 and fade["features"]["vix"] is None


def test_the_same_symbol_is_not_signalled_twice_within_30_days_per_source_but_may_appear_in_both(tmp_path):
    from tempo.ledger import Ledger
    from tempo.news_split import record_signals
    ledger = Ledger(tmp_path / "l.jsonl", clock=lambda: at("2026-11-17", 16, 30).timestamp())
    assert len(record_signals([hit("AAA", 1)], DRIFT, ledger, None, None)) == 1
    assert record_signals([hit("AAA", 1)], DRIFT, ledger, None, None) == []
    assert len(record_signals([hit("AAA", -1)], FADE, ledger, None, None)) == 1


def test_a_new_event_for_the_same_symbol_is_blocked_for_30_days_then_allowed(tmp_path):
    from tempo.ledger import Ledger
    from tempo.news_split import record_signals
    path = tmp_path / "l.jsonl"
    first = Ledger(path, clock=lambda: at("2026-11-17", 16, 30).timestamp())
    assert len(record_signals([hit("AAA", 1)], DRIFT, first, None, None)) == 1
    soon = Ledger(path, clock=lambda: at("2026-11-20", 16, 30).timestamp())
    assert record_signals([hit("AAA", 1, day="2026-11-20")], DRIFT, soon, None, None) == []
    later = Ledger(path, clock=lambda: at("2026-12-18", 16, 30).timestamp())
    assert len(record_signals([hit("AAA", 1, day="2026-12-18")], DRIFT, later, None, None)) == 1
