from dataclasses import replace

from tempo.tactical_report import Metrics, verdict

GOOD = Metrics(sharpe=0.9, ew_sharpe=0.6, sixty_sharpe=0.7, cagr_by_slip={0: 0.08, 1: 0.075, 3: 0.07, 5: 0.065, 10: 0.05},
               sixty_cagr=0.07, max_dd=-0.15, spy_max_dd=-0.55, ew_max_dd=-0.40, half1_sharpe=0.8, half2_sharpe=0.9, t_stat=3.5,
               beat_pct=97.0, variant_sharpes=[0.9, 0.8, 0.7, 0.55], cash_share=0.2)


def run(**over):
    return verdict(replace(GOOD, **over))


def test_passes_when_every_criterion_holds():
    assert all(ok for _, ok in run())


def test_eight_criteria():
    assert len(run()) == 8


def test_each_criterion_fails_on_its_own():
    cases = [dict(sharpe=0.65), dict(sharpe=0.55, ew_sharpe=0.5, sixty_sharpe=0.7),
             dict(max_dd=-0.45), dict(max_dd=-0.6),
             dict(cagr_by_slip={0: 0.08, 1: 0.065, 3: 0.06, 5: 0.055, 10: 0.04}),
             dict(half1_sharpe=-0.1), dict(half2_sharpe=0.0), dict(t_stat=3.0),
             dict(cagr_by_slip={0: 0.08, 1: 0.075, 3: 0.07, 5: -0.01, 10: -0.05}),
             dict(beat_pct=94.9), dict(variant_sharpes=[0.9, 0.5, 0.4, 0.3])]
    for over in cases:
        failed = [text for text, ok in run(**over) if not ok]
        assert len(failed) >= 1, over


def test_beating_one_benchmark_but_not_the_other_fails_the_first_criterion():
    failed = [text for text, ok in run(ew_sharpe=0.5, sixty_sharpe=0.95) if not ok]
    assert failed == ["primary net Sharpe at 1 bp at or above BOTH the always-held equal-weight benchmark and the 60/40"]


def test_drawdown_must_beat_both_benchmarks():
    failed = [text for text, ok in run(max_dd=-0.45, spy_max_dd=-0.55, ew_max_dd=-0.40) if not ok]
    assert failed == ["primary max drawdown shallower than BOTH SPY buy and hold and the always-held equal-weight benchmark"]
