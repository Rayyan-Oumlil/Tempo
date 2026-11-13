"""exec_v2 scoring: enter at the price the runner can get (09:40 ET bar), exit at the exit-window price (15:45 ET bar,
close minus 15 minutes on early-close days), and subtract beta times the market move instead of the whole market move."""
import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from tempo.data import Bars
from tempo.exec_score import METHOD, Intraday, beta_before, exit_hhmm, score_signal_exec
from tempo.ledger import Ledger

ET = ZoneInfo("America/New_York")


def daily(dates, closes):
    return Bars(dates, closes, closes, closes, closes)


def trading_dates(n, start=date(2026, 11, 3)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def intraday(entries: dict[str, float], exits: dict[str, float]) -> Intraday:
    opens = {(day, "09:40"): px for day, px in entries.items()}
    opens.update({(day, "15:45"): px for day, px in exits.items()})
    return Intraday(opens)


SIGNAL = {"signal_id": "s:AAA:e", "source": "s", "symbol": "AAA", "direction": 1, "date_et": "2026-11-03", "features": {}}


def flat_daily(dates):
    return daily(dates, [100.0] * len(dates))


def test_exit_bar_is_fifteen_minutes_before_the_close():
    assert exit_hhmm(date(2026, 11, 12)) == "15:45"
    assert exit_hhmm(date(2026, 11, 27)) == "12:45"      # early close 13:00 the day after Thanksgiving


def test_beta_is_one_for_a_stock_that_moves_with_the_market_after_shrinkage():
    dates = trading_dates(70)
    market = [100.0 * (1 + 0.01 * ((i % 5) - 2)) ** 1 for i in range(70)]
    b = beta_before(daily(dates, market), daily(dates, market), before=dates[-1])
    assert b == pytest.approx(1.0)


def test_beta_of_a_double_mover_is_shrunk_toward_one():
    dates = trading_dates(70)
    rets = [0.01 if i % 2 else -0.008 for i in range(70)]
    mkt, stk = [100.0], [100.0]
    for r in rets[1:]:
        mkt.append(mkt[-1] * (1 + r))
        stk.append(stk[-1] * (1 + 2 * r))
    b = beta_before(daily(dates, stk), daily(dates, mkt), before=dates[-1])
    assert b == pytest.approx(2 / 3 * 2.0 + 1 / 3, rel=0.02)   # raw about 2, shrunk to about 1.67


def test_beta_never_looks_at_the_entry_day_or_later():
    dates = trading_dates(70)
    mkt = [100.0 * 1.001 ** i * (1 + 0.004 * ((i * 7) % 5 - 2)) for i in range(70)]
    stk = list(mkt)
    spiked = stk[:-1] + [stk[-1] * 3.0]                  # an absurd move ON the day we pass as `before`
    assert beta_before(daily(dates, spiked), daily(dates, mkt), before=dates[-1]) == pytest.approx(
        beta_before(daily(dates, stk), daily(dates, mkt), before=dates[-1]))


def test_too_little_history_means_no_beta_and_no_score():
    dates = trading_dates(30)                                       # 29 returns: under the 40 required
    moving = [100.0 * (1 + 0.004 * ((i * 7) % 5 - 2)) for i in range(30)]
    assert beta_before(daily(dates, moving), daily(dates, moving), before=dates[-1] + "x") is None   # varying, so only the count blocks it
    assert beta_before(flat_daily(dates), flat_daily(dates), before=dates[-1]) is None               # a flat market has no beta either


def history_then_event(horizon):
    """70 days of history (stock = market, beta 1 after shrinkage), then an entry day and `horizon-1` more."""
    hist = [f"2026-08-{d:02d}" for d in range(3, 31) if datetime(2026, 8, d).weekday() < 5]          # 20 days
    hist += [f"2026-09-{d:02d}" for d in range(1, 31) if datetime(2026, 9, d).weekday() < 5]          # 22 days
    hist += [f"2026-10-{d:02d}" for d in range(1, 32) if datetime(2026, 10, d).weekday() < 5]         # 22 days
    return hist


def make_inputs(direction=1, stock=(100.0, 103.0), spy=(100.0, 101.0), horizon=1, cost=0.002):
    hist = history_then_event(horizon)
    event = ["2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06", "2026-11-09"]
    dates = hist + event
    mkt = [100.0 * (1 + 0.004 * ((i * 7) % 5 - 2)) for i in range(len(dates))]
    d_stock, d_spy = daily(dates, list(mkt)), daily(dates, list(mkt))
    entry_day, exit_day = "2026-11-04", event[1 + horizon - 1]
    i_stock = intraday({entry_day: stock[0]}, {exit_day: stock[1]})
    i_spy = intraday({entry_day: spy[0]}, {exit_day: spy[1]})
    sig = {**SIGNAL, "direction": direction, "features": {"round_trip_cost": cost}}
    return sig, d_stock, d_spy, i_stock, i_spy


def test_long_score_uses_the_executable_prices_and_subtracts_beta_times_market():
    sig, ds, dm, is_, im = make_inputs(stock=(100.0, 103.0), spy=(100.0, 101.0))
    out = score_signal_exec(sig, ds, dm, is_, im, horizon=1)
    assert out["method"] == METHOD and out["beta"] == pytest.approx(1.0)
    assert out["entry_px"] == 100.0 and out["exit_px"] == 103.0
    assert out["ret"] == pytest.approx(0.03)
    assert out["bench_ret"] == pytest.approx(0.01)
    assert out["excess"] == pytest.approx(0.02)
    assert out["net_excess"] == pytest.approx(0.018)         # minus the 20 bps cost the signal declares


def test_short_score_flips_both_the_stock_and_the_hedge():
    sig, ds, dm, is_, im = make_inputs(direction=-1, stock=(100.0, 103.0), spy=(100.0, 101.0))
    out = score_signal_exec(sig, ds, dm, is_, im, horizon=1)
    assert out["ret"] == pytest.approx(-0.03) and out["bench_ret"] == pytest.approx(-0.01)
    assert out["net_excess"] == pytest.approx(-0.02 - 0.002)


def test_entry_is_the_first_day_strictly_after_the_signal_date():
    sig, ds, dm, is_, im = make_inputs()
    sig = {**sig, "date_et": "2026-11-04"}      # signal on the 4th: entry is the 5th, which has no intraday bars here
    assert score_signal_exec(sig, ds, dm, is_, im, horizon=1) is None


def test_a_missing_intraday_bar_means_waiting_not_a_guess():
    sig, ds, dm, is_, im = make_inputs()
    assert score_signal_exec(sig, ds, dm, Intraday({}), im, horizon=1) is None
    assert score_signal_exec(sig, ds, dm, is_, Intraday({}), horizon=1) is None


def test_not_enough_days_after_entry_means_waiting():
    sig, ds, dm, is_, im = make_inputs(horizon=1)
    assert score_signal_exec(sig, ds, dm, is_, im, horizon=5) is None            # entry the 4th, the 5th day is not here yet
    assert score_signal_exec({**sig, "date_et": "2026-11-09"}, ds, dm, is_, im, horizon=1) is None   # no day after the 9th


def test_multi_day_horizon_exits_on_the_horizon_th_day_counting_entry_as_day_one():
    sig, ds, dm, is_, im = make_inputs(stock=(100.0, 110.0), spy=(100.0, 102.0), horizon=3)
    out = score_signal_exec(sig, ds, dm, is_, im, horizon=3)
    assert out["exit_date"] == "2026-11-06" and out["entry_date"] == "2026-11-04"
    assert out["ret"] == pytest.approx(0.10)


def test_the_score_carries_no_nan():
    sig, ds, dm, is_, im = make_inputs()
    out = score_signal_exec(sig, ds, dm, is_, im, horizon=1)
    assert all(not (isinstance(v, float) and math.isnan(v)) for v in out.values())


def test_ledger_keeps_legacy_and_exec_scores_apart(tmp_path):
    ledger = Ledger(tmp_path / "l.jsonl", clock=lambda: datetime(2026, 11, 3, 20, 0, tzinfo=ET).timestamp())
    ledger.record_signal(source="s", symbol="AAA", direction=1, event_id="e")
    legacy = {"signal_id": "s:AAA:e", "source": "s", "symbol": "AAA", "horizon": 1, "ret": 0.0, "bench_ret": 0.0,
              "excess": 0.0, "net_excess": 0.0, "round_trip_cost": 0.0, "entry_date": "d", "exit_date": "d"}
    ledger.journal.append("score", **legacy)                      # a row written before the amendment: no method field
    assert ledger.scores() == []                                  # legacy rows never count toward a verdict
    assert len(ledger.scores(method=None)) == 1                   # but stay readable
    from tempo.ledger import unscored
    assert [(s["signal_id"], h) for s, h in unscored(ledger, (1,))] == [("s:AAA:e", 1)]   # legacy does not mark it done
    new = {**legacy, "method": METHOD, "net_excess": 0.01}
    assert ledger.record_scores([new]) == 1
    assert ledger.record_scores([new]) == 0                       # same method, same signal, same horizon: once
    assert [r["net_excess"] for r in ledger.scores()] == [0.01]
    assert unscored(ledger, (1,)) == []


def test_a_high_beta_stock_is_hedged_with_its_own_beta_not_with_one():
    sig, ds, dm, is_, im = make_inputs(stock=(100.0, 103.0), spy=(100.0, 101.0))
    mkt = dm.close
    rets = [0.0] + [mkt[i] / mkt[i - 1] - 1 for i in range(1, len(mkt))]
    stock_closes = [100.0]
    for r in rets[1:]:
        stock_closes.append(stock_closes[-1] * (1 + 2 * r))
    out = score_signal_exec(sig, daily(ds.dates, stock_closes), dm, is_, im, horizon=1)
    assert out["beta"] == pytest.approx(2 / 3 * 2.0 + 1 / 3, rel=0.05)
    assert out["bench_ret"] == pytest.approx(out["beta"] * 0.01)              # not 0.01: the hedge is scaled
    assert out["excess"] == pytest.approx(0.03 - out["beta"] * 0.01)


def test_a_signal_with_a_short_price_history_stays_unscored():
    sig, ds, dm, is_, im = make_inputs()
    keep = 30
    short_d = Bars(ds.dates[-keep:], ds.close[-keep:], ds.close[-keep:], ds.close[-keep:], ds.close[-keep:])
    short_m = Bars(dm.dates[-keep:], dm.close[-keep:], dm.close[-keep:], dm.close[-keep:], dm.close[-keep:])
    assert score_signal_exec(sig, short_d, short_m, is_, im, horizon=1) is None
