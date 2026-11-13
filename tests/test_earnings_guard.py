from datetime import datetime

import pytest

from tempo.earnings_guard import MIN_PER_ARM, effective_day, has_earnings, render, split, summarize, verdict
from tempo.earnings_reaction import ET


def at(day, hh, mm=0):
    return datetime.fromisoformat(f"{day}T{hh:02d}:{mm:02d}:00").replace(tzinfo=ET)


def test_a_release_after_the_close_moves_the_next_session_and_one_before_the_open_moves_that_day():
    assert effective_day(at("2026-11-16", 16, 5)).isoformat() == "2026-11-17"
    assert effective_day(at("2026-11-16", 7, 0)).isoformat() == "2026-11-16"
    assert effective_day(at("2026-11-16", 11, 0)).isoformat() == "2026-11-16"          # accepted during the session: its own date
    assert effective_day(at("2026-11-20", 17, 0)).isoformat() == "2026-11-23"          # Friday evening: Monday


def test_window_is_inclusive_on_both_ends():
    f = [at("2026-11-16", 16, 30)]                                                       # reaction session 2026-11-17
    assert has_earnings(f, "2026-11-17", "2026-11-23") and has_earnings(f, "2026-11-10", "2026-11-17")
    assert not has_earnings(f, "2026-11-18", "2026-11-25") and not has_earnings(f, "2026-11-09", "2026-11-16")
    assert not has_earnings([], "2026-11-17", "2026-11-23")


def score(source, symbol, net, entry="2026-11-17", exit_="2026-11-23", horizon=5):
    return {"source": source, "symbol": symbol, "net_excess": net, "entry_date": entry, "exit_date": exit_, "horizon": horizon}


def test_earnings_sources_are_left_out_and_an_unknown_symbol_is_an_error_not_no_earnings():
    rows = split([score("earnings_reaction_v1", "AAA", 0.1), score("short_volume_v1", "BBB", 0.01)], {"BBB": [at("2026-11-17", 17)]})
    assert [r["symbol"] for r in rows] == ["BBB"] and rows[0]["earnings"] is True
    with pytest.raises(KeyError):
        split([score("short_volume_v1", "ZZZ", 0.01)], {})


def make_rows(n_with, n_without, sd_with, sd_without):
    rows = [{"source": "s", "horizon": 5, "net_excess": (-1) ** i * sd_with, "earnings": True} for i in range(n_with)]
    rows += [{"source": "s", "horizon": 5, "net_excess": (-1) ** i * sd_without, "earnings": False} for i in range(n_without)]
    return rows


def test_summary_counts_and_spread_with_and_without_the_earnings_trades():
    s = summarize(make_rows(10, 20, 0.10, 0.01))
    for key in ("s h5", "ALL h5"):
        assert s[key]["n"] == 30 and s[key]["n_earnings"] == 10
        assert s[key]["sd_kept"] < s[key]["sd"]
    assert s["s h5"]["mean_kept"] == pytest.approx(0.0, abs=0.001)


def test_verdict_needs_enough_trades_in_both_arms_and_a_real_fall_in_spread():
    assert verdict(summarize(make_rows(10, 20, 0.10, 0.01))["s h5"]) == "variance falls: keep the guard"
    assert verdict(summarize(make_rows(10, 20, 0.01, 0.10))["s h5"]).startswith("variance does not fall")
    assert verdict(summarize(make_rows(MIN_PER_ARM - 1, 20, 0.10, 0.01))["s h5"]).startswith("too few")
    assert verdict(summarize(make_rows(10, MIN_PER_ARM - 1, 0.10, 0.01))["s h5"]).startswith("too few")


def test_render_has_a_row_per_group_and_says_when_empty():
    text = render(summarize(make_rows(10, 20, 0.10, 0.01)))
    assert "s h5" in text and "ALL h5" in text and "measurement only" in text
    assert "no scored signal" in render({})
