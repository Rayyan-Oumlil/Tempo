from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from tempo.data import Bars
from tempo.ledger import (MIN_SCORED, ROUND_TRIP_COST, Ledger, SignalRefused, score_signal, status_line, summarize,
                          unscored)

ET = ZoneInfo("America/New_York")


def clock_at(y, m, d, hh=20, mm=0):
    return lambda: datetime(y, m, d, hh, mm, tzinfo=ET).timestamp()


def make_ledger(tmp_path, clock=None):
    return Ledger(tmp_path / "ledger.jsonl", clock=clock or clock_at(2026, 11, 3))


def sig(ledger, **over):
    kw = dict(source="insider_v1", symbol="XYZ", direction=1, event_id="0001", features={"n_insiders": 3}, price=10.0)
    return ledger.record_signal(**{**kw, **over})


def bars(dates, opens, closes):
    return Bars(dates, opens, [max(o, c) for o, c in zip(opens, closes)], [min(o, c) for o, c in zip(opens, closes)], closes)


DATES = ["2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06", "2026-11-09"]
STOCK = bars(DATES, [10.0, 10.0, 10.5, 11.0, 11.5], [10.2, 10.4, 10.9, 11.2, 11.8])
BENCH = bars(DATES, [100.0, 100.0, 100.5, 101.0, 101.0], [100.2, 100.4, 100.7, 101.1, 101.5])


def test_a_signal_is_stamped_with_the_clock_and_the_new_york_date(tmp_path):
    rec = sig(make_ledger(tmp_path))
    assert rec["kind"] == "signal" and rec["signal_id"] == "insider_v1:XYZ:0001"
    assert rec["date_et"] == "2026-11-03" and rec["direction"] == 1 and rec["backfill"] is False
    assert rec["features"] == {"n_insiders": 3} and rec["price"] == 10.0


def test_the_date_is_the_new_york_date_not_utc(tmp_path):
    late = make_ledger(tmp_path, clock_at(2026, 11, 3, 23, 30))  # 04:30 UTC the next day
    assert sig(late)["date_et"] == "2026-11-03"


def test_a_duplicate_event_is_refused_but_other_symbols_and_sources_are_not(tmp_path):
    ledger = make_ledger(tmp_path)
    sig(ledger)
    with pytest.raises(SignalRefused, match="already recorded"):
        sig(ledger)
    sig(ledger, symbol="ABC")
    sig(ledger, source="llm_v1")
    assert len(ledger.signals()) == 3


@pytest.mark.parametrize("over", [dict(direction=0), dict(direction=2), dict(source=""), dict(symbol=""), dict(event_id="")])
def test_bad_signals_are_refused(tmp_path, over):
    with pytest.raises(SignalRefused):
        sig(make_ledger(tmp_path), **over)


def test_backfilled_signals_are_kept_but_excluded_from_evaluation_by_default(tmp_path):
    ledger = make_ledger(tmp_path)
    sig(ledger)
    sig(ledger, symbol="OLD", event_id="9", backfill=True)
    assert [s["symbol"] for s in ledger.signals()] == ["XYZ"]
    assert {s["symbol"] for s in ledger.signals(include_backfill=True)} == {"XYZ", "OLD"}


def test_the_ledger_survives_a_new_instance(tmp_path):
    sig(make_ledger(tmp_path))
    again = Ledger(tmp_path / "ledger.jsonl", clock=clock_at(2026, 11, 4))
    assert len(again.signals()) == 1
    with pytest.raises(SignalRefused):
        sig(again)


def test_scoring_enters_at_the_next_open_and_exits_at_the_close_of_the_last_day(tmp_path):
    s = sig(make_ledger(tmp_path))  # signal on 2026-11-03 evening
    score = score_signal(s, STOCK, BENCH, horizon=3)
    assert score["entry_date"] == "2026-11-04" and score["exit_date"] == "2026-11-06"
    assert score["ret"] == pytest.approx(11.2 / 10.0 - 1)
    assert score["bench_ret"] == pytest.approx(101.1 / 100.0 - 1)
    assert score["excess"] == pytest.approx(score["ret"] - score["bench_ret"])
    assert score["net_excess"] == pytest.approx(score["excess"] - ROUND_TRIP_COST)


def test_a_short_signal_flips_the_sign(tmp_path):
    s = sig(make_ledger(tmp_path), direction=-1)
    long_score = score_signal(sig(make_ledger(tmp_path / "other")), STOCK, BENCH, 3)
    short_score = score_signal(s, STOCK, BENCH, 3)
    assert short_score["ret"] == pytest.approx(-long_score["ret"])
    assert short_score["excess"] == pytest.approx(-long_score["excess"])


def test_scoring_never_uses_prices_on_or_before_the_signal_date(tmp_path):
    s = sig(make_ledger(tmp_path))
    changed = bars(DATES, [999.0, 10.0, 10.5, 11.0, 11.5], [999.0, 10.4, 10.9, 11.2, 11.8])  # day-of-signal prices altered
    assert score_signal(s, changed, BENCH, 3) == score_signal(s, STOCK, BENCH, 3)


def test_a_signal_is_not_scoreable_until_the_horizon_has_passed(tmp_path):
    s = sig(make_ledger(tmp_path))
    assert score_signal(s, STOCK, BENCH, horizon=4) is not None   # entry 11-04 .. exit 11-09
    assert score_signal(s, STOCK, BENCH, horizon=5) is None       # would need a day we do not have yet


def test_a_signal_needs_the_benchmark_on_the_same_days(tmp_path):
    s = sig(make_ledger(tmp_path))
    thin = bars(DATES[:3], BENCH.open[:3], BENCH.close[:3])
    assert score_signal(s, STOCK, thin, horizon=3) is None


def test_scores_are_written_once(tmp_path):
    ledger = make_ledger(tmp_path)
    s = sig(ledger)
    score = score_signal(s, STOCK, BENCH, 3)
    assert ledger.record_scores([score]) == 1
    assert ledger.record_scores([score]) == 0  # idempotent
    assert len([r for r in ledger.journal.records() if r["kind"] == "score"]) == 1


def test_unscored_lists_what_is_still_to_do(tmp_path):
    ledger = make_ledger(tmp_path)
    s = sig(ledger)
    ledger.record_scores([score_signal(s, STOCK, BENCH, 3)])
    todo = unscored(ledger, horizons=(1, 3, 5))
    assert [(x["signal_id"], h) for x, h in todo] == [(s["signal_id"], 1), (s["signal_id"], 5)]


def test_summary_statistics():
    scores = [{"net_excess": x} for x in (0.02, 0.03, -0.01, 0.04, 0.02)]
    n, mean, t, hit = summarize(scores)
    assert n == 5 and mean == pytest.approx(0.02) and hit == pytest.approx(0.8) and t > 1
    assert summarize([]) == (0, 0.0, None, 0.0)
    assert summarize([{"net_excess": 0.01}])[2] is None


def test_the_status_line_refuses_to_conclude_before_enough_scores():
    assert "NOT ENOUGH" in status_line(MIN_SCORED - 1, 0.05, 4.0, 0.7)
    assert "NOT ENOUGH" not in status_line(MIN_SCORED, 0.05, 4.0, 0.7)


def test_a_score_of_exactly_zero_is_not_a_hit():
    assert summarize([{"net_excess": 0.0}, {"net_excess": 0.01}])[3] == 0.5


from tempo.ledger import cli_add


def test_cli_add_records_a_long_call_with_its_features(tmp_path):
    ledger = make_ledger(tmp_path)
    rec = cli_add(["claude_earnings_v1", "AMD", "+1", "2026Q3", "--confidence", "3", "--reason", "strong guide", "--url", "http://x", "--eps", "1.97"], ledger)
    assert rec["direction"] == 1 and rec["signal_id"] == "claude_earnings_v1:AMD:2026Q3"
    assert rec["features"] == {"confidence": 3, "reason": "strong guide", "release_url": "http://x", "eps_estimate": 1.97}


@pytest.mark.parametrize("word,expected", [("-1", -1), ("short", -1), ("long", 1), ("+1", 1)])
def test_cli_add_understands_direction_words(tmp_path, word, expected):
    assert cli_add(["s", "T", word, "e1", "--confidence", "2"], make_ledger(tmp_path))["direction"] == expected


def test_cli_add_refuses_a_confidence_outside_one_to_five_and_unknown_directions(tmp_path):
    with pytest.raises(SignalRefused):
        cli_add(["s", "T", "+1", "e1", "--confidence", "9"], make_ledger(tmp_path))
    with pytest.raises(SignalRefused):
        cli_add(["s", "T", "maybe", "e1", "--confidence", "3"], make_ledger(tmp_path))
