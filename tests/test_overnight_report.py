from dataclasses import replace

from tempo.overnight_report import Metrics, verdict

SPY = Metrics(sharpe=0.9, bh_sharpe=0.6, cagr_by_slip={0: 0.08, 1: 0.07, 3: 0.04, 5: 0.02, 10: -0.03}, half1_cagr=0.06,
              half2_cagr=0.08, post2010_cagr=0.07, t_stat=3.5, max_dd=-0.2, bh_max_dd=-0.55, break_even_bps=7.0)


def run(spy=None, qqq=None):
    return verdict(spy or SPY, qqq or SPY)


def test_passes_when_every_criterion_holds():
    assert all(ok for _, ok in run())


def test_seven_criteria():
    assert len(run()) == 7


def test_each_spy_criterion_fails_on_its_own():
    cases = [dict(sharpe=0.5), dict(cagr_by_slip={0: 0.08, 1: 0.07, 3: -0.01, 5: -0.02, 10: -0.03}), dict(half1_cagr=-0.01),
             dict(half2_cagr=0.0), dict(post2010_cagr=-0.01), dict(t_stat=3.0), dict(max_dd=-0.6)]
    for over in cases:
        failed = [text for text, ok in run(spy=replace(SPY, **over)) if not ok]
        assert len(failed) >= 1, over


def test_a_failing_qqq_fails_only_the_qqq_criterion():
    failed = [text for text, ok in run(qqq=replace(SPY, half2_cagr=-0.02)) if not ok]
    assert failed == ["QQQ also passes: positive CAGR at 3 bps, in both halves, and Sharpe at or above buy and hold"]


def test_qqq_needs_the_three_checks_not_the_t_statistic():
    # QQQ's t-statistic is not a criterion, only the CAGR at 3 bps, both halves, and Sharpe vs buy and hold
    assert all(ok for _, ok in run(qqq=replace(SPY, t_stat=0.5, max_dd=-0.9)))
