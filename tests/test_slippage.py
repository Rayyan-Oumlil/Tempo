from tempo import slippage as sl


def entered(sid, d, fill, ref=100.0, exit_fill=None, status="entered"):
    return sid, {"status": status, "direction": d, "fill_price": fill, "ref_price": ref, "symbol": sid.split(":")[1],
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
