from datetime import date, timedelta

import pytest

from tempo.history_shortvol import (Ohlc, all_symbols, leg_verdicts, load_ohlc, members_on, outcome, parse_members, pick_day, render, save_ohlc,
                                    simulate, weekdays_between)

DAYS: list[str] = []
_d = date(2020, 1, 2)
while len(DAYS) < 80:
    if _d.weekday() < 5:
        DAYS.append(_d.isoformat())
    _d += timedelta(days=1)


def flat(price: float = 100.0, volume: float = 1e6) -> Ohlc:
    return Ohlc(DAYS, [price] * len(DAYS), [price] * len(DAYS), [volume] * len(DAYS))


def test_members_come_from_the_latest_row_on_or_before_the_day_and_an_earlier_day_is_an_error():
    hist = parse_members('date,tickers\n2020-01-01,"AAA,BBB"\n2020-03-01,"AAA,CCC"\n')
    assert members_on(hist, "2020-02-15") == {"AAA", "BBB"}
    assert members_on(hist, "2020-03-01") == {"AAA", "CCC"} and members_on(hist, "2021-01-01") == {"AAA", "CCC"}
    with pytest.raises(ValueError):
        members_on(hist, "2019-12-31")


@pytest.mark.parametrize("text", ["", "a,b\n1,2\n", 'date,tickers\n2020-03-01,"A"\n2020-01-01,"B"\n'])
def test_a_bad_membership_file_is_refused(text):
    with pytest.raises(ValueError):
        parse_members(text)


def test_all_symbols_covers_everyone_in_the_window_including_those_who_left():
    hist = parse_members('date,tickers\n2019-01-01,"OLD,KEEP"\n2020-02-01,"KEEP,NEW"\n2021-01-01,"LATE"\n')
    assert all_symbols(hist, "2020-01-01", "2020-12-31") == ["KEEP", "NEW", "OLD"]


def test_outcome_enters_at_the_next_open_exits_at_the_close_five_sessions_on_and_subtracts_spy():
    spy = Ohlc(DAYS, [100.0] * 80, [100.0 + n for n in range(80)], [1e9] * 80)
    spy = Ohlc(DAYS, [100.0 + n for n in range(80)], [100.0 + n for n in range(80)], [1e9] * 80)
    stock = Ohlc(DAYS, [50.0 + n for n in range(80)], [50.0 + 2 * n for n in range(80)], [1e6] * 80)
    i = 30                                         # signal day; entry = session 31 open; exit = session 35 close
    long_ = outcome(stock, spy, DAYS[i], 1)
    assert long_ == pytest.approx((120.0 / 81.0 - 1) - (135.0 / 131.0 - 1))
    assert outcome(stock, spy, DAYS[i], -1) == pytest.approx(-long_)


def test_outcome_is_none_without_a_bar_or_enough_future():
    spy = flat()
    keep = [n for n in range(80) if n != 35]
    gappy = Ohlc([DAYS[n] for n in keep], [10.0] * 79, [10.0] * 79, [1e6] * 79)
    assert outcome(gappy, spy, DAYS[30], 1) is None        # the exit session has no stock bar
    assert outcome(gappy, spy, DAYS[77], 1) is None        # fewer than 5 sessions left
    assert outcome(gappy, spy, "1999-01-01", 1) is None
    assert outcome(Ohlc(DAYS, [0.0] * 80, [1.0] * 80, [1e6] * 80), spy, DAYS[30], 1) is None


def universe(n: int = 120) -> list[str]:
    return [f"S{i:03d}" for i in range(n)]


def finra_day(extreme_high: str, extreme_low: str, syms: list[str]) -> dict[str, tuple[float, float]]:
    out = {s: (500_000.0 + 1000 * (i % 7), 1_000_000.0) for i, s in enumerate(syms)}      # ratio 0.50 to 0.506
    out[extreme_high] = (950_000.0, 1_000_000.0)
    out[extreme_low] = (50_000.0, 1_000_000.0)
    return out


def test_pick_day_takes_the_most_extreme_liquid_names_and_counts_what_it_skipped():
    syms = universe()
    past = [{s: (500_000.0 + 1000 * ((i + k) % 7), 1_000_000.0) for i, s in enumerate(syms)} for k in range(20)]
    today = finra_day("S010", "S011", syms)
    books = {s: flat() for s in syms}
    books["S010"] = None                                    # the top short candidate has no bars: skipped and counted
    picks, counts = pick_day(DAYS[40], today, past, frozenset(syms), books.get, n_each=3)
    shorts = [p for p in picks if p[1] == -1]
    longs = [p for p in picks if p[1] == 1]
    assert counts["no_bars"] == 1 and len(shorts) == 3 and len(longs) == 3
    assert "S010" not in [s for s, _, _ in shorts] and longs[0][0] == "S011" and longs[0][2] < 0 < shorts[0][2]


def test_an_illiquid_candidate_is_skipped_and_counted():
    syms = universe()
    past = [{s: (500_000.0 + 1000 * ((i + k) % 7), 1_000_000.0) for i, s in enumerate(syms)} for k in range(20)]
    today = finra_day("S010", "S011", syms)
    books = {s: flat() for s in syms}
    books["S011"] = flat(volume=10.0)                       # ADV about 1,000 USD: fails the live liquidity filter
    picks, counts = pick_day(DAYS[40], today, past, frozenset(syms), books.get, n_each=2)
    assert counts["illiquid"] == 1 and "S011" not in [s for s, d, _ in picks]


def test_too_few_names_for_a_z_score_cross_section_give_no_pick():
    syms = universe(20)                                     # the live rule needs at least 100 scorable names
    past = [finra_day("S001", "S002", syms)] * 20
    assert pick_day(DAYS[40], finra_day("S001", "S002", syms), past, frozenset(syms), lambda s: flat())[0] == []


def _series():
    syms = universe()
    base = lambda k: {s: (500_000.0 + 1000 * ((i + k) % 7), 1_000_000.0) for i, s in enumerate(syms)}      # noqa: E731
    files = {d: base(n) for n, d in enumerate(DAYS)}
    files[DAYS[40]] = finra_day("S010", "S011", syms)
    spy = Ohlc(DAYS, [100.0] * 80, [100.0] * 80, [1e9] * 80)
    stock = {s: flat() for s in syms}
    # the heavily shorted name falls after the signal, the barely shorted one rises: both legs earn
    stock["S010"] = Ohlc(DAYS, [100.0] * 80, [100.0] * 36 + [90.0] * 44, [1e6] * 80)
    stock["S011"] = Ohlc(DAYS, [100.0] * 80, [100.0] * 36 + [110.0] * 44, [1e6] * 80)
    hist = parse_members(f'date,tickers\n2019-01-01,"{",".join(syms)}"\n')
    return files, hist, stock, spy


def test_simulate_runs_the_live_rule_over_history_and_both_legs_earn_when_the_extremes_revert():
    files, hist, stock, spy = _series()
    rows, totals = simulate(DAYS, files.get, hist, stock.get, spy, DAYS[0], DAYS[-1])
    day40 = [r for r in rows if r["day"] == DAYS[40]]
    assert {(r["symbol"], r["direction"]) for r in day40 if r["symbol"] in ("S010", "S011")} == {("S010", -1), ("S011", 1)}
    assert [round(r["drift"], 3) for r in day40 if r["symbol"] == "S010"] == [0.1] and [round(r["drift"], 3) for r in day40 if r["symbol"] == "S011"] == [0.1]
    assert totals["days"] == 80 - 20 and totals["days_skipped"] == 20           # the first 20 sessions only build the baseline


def test_a_missing_file_breaks_the_baseline_instead_of_being_bridged():
    files, hist, stock, spy = _series()
    del files[DAYS[50]]
    rows, totals = simulate(DAYS, files.get, hist, stock.get, spy, DAYS[0], DAYS[-1])
    days_with_rows = {r["day"] for r in rows}
    assert DAYS[50] not in days_with_rows and not any(DAYS[51] <= d <= DAYS[70] for d in days_with_rows)    # 20 sessions to rebuild
    assert DAYS[71] in days_with_rows


def test_verdict_kills_a_leg_below_cost_and_drops_the_source_only_when_both_die():
    def rows(long_drift, short_drift):
        return ([{"day": f"d{n:03d}", "direction": 1, "drift": long_drift} for n in range(40)]
                + [{"day": f"d{n:03d}", "direction": -1, "drift": short_drift} for n in range(40)])
    totals = {"days": 40, "days_skipped": 0, "members": 100, "no_bars": 3, "illiquid": 2}
    both = leg_verdicts(rows(0.0005, 0.0005))
    assert both["long"][4].startswith("KILL") and both["short"][4].startswith("KILL")
    assert "drop short_volume_v1" in render(rows(0.0005, 0.0005), totals)
    one = render(rows(0.0005, 0.02), totals)
    assert "not dropped" in one and "KILL" in one and "no bars (delisted or unknown to IBKR): 3" in one
    assert leg_verdicts(rows(0.02, 0.02))["long"][4].startswith("not killed")
    split = leg_verdicts(rows(0.0005, 0.02))                  # only the long leg is below cost
    assert split["long"][4].startswith("KILL") and split["short"][4].startswith("not killed")


def test_rows_without_a_forward_bar_are_ignored_and_too_few_days_give_no_verdict():
    assert leg_verdicts([{"day": "d1", "direction": 1, "drift": None}])["long"][2] is None
    assert leg_verdicts([{"day": "d1", "direction": 1, "drift": 0.5}])["long"][4].startswith("too few days")


def test_ohlc_round_trips_through_the_cache_and_weekdays_are_counted(tmp_path):
    bars = Ohlc(["2020-01-02", "2020-01-03"], [1.0, 2.0], [1.5, 2.5], [10.0, 20.0])
    save_ohlc(tmp_path / "x" / "A.csv", bars)
    assert load_ohlc(tmp_path / "x" / "A.csv") == bars and load_ohlc(tmp_path / "none.csv") is None
    assert weekdays_between(date(2020, 1, 1), date(2020, 1, 7)) == 5            # Wed Thu Fri Mon Tue
