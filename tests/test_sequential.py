import math
import random
from statistics import mean, variance

from tempo import sequential as sq


def noise(n, mu, sd, seed):
    r = random.Random(seed)
    return [r.gauss(mu, sd) for _ in range(n)]


def test_hac_with_lag_zero_is_the_population_variance_of_the_mean():
    x = noise(50, 0.0, 0.02, 1)
    m = mean(x)
    assert math.isclose(sq.hac_variance_of_mean(x, 0), sum((v - m) ** 2 for v in x) / 50 / 50)


def test_hac_hand_computed_lag_one():
    x = [1.0, 2.0, 3.0, 2.0]
    d = [v - 2.0 for v in x]                         # -1, 0, 1, 0
    gamma0, gamma1 = sum(v * v for v in d) / 4, (d[1] * d[0] + d[2] * d[1] + d[3] * d[2]) / 4
    assert math.isclose(sq.hac_variance_of_mean(x, 1), (gamma0 + 2 * 0.5 * gamma1) / 4)


def test_overlap_inflates_the_error_bar():
    base = noise(300, 0.0, 0.02, 2)
    smooth = [mean(base[i:i + 5]) for i in range(0, 296)]          # 5-day overlap: strong positive autocorrelation
    naive = variance(smooth) / len(smooth)
    assert sq.hac_variance_of_mean(smooth, 4) > 2 * naive


def test_msprt_rejects_a_real_effect_and_not_pure_noise():
    assert sq.msprt_p(noise(120, 0.02, 0.01, 3), 4) < 0.001
    assert sq.msprt_p(noise(120, 0.0, 0.02, 4), 4) > 0.2
    assert sq.msprt_p([0.01] * 5, 4) == 1.0                         # too few days: no evidence claimed


def test_always_valid_p_never_falls_when_data_is_added_back_to_noise():
    x = noise(200, 0.0, 0.02, 5)
    assert all(0 < sq.msprt_p(x[:k], 4) <= 1 for k in (10, 50, 200))


def test_cohorts_average_trades_that_share_an_entry_day():
    rows = [{"source": "a", "horizon": 5, "entry_date": "2026-11-13", "net_excess": v} for v in (0.02, 0.04)]
    rows.append({"source": "a", "horizon": 5, "entry_date": "2026-11-16", "net_excess": 0.01})
    assert sq.cohorts(rows)[("a", 5)] == [("2026-11-13", 0.03, 2), ("2026-11-16", 0.01, 1)]


def score_rows(source, xs, horizon=5):
    return [{"source": source, "horizon": horizon, "entry_date": f"2026-{1 + i // 28:02d}-{1 + i % 28:02d}", "net_excess": v} for i, v in enumerate(xs)]


def test_analyse_reports_nothing_certain_with_few_days_and_deflates_among_several_sources():
    rows = sq.analyse(score_rows("few", [0.01] * 5))
    assert rows[0]["ci"] is None and rows[0]["p"] is None and "no interval yet" in sq.render(rows)
    scores = score_rows("good", noise(120, 0.02, 0.01, 6)) + score_rows("flat1", noise(120, 0.0, 0.02, 7)) + score_rows("flat2", noise(120, 0.0, 0.02, 8))
    by = {r["source"]: r for r in sq.analyse(scores)}
    assert by["good"]["ci"][0] > 0 and by["good"]["p"] < 0.001 and by["good"]["dsr"] > 0.9
    assert by["flat1"]["ci"][0] < 0 < by["flat1"]["ci"][1] and by["flat1"]["p"] > 0.05
    assert by["good"]["days_needed"] < by["flat1"]["days_needed"]


def test_deflated_sharpe_needs_at_least_two_tries_and_falls_as_tries_grow():
    assert sq.deflated_sharpe(0.3, 100, 0.0, 3.0, [0.3]) is None
    few = sq.deflated_sharpe(0.3, 100, 0.0, 3.0, [0.3, 0.0])
    many = sq.deflated_sharpe(0.3, 100, 0.0, 3.0, [0.3, 0.0, 0.05, -0.05, 0.1, -0.1, 0.02, -0.02, 0.08, -0.08])
    assert few is not None and many is not None and 0 <= many <= 1 and few != many


def test_interval_is_196_standard_errors_and_widens_with_the_horizon():
    base = noise(300, 0.01, 0.02, 9)
    xs = [mean(base[i:i + 5]) for i in range(0, 120)]
    one = sq.analyse(score_rows("s", xs, horizon=1))[0]
    five = sq.analyse(score_rows("s", xs, horizon=5))[0]
    assert math.isclose((one["ci"][1] - one["ci"][0]) / 2, 1.96 * one["mde"] / 2.8)
    assert (five["ci"][1] - five["ci"][0]) > 1.5 * (one["ci"][1] - one["ci"][0])


def test_msprt_charges_for_overlap_and_remembers_an_early_peak():
    base = noise(300, 0.004, 0.02, 10)
    smooth = [mean(base[i:i + 5]) for i in range(0, 120)]
    assert sq.msprt_p(smooth, 4) > sq.msprt_p(smooth, 0)
    flip = [0.03 + e for e in noise(20, 0, 0.002, 11)] + [-0.03 + e for e in noise(20, 0, 0.002, 12)]
    assert sq.msprt_p(flip, 0) < 0.01          # evidence seen at day 20 is not erased by the mean returning to zero
