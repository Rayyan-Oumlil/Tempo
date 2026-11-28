import datetime as dt

import numpy as np
import pandas as pd
import pytest

from tempo import history_y as y
from tempo import x4_signal as s


def closes(vals):
    return pd.Series(vals, index=pd.date_range("2022-01-01", periods=len(vals)), dtype="float64")


def test_signal_matches_the_frozen_backtest_weight():
    rng = np.random.default_rng(3)
    c = closes(100 * np.cumprod(1 + rng.normal(0.002, 0.03, 400)))
    sig = s.compute_signal(c)
    assert sig.target_weight == pytest.approx(y.x4_weights(c.rename("BTC-USD")).iloc[-1, 0])
    assert sig.signal_on == (c.iloc[-1] > c.rolling(100).mean().iloc[-1])


def test_off_signal_means_zero_weight():
    c = closes(np.r_[np.linspace(100, 200, 200), np.linspace(200, 80, 100)])
    sig = s.compute_signal(c)
    assert not sig.signal_on and sig.target_weight == 0.0


def test_too_little_history_fails_loudly():
    with pytest.raises(ValueError):
        s.compute_signal(closes(np.full(50, 100.0)))


TODAY = dt.date(2026, 11, 28)


def ts(day, hour=0):
    return int(dt.datetime(2026, 11, day, hour, tzinfo=dt.timezone.utc).timestamp())


def daily(rows):
    return {"timestamp": [ts(d) for d, _ in rows], "indicators": {"adjclose": [{"adjclose": [c for _, c in rows]}]}}


def hourly(rows):
    return lambda: {"timestamp": [ts(d, h) for d, h, _ in rows], "indicators": {"quote": [{"close": [c for _, _, c in rows]}]}}


def no_hourly():
    raise AssertionError("hourly bars must not be requested")


def test_complete_daily_series_never_asks_for_hourly_and_drops_the_open_day():
    c = s.parse_closes(daily([(26, 100.0), (27, 101.0), (28, 999.0)]), no_hourly, TODAY)
    assert list(c) == [100.0, 101.0] and c.attrs["last_close_source"] == "yahoo daily"


@pytest.mark.parametrize("rows", [[(26, 100.0), (27, None), (28, 999.0)], [(26, 100.0), (28, 999.0)]])
def test_empty_or_absent_yesterday_comes_from_the_2300_utc_hourly_bar(rows):
    c = s.parse_closes(daily(rows), hourly([(27, 22, 7.0), (27, 23, 101.5), (28, 0, 8.0)]), TODAY)
    assert c.index[-1] == pd.Timestamp("2026-11-27") and c.iloc[-1] == 101.5 and len(c) == 2
    assert c.attrs["last_close_source"] == "yahoo 23:00 UTC hourly"


@pytest.mark.parametrize("bars", [[(27, 22, 7.0)], [(27, 23, None)], [(26, 23, 7.0)]])
def test_without_the_final_hourly_bar_the_series_stays_stale(bars):
    c = s.parse_closes(daily([(26, 100.0), (27, None)]), hourly(bars), TODAY)
    assert c.index[-1] == pd.Timestamp("2026-11-26")


def test_signal_and_printout_carry_the_close_source():
    c = closes(np.linspace(100, 200, 300))
    assert s.compute_signal(c).close_source == "yahoo daily"
    c.attrs["last_close_source"] = "yahoo 23:00 UTC hourly"
    sig = s.compute_signal(c)
    assert sig.close_source == "yahoo 23:00 UTC hourly" and "23:00 UTC hourly" in s.describe(sig, None)


def test_describe_prints_notional_and_states_no_order():
    rng = np.random.default_rng(4)
    sig = s.compute_signal(closes(100 * np.cumprod(1 + rng.normal(0.003, 0.02, 300))))
    text = s.describe(sig, 10_000)
    assert "PRINT ONLY" in text and "BTC" in text
