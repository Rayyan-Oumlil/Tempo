from dataclasses import replace

from tempo.meanrev_report import Metrics, round_trip_returns, verdict
from tempo.backtest import Trade

PRIMARY = Metrics(sharpe=0.9, bh_sharpe=0.6, cagr_by_slip={0: 0.07, 1: 0.06, 3: 0.04, 5: 0.02, 10: -0.02}, half1_cagr=0.05,
                  half2_cagr=0.06, post2010_cagr=0.05, post2010_sharpe=0.6, t_stat=3.4, max_dd=-0.15, bh_max_dd=-0.55,
                  beat_pct=97.0, exposure=0.11, round_trips=180, avg_trip=0.003, break_even_bps=7.0)
GOOD_VARIANTS = [0.04, 0.03, 0.02, -0.01]


def run(primary=PRIMARY, variants=GOOD_VARIANTS):
    return verdict(primary, variants)


def test_passes_when_every_criterion_holds():
    assert all(ok for _, ok in run())


def test_eight_criteria():
    assert len(run()) == 8


def test_each_criterion_fails_on_its_own():
    cases = [dict(sharpe=0.5), dict(cagr_by_slip={0: 0.07, 1: 0.06, 3: -0.01, 5: -0.02, 10: -0.05}), dict(half1_cagr=-0.01),
             dict(half2_cagr=0.0), dict(post2010_cagr=-0.01), dict(post2010_sharpe=0.39), dict(t_stat=3.0), dict(max_dd=-0.6),
             dict(beat_pct=94.0)]
    for over in cases:
        failed = [text for text, ok in run(replace(PRIMARY, **over)) if not ok]
        assert len(failed) == 1, (over, failed)


def test_fragile_variants_fail_the_last_criterion():
    failed = [text for text, ok in run(variants=[0.04, -0.01, -0.02, -0.03]) if not ok]
    assert failed == ["at least 3 of the 4 variants have net CAGR above 0 at 3 bps per side"]


def test_round_trip_returns_include_costs():
    trades = [Trade(2, "BUY", 100, 10.0, 1.0), Trade(5, "SELL", 100, 11.0, 1.0)]  # paid 1001, received 1099
    assert round_trip_returns(trades) == [(1099.0 - 1001.0) / 1001.0]


def test_an_open_trade_at_the_end_is_not_a_round_trip():
    assert round_trip_returns([Trade(2, "BUY", 100, 10.0, 1.0)]) == []
