from datetime import datetime

from tempo import slippage as sl

ON_TIME = datetime(2026, 11, 13, 9, 41, tzinfo=sl.ET).timestamp()
LATE = datetime(2026, 11, 13, 15, 0, tzinfo=sl.ET).timestamp()


def entered(sid, d, fill, ref=100.0, exit_fill=None, status="entered", ts=ON_TIME):
    return sid, {"status": status, "direction": d, "fill_price": fill, "ref_price": ref, "symbol": sid.split(":")[1], "ts": ts,
                 **({"exit_fill_price": exit_fill} if exit_fill else {})}


def score(sid, entry_px=100.0, exit_px=110.0, horizon=5):
    return {"signal_id": sid, "horizon": horizon, "entry_px": entry_px, "exit_px": exit_px, "entry_date": "2026-11-13"}


def test_a_long_paying_more_and_a_short_receiving_less_are_both_positive_gaps():
    state = dict([entered("analyst_actions_v1:AAA:1", 1, 100.5), entered("analyst_actions_v1:BBB:1", -1, 99.5)])
    rows, pending, _ = sl.trade_gaps(state, [score("analyst_actions_v1:AAA:1"), score("analyst_actions_v1:BBB:1")])
    assert pending == 0 and [round(r["entry_gap_bps"]) for r in rows] == [50, 50]


def test_better_than_the_ledger_is_negative_and_exit_gap_has_the_opposite_sign():
    state = dict([entered("analyst_actions_v1:AAA:1", 1, 99.0, exit_fill=109.0, status="exited")])
    (row,), *_ = sl.trade_gaps(state, [score("analyst_actions_v1:AAA:1")])
    assert round(row["entry_gap_bps"]) == -100 and round(row["exit_gap_bps"]) == 91     # sold 109 where the ledger sold 110


def test_unscored_trades_are_pending_and_skips_are_ignored():
    state = dict([entered("analyst_actions_v1:AAA:1", 1, 100.0),
                  ("analyst_actions_v1:SKP:1", {"status": "skipped", "symbol": "SKP"})])
    rows, pending, _ = sl.trade_gaps(state, [score("analyst_actions_v1:AAA:1", horizon=21)])    # wrong horizon: not this trade's score
    assert rows == [] and pending == 1


def test_alarm_needs_enough_trades_and_uses_the_absolute_gap_of_the_latest_ones():
    def rows(n, fill):
        state = dict(entered(f"analyst_actions_v1:S{i}:1", 1, fill) for i in range(n))
        return sl.trade_gaps(state, [score(f"analyst_actions_v1:S{i}:1") for i in range(n)])[0]
    assert sl.alarms(sl.summarize(rows(19, 101.0))) == []                     # 100 bps but only 19 trades
    assert len(sl.alarms(sl.summarize(rows(20, 101.0)))) == 1
    assert sl.alarms(sl.summarize(rows(20, 100.5))) == []                     # 50 bps is inside the limit
    mixed = rows(10, 101.0) + [{**r, "entry_gap_bps": -100.0} for r in rows(10, 101.0)]
    assert len(sl.alarms(sl.summarize(mixed))) == 1                           # offsetting signs must not hide it


def test_render_says_so_when_nothing_is_scored():
    text, problems = sl.render([], 3)
    assert "no paper trade has an exec_v2 score yet" in text and "3 entered" in text and problems == []


def test_a_traded_source_without_a_horizon_is_reported_not_silently_pending():
    state = dict([entered("mystery_v1:AAA:1", 1, 100.0)])
    rows, pending, unknown = sl.trade_gaps(state, [])
    assert rows == [] and pending == 0 and unknown == ["mystery_v1"]
    _, problems = sl.render(rows, pending, unknown)
    assert any("mystery_v1" in p and "HORIZONS" in p for p in problems)


def test_entry_delay_is_measured_from_0940_on_the_entry_date():
    assert round(sl.entry_delay_min(ON_TIME, "2026-11-13")) == 1
    assert round(sl.entry_delay_min(LATE, "2026-11-13")) == 320
    assert sl.entry_delay_min(ON_TIME, "2026-11-14") < 0


def test_late_entries_are_counted_apart_and_never_reach_the_means_or_the_alarm():
    state = dict([entered(f"analyst_actions_v1:S{i}:1", 1, 103.0, ts=LATE) for i in range(25)]
                 + [entered(f"analyst_actions_v1:G{i}:1", 1, 100.1) for i in range(20)])
    scores = [score(sid) for sid in state]
    rows, pending, unknown = sl.trade_gaps(state, scores)
    summary = sl.summarize(rows)["analyst_actions_v1"]
    assert summary["n"] == 20 and summary["late_n"] == 25 and round(summary["late_abs"]) == 300
    assert round(summary["entry_abs"]) == 10 and sl.alarms(sl.summarize(rows)) == []        # 300 bps late gaps would have alarmed
    text, problems = sl.render(rows, pending, unknown)
    assert "25 (300)" in text and problems == []


def test_a_source_with_only_late_entries_still_reports_and_does_not_crash():
    state = dict([entered("analyst_actions_v1:AAA:1", 1, 101.0, ts=LATE)])
    rows, pending, _ = sl.trade_gaps(state, [score("analyst_actions_v1:AAA:1")])
    text, problems = sl.render(rows, pending)
    assert "1 (100)" in text and problems == []


def test_a_journaled_entry_without_a_timestamp_is_an_error():
    sid, t = entered("analyst_actions_v1:AAA:1", 1, 100.0)
    del t["ts"]
    import pytest
    with pytest.raises(KeyError):
        sl.trade_gaps({sid: t}, [score(sid)])
