from dataclasses import replace
from datetime import date

from tempo.pairs_report import Metrics, drop_incomplete_today, usable_pairs, verdict

GOOD = Metrics(sharpe=0.8, stress_sharpe=0.6, beat_pct=97.0, half1=0.7, half2=0.9, variant_sharpes=[0.8, 0.5, 0.6, 0.4, 0.3],
               spy_corr=0.05, pair_win_share=0.8, max_dd=-0.1)


def run(**over):
    return verdict(replace(GOOD, **over))


def test_passes_when_every_criterion_holds():
    assert all(ok for _, ok in run())


def test_each_criterion_fails_on_its_own():
    cases = [dict(sharpe=0.49), dict(stress_sharpe=0.3), dict(beat_pct=94.9), dict(half1=-0.1), dict(half2=0.0),
             dict(variant_sharpes=[0.8, 0.5, -0.1, -0.2, 0.3]), dict(spy_corr=0.31), dict(spy_corr=-0.31),
             dict(pair_win_share=0.59), dict(max_dd=-0.2)]
    for over in cases:
        failed = [text for text, ok in run(**over) if not ok]
        assert len(failed) == 1, (over, failed)


def test_eight_criteria():
    assert len(run()) == 8


def test_drops_pairs_with_less_than_15_years_and_says_why():
    long_series = (["x"] * 4000, [1.0] * 4000)
    short_series = (["x"] * 2000, [1.0] * 2000)
    series = {"AAA": long_series, "BBB": long_series, "KO": long_series, "PEP": short_series}
    kept, dropped = usable_pairs([["AAA", "BBB"], ["KO", "PEP"]], series)
    assert kept == [("AAA", "BBB")]
    assert dropped == [(("KO", "PEP"), "PEP has 2000 days, under the 3780 needed")]


def test_drops_a_bar_dated_today_because_it_is_unfinished():
    dates, closes = drop_incomplete_today(["2026-11-02", "2026-11-03"], [1.0, 2.0], today=date(2026, 11, 3))
    assert dates == ["2026-11-02"] and closes == [1.0]
    dates, closes = drop_incomplete_today(["2026-11-02"], [1.0], today=date(2026, 11, 3))
    assert dates == ["2026-11-02"]
