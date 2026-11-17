import pytest

from tempo.history_core import Series, Trade, judge, load_series, trade_excess


def days(n, start_month=1):
    out = []
    for i in range(n):
        out.append(f"2024-{1 + i // 28:02d}-{1 + i % 28:02d}")
    return out


def series(closes, opens=None, dates=None):
    dates = dates or days(len(closes))
    return Series(dates, list(opens or closes), list(closes), [1e6] * len(closes))


def noisy_closes(n):
    out, px = [], 100.0
    for i in range(n):
        px *= 1 + 0.004 * (((i * 7) % 5) - 2)
        out.append(px)
    return out


def test_excess_is_stock_move_minus_beta_times_spy_move_from_open_to_a_later_close():
    closes = noisy_closes(80)
    spy, stock = series(closes), series(closes)          # identical returns before the entry day: raw beta 1, shrunk beta 1
    entry, exit_ = spy.dates[60], spy.dates[65]
    spy.open[60], spy.close[65] = 100.0, 105.0
    stock.open[60], stock.close[65] = 100.0, 110.0
    assert trade_excess(stock, spy, entry, 1, 5) == pytest.approx(0.05)
    assert trade_excess(stock, spy, entry, -1, 5) == pytest.approx(-0.05)
    assert exit_ == spy.dates[65]


def test_no_beta_no_bar_or_no_exit_day_means_no_score_never_a_guess():
    closes = noisy_closes(80)
    spy, stock = series(closes), series(closes)
    assert trade_excess(stock, spy, spy.dates[20], 1, 5) is None          # under 40 prior returns: no beta
    assert trade_excess(stock, spy, spy.dates[78], 1, 5) is None          # the exit day is beyond the data
    assert trade_excess(stock, spy, "1999-01-01", 1, 5) is None           # entry day not a bar
    short = Series(stock.dates[:64], stock.open[:64], stock.close[:64], stock.volume[:64])
    assert trade_excess(short, spy, spy.dates[60], 1, 5) is None          # the stock has no bar on the exit day


def test_load_series_needs_an_open_column(tmp_path):
    good, bad = tmp_path / "a.csv", tmp_path / "b.csv"
    good.write_text("date,open,close,volume\n2024-01-02,10,11,500\n", encoding="utf-8")
    bad.write_text("date,close,volume\n2024-01-02,11,500\n", encoding="utf-8")
    s = load_series(good)
    assert s is not None and s.open == [10.0] and s.close == [11.0] and s.pos == {"2024-01-02": 0}
    assert load_series(bad) is None and load_series(tmp_path / "none.csv") is None


def trades(per_day, gross_for, n_days=60, years=("2023", "2024", "2025")):
    out = []
    for y in years:
        for i in range(n_days):
            day = f"{y}-{1 + i // 28:02d}-{1 + i % 28:02d}"
            for k in range(per_day):
                out.append(Trade(day, f"S{k}", gross_for(y, i)))
    return out


def wobble(i):
    return 0.004 if i % 2 else -0.004


def test_a_clear_edge_in_every_year_is_forward():
    v = judge(trades(2, lambda y, i: 0.03 + wobble(i)), cost=0.002, horizon=5)
    assert v.decision == "FORWARD" and not v.reasons and v.t >= 2.8 and v.events == 360


def test_noise_is_killed():
    v = judge(trades(2, lambda y, i: 0.01 * (1 if i % 2 else -1)), cost=0.002, horizon=5)
    assert v.decision == "KILL" and v.ci[0] <= 0


def test_one_losing_year_blocks_forward_even_if_the_total_is_positive():
    v = judge(trades(2, lambda y, i: (-0.01 if y == "2024" else 0.03) + wobble(i)), cost=0.002, horizon=5)
    assert v.decision == "NOT PROVEN" and any("2024" in r for r in v.reasons)


def test_an_edge_that_dies_at_one_and_a_half_times_the_cost_is_not_forward():
    v = judge(trades(2, lambda y, i: 0.0025 + 0.0001 * (1 if i % 2 else -1)), cost=0.002, horizon=5)
    assert v.decision == "NOT PROVEN" and any("1.5x" in r for r in v.reasons)


def test_too_few_events_is_not_forward():
    v = judge(trades(1, lambda y, i: 0.03 + wobble(i)), cost=0.002, horizon=5)
    assert v.events == 180 and v.decision == "NOT PROVEN" and any("events" in r for r in v.reasons)


def test_a_missing_test_year_is_not_forward():
    v = judge(trades(4, lambda y, i: 0.03 + wobble(i), years=("2023", "2024")), cost=0.002, horizon=5)
    assert v.decision == "NOT PROVEN" and any("no events in 2025" in r for r in v.reasons)


def test_too_few_entry_days_gives_no_verdict_not_a_guess():
    v = judge(trades(10, lambda y, i: 0.05, n_days=5), cost=0.002, horizon=5)
    assert v.decision == "NO VERDICT" and v.mean_net is None


def test_only_test_years_count():
    early = [Trade(f"2019-01-{d:02d}", "X", 0.5) for d in range(1, 28)]
    v = judge(early + trades(2, lambda y, i: 0.01 * (1 if i % 2 else -1)), cost=0.002, horizon=5)
    assert v.decision == "KILL" and v.events == 360
