from datetime import datetime
from zoneinfo import ZoneInfo

from tempo import daily_report as dr

NOW = datetime(2026, 11, 11, 18, 45, tzinfo=ZoneInfo("America/New_York"))
GOOD = dict(now=NOW, trading_day=True, heartbeat_age_min=4, heartbeat_ok=True,
            sched_lines_today=("2026-11-11 16:41:56 ET evening: git -> rc 0: ledger committed and pushed",
                               "2026-11-11 19:16:56 ET late: git -> rc 0: ledger unchanged"),
            backup_age_h=20, disk_free_share=0.9, collector_age_days={"finra_short_volume": 0.5, "fred": 0.5, "options": 0.5, "vol_series": 0.5}, ledger_counts={"a": 3})


def test_all_good_says_so():
    subject, body = dr.build(dr.Facts(**GOOD))
    assert subject == "Tempo daily: all good" and "PROBLEM" not in body


def _problems(**override):
    subject, body = dr.build(dr.Facts(**{**GOOD, **override}))
    return subject, [ln for ln in body.splitlines() if ln.startswith("PROBLEM")]


def test_each_failure_is_named():
    assert len(_problems(heartbeat_age_min=45)[1]) == 1
    assert len(_problems(heartbeat_ok=False)[1]) == 1
    assert len(_problems(backup_age_h=None)[1]) == 1
    assert len(_problems(backup_age_h=40)[1]) == 1
    assert len(_problems(disk_free_share=0.05)[1]) == 1
    assert len(_problems(sched_lines_today=())[1]) == 2                      # evening and late never pushed
    assert len(_problems(sched_lines_today=GOOD["sched_lines_today"] + ("x: FAILED boom",))[1]) == 1
    assert len(_problems(sched_lines_today=GOOD["sched_lines_today"][:1])[1]) == 1                 # only late missing
    subject, p = _problems(heartbeat_age_min=None, backup_age_h=None)
    assert subject == "Tempo daily: 2 PROBLEM(S)" and len(p) == 2


def test_weekend_does_not_demand_the_evening_job():
    assert _problems(trading_day=False, sched_lines_today=())[1] == []


def test_a_stale_collector_is_a_problem(monkeypatch):
    monkeypatch.setattr(dr, "COLLECTORS", (("opt", True, 1),))
    assert len(_problems(collector_age_days={"opt": 3.0})[1]) == 1
    assert len(_problems(collector_age_days={"opt": None})[1]) == 1
    assert _problems(collector_age_days={"opt": 0.2})[1] == []
    assert _problems(collector_age_days={"opt": 9.0}, trading_day=False, sched_lines_today=())[1] == []


def test_slippage_alarms_and_table_reach_the_email():
    subject, body = dr.build(dr.Facts(**GOOD, slippage_text="TABLE", slippage_alarms=("x: 80 bps",)))
    assert "1 PROBLEM" in subject and "PROBLEM: paper fills vs ledger: x: 80 bps" in body and "TABLE" in body
    assert dr.build(dr.Facts(**GOOD))[0] == "Tempo daily: all good"


def test_gateway_login_trouble_is_a_problem_in_the_email():
    subject, body = dr.build(dr.Facts(**GOOD, gateway_login=("Gateway login: 'Unrecognized Username or Password' x3 (first a, last b)",)))
    assert "1 PROBLEM" in subject and "PROBLEM: Gateway login: 'Unrecognized Username or Password'" in body
