import pytest

from tempo.beta_compare import alt_excess, clip_returns, compare, render, robust_beta_before, winsorised
from tempo.data import Bars
from tempo.exec_score import beta_before


def bars(closes, start=0):
    dates = [f"2026-01-{n + 1:02d}" if n < 31 else f"2026-02-{n - 30:02d}" for n in range(start, start + len(closes))]
    return Bars(dates, closes, closes, closes, closes)


def path(returns, base=100.0):
    out = [base]
    for r in returns:
        out.append(out[-1] * (1 + r))
    return out


def test_clipping_pulls_the_extremes_to_the_5th_and_95th_percentile_and_leaves_the_rest():
    r = [i / 1000 for i in range(-50, 50)] + [0.9]                  # one huge outlier
    out = clip_returns(r)
    assert max(out) < 0.9 and max(out) == sorted(r)[int(round(0.95 * 100))]
    assert sum(a != b for a, b in zip(r, out)) <= 12 and out[50] == r[50]


def test_empty_and_short_series_come_through_unchanged():
    short = [0.0, 0.01, -0.01, 0.02, -0.02, 0.01, -0.01, 0.0, 0.9]            # too short for the quantiles to differ from min and max
    assert clip_returns([]) == [] and clip_returns(short) == short


def test_one_earnings_gap_inflates_the_plain_beta_and_the_winsorised_beta_is_lower():
    spy_r = [0.01 * ((-1) ** n) for n in range(70)]
    stock_r = [r * 1.0 for r in spy_r]
    stock_r[40] = 0.60                                              # a gap that has nothing to do with the market
    spy, stock = bars(path(spy_r)), bars(path(stock_r))
    before = "9999"
    plain = beta_before(stock, spy, before)
    robust = robust_beta_before(stock, spy, before)
    assert plain is not None and robust is not None
    assert robust < plain and abs(robust - 1.0) < abs(plain - 1.0)


def test_a_clean_series_keeps_its_beta():
    spy_r = [0.01 * ((-1) ** n) + 0.002 * (n % 3) for n in range(70)]
    stock_r = [1.5 * r for r in spy_r]
    spy, stock = bars(path(spy_r)), bars(path(stock_r))
    plain, robust = beta_before(stock, spy, "9999"), robust_beta_before(stock, spy, "9999")
    assert plain is not None and robust is not None and abs(plain - robust) < 0.15


def test_winsorised_uses_only_the_regression_window_before_the_entry_day():
    spy_r = [0.01 * ((-1) ** n) for n in range(80)]
    spy, stock = bars(path(spy_r)), bars(path(spy_r))
    w = winsorised(stock, spy, spy.dates[70])
    assert len(w.dates) == 61 and w.dates[-1] < spy.dates[70]


def row(**kw):
    base = {"signal_id": "s", "ret": 0.03, "bench_ret": 0.012, "beta": 1.2, "round_trip_cost": 0.002}
    return {**base, **kw}


def test_alt_excess_rescales_the_spy_leg_and_keeps_the_cost():
    assert alt_excess(row(), 1.2) == pytest.approx(0.03 - 0.012 - 0.002)          # same beta: unchanged
    assert alt_excess(row(), 0.6) == pytest.approx(0.03 - 0.006 - 0.002)          # half the beta, half the hedge
    assert alt_excess(row(bench_ret=-0.012), 1.8) == pytest.approx(0.03 + 0.018 - 0.002)
    with pytest.raises(ValueError):
        alt_excess(row(beta=0.0), 1.0)


def test_compare_and_render():
    rows = [{"source": "a", "net_excess": 0.01, "alt_net_excess": 0.02, "beta": 1.0, "beta_alt": 1.5},
            {"source": "a", "net_excess": 0.03, "alt_net_excess": 0.03, "beta": 1.0, "beta_alt": 0.9}]
    s = compare(rows)["a"]
    assert s["n"] == 2 and s["mean"] == pytest.approx(0.02) and s["mean_alt"] == pytest.approx(0.025)
    assert s["beta_shift"] == pytest.approx(0.2) and s["big_shift"] == pytest.approx(0.5)
    assert "report only" in render({"a": s}) and "no exec_v2 scores yet" in render({})
