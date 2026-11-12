import random

import pytest

from tempo.autopsy import (MIN_CELL, Trade, bonferroni_t, build_trades, candidate_patterns, cause, load_vix, pattern_cells,
                           trade_summary, vix_regime)


def trade(paper=-0.02, ledger=0.01, bench=0.0, net=0.008, slip=0.0, d=1):
    return Trade("claude_earnings_v1:AAA:e", "claude_earnings_v1", "AAA", d, paper, slip, ledger, bench, net)


@pytest.mark.parametrize("t, expected", [
    (trade(paper=0.02, ledger=0.01), "win"),
    (trade(paper=0.02, ledger=-0.01), "lucky win"),
    (trade(paper=-0.02, ledger=-0.03, bench=0.0, net=-0.03), "wrong idea"),
    (trade(paper=-0.02, ledger=-0.01, bench=-0.04, net=0.03), "market move"),
    (trade(paper=-0.02, ledger=0.01, slip=0.005), "execution"),
    (trade(paper=-0.02, ledger=0.01, slip=0.0005), "timing"),
    (trade(paper=0.0, ledger=0.001, net=0.0), "noise"),
    (Trade("s:A:e", "claude_earnings_v1", "A", 1, -0.01, 0.0, None, None, None), "unscored"),
])
def test_each_loss_gets_exactly_one_cause(t, expected):
    t = t if expected != "noise" else trade(paper=-0.001, ledger=0.001)
    assert cause(t) == expected


def state_entry(sid, d, fill, ref, exit_fill, symbol="AAA"):
    return {"status": "exited", "direction": d, "fill_price": fill, "ref_price": ref, "exit_fill_price": exit_fill, "symbol": symbol}


def test_trades_are_joined_to_the_ledger_score_at_the_sources_horizon():
    state = {"claude_earnings_v1:AAA:e": state_entry("x", 1, 100.0, 99.0, 103.0),
             "insider_cluster_v1:BBB:e": state_entry("x", -1, 50.0, 50.0, 49.0, "BBB"),
             "claude_earnings_v1:CCC:e": {"status": "entered", "direction": 1},                      # still open: ignored
             "claude_earnings_v1:DDD:e": {"status": "exited", "direction": 1, "symbol": "DDD", "exit_fill_price": None}}   # nothing to close
    scores = [{"signal_id": "claude_earnings_v1:AAA:e", "horizon": 5, "ret": 0.02, "bench_ret": 0.001, "net_excess": 0.018},
              {"signal_id": "claude_earnings_v1:AAA:e", "horizon": 1, "ret": 9.9, "bench_ret": 0, "net_excess": 9.9},     # wrong horizon
              {"signal_id": "insider_cluster_v1:BBB:e", "horizon": 21, "ret": 0.03, "bench_ret": 0.0, "net_excess": 0.028}]
    a, b = build_trades(state, scores)
    assert a.paper_ret == pytest.approx(0.03) and a.entry_slip == pytest.approx(100 / 99 - 1) and a.ledger_ret == 0.02
    assert b.paper_ret == pytest.approx(0.02) and b.ledger_ret == 0.03             # a short that fell 2% earned 2%
    assert len(build_trades(state, [])) == 2 and build_trades(state, [])[0].ledger_ret is None


def test_short_entry_slippage_is_positive_when_the_fill_is_worse():
    worse = build_trades({"claude_earnings_v1:A:e": state_entry("x", -1, 99.0, 100.0, 98.0)}, [])[0]    # sold lower than planned
    better = build_trades({"claude_earnings_v1:A:e": state_entry("x", -1, 101.0, 100.0, 98.0)}, [])[0]
    assert worse.entry_slip == pytest.approx(0.01) and better.entry_slip == pytest.approx(-0.01)


def test_summary_averages_and_counts_causes():
    s = trade_summary([trade(paper=0.02, ledger=0.01), trade(paper=-0.02, ledger=-0.03, net=-0.03)])["claude_earnings_v1"]
    assert s["n"] == 2 and s["win_rate"] == 0.5 and s["mean_paper"] == pytest.approx(0.0)
    assert s["mean_gap"] == pytest.approx(((0.02 - 0.01) + (-0.02 + 0.03)) / 2) and s["causes"] == {"win": 1, "wrong idea": 1}
    assert trade_summary([]) == {}


def test_vix_regime_compares_with_the_trailing_median_and_needs_history(tmp_path):
    vix = {f"2026-{m:02d}-{d:02d}": 15.0 for m in range(1, 9) for d in range(1, 29)}
    vix["2026-09-01"] = 30.0
    vix["2026-09-02"] = 10.0
    assert vix_regime(vix, "2026-09-01") == "high" and vix_regime(vix, "2026-09-02") == "low"
    assert vix_regime(vix, "2026-09-05") is None                                   # no reading that day
    assert vix_regime({"2026-01-01": 20.0}, "2026-01-01") is None                  # too little history
    f = tmp_path / "v.csv"
    f.write_text("observation_date,VIXCLS\n2026-01-01,20.5\n2026-01-02,.\n2026-01-05,\n", encoding="utf-8")
    assert load_vix(f) == {"2026-01-01": 20.5} and load_vix(tmp_path / "none.csv") == {}


def test_bonferroni_bar_grows_with_the_number_of_cells():
    assert bonferroni_t(1) == pytest.approx(1.96, abs=0.01)
    assert bonferroni_t(10) > bonferroni_t(2) > bonferroni_t(1)


def fake_cells(n_noise_cells, real_effect):
    rng = random.Random(7)
    cells = [("src", f"noise{i}", [rng.gauss(0, 0.02) for _ in range(MIN_CELL * 2)]) for i in range(n_noise_cells)]
    cells.append(("src", "real", [real_effect + rng.gauss(0, 0.01) for _ in range(MIN_CELL * 2)]))
    cells.append(("src", "tiny", [0.05 for _ in range(MIN_CELL - 1)]))             # too few scores: never examined
    return cells


def test_only_a_strong_effect_in_a_big_enough_cell_is_a_candidate():
    found, bar, examined = candidate_patterns(fake_cells(20, 0.02))
    assert examined == 21 and [f[1] for f in found] == ["real"] and bar > 3
    assert candidate_patterns(fake_cells(20, 0.0))[0] == []


def test_pattern_cells_split_by_direction_weekday_and_vix_on_the_sources_horizon():
    sigs = [{"signal_id": "a", "source": "short_volume_v1", "direction": -1, "date_et": "2026-11-11"},         # Wednesday
            {"signal_id": "b", "source": "short_volume_v1", "direction": 1, "date_et": "2026-11-12"}]
    scores = [{"signal_id": "a", "horizon": 5, "net_excess": 0.01}, {"signal_id": "a", "horizon": 1, "net_excess": 5.0},
              {"signal_id": "b", "horizon": 5, "net_excess": -0.02}, {"signal_id": "zzz", "horizon": 5, "net_excess": 1.0}]
    cells = {(s, label): v for s, label, v in pattern_cells(sigs, scores, {})}
    assert cells[("short_volume_v1", "direction=short")] == [0.01] and cells[("short_volume_v1", "weekday=Thu")] == [-0.02]
    assert not any("vix" in label for _, label in cells)                                     # no VIX data: no vix cells
