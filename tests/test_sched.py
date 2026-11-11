from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from tempo.journal import Journal
from tempo.sched import Step, is_due, previous_trading_days, run_job, steps_for
from tests.test_paper_run import make_ledger as _make_ledger

ET = ZoneInfo("America/New_York")
_LEDGERS: dict = {}


def make_ledger(folder, **kw):
    """One ledger per folder, so repeated calls inside a test see the same signals instead of recording them twice."""
    key = (str(folder), tuple(sorted(kw.items())))
    if key not in _LEDGERS:
        _LEDGERS[key] = _make_ledger(folder, **kw)
    return _LEDGERS[key]


def et(d, hh, mm):
    return datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(timezone.utc)


ENTRY = date(2026, 11, 3)     # entry day of make_ledger's signals (signals dated Mon 2026-11-02)
SAT = date(2026, 11, 7)


class Rec:
    """Fake runner and notifier that remember what they were asked."""

    def __init__(self, rc=0, out="entries: 3 order(s) completed"):
        self.rc, self.out, self.steps, self.notes, self.logs = rc, out, [], [], []

    def run(self, step):
        self.steps.append(step)
        return self.rc, self.out

    def notify(self, title, text):
        self.notes.append((title, text))

    def log(self, line):
        self.logs.append(line)


def go(job, tmp_path, now, rec, final=False, ledger=None, paper=None):
    return run_job(job, now=now, final=final, ledger=ledger or make_ledger(tmp_path), paper=paper or Journal(tmp_path / "paper.jsonl"),
                   run=rec.run, notify=rec.notify, log=rec.log, alerts_path=tmp_path / "alerts.json")


def test_previous_trading_days_skip_weekends_and_holidays_and_come_oldest_first():
    assert previous_trading_days(date(2026, 11, 9), 3) == [date(2026, 11, 4), date(2026, 11, 5), date(2026, 11, 6)]
    assert previous_trading_days(date(2026, 11, 27), 2) == [date(2026, 11, 24), date(2026, 11, 25)]   # Thanksgiving 26th is closed


def test_the_morning_pull_asks_for_the_last_three_trading_days_so_a_gap_heals():
    (step,) = steps_for("morning", date(2026, 11, 10))
    assert step.argv[-4:] == ("tempo.insider", "2026-11-05", "2026-11-06", "2026-11-09")


def test_order_jobs_switch_read_only_off_and_nothing_else_does():
    assert ("IBKR_READONLY", "0") in steps_for("entries", ENTRY)[0].env
    assert ("IBKR_READONLY", "0") in steps_for("exits", ENTRY)[0].env
    assert all(("IBKR_READONLY", "0") not in s.env for s in steps_for("evening", ENTRY) + steps_for("morning", ENTRY))


def test_nothing_runs_on_a_day_the_market_is_closed(tmp_path):
    rec = Rec()
    assert go("morning", tmp_path, et(SAT, 6, 30), rec) == 0
    assert rec.steps == [] and rec.notes == []


def test_entries_wait_until_the_window_opens_and_only_run_when_something_is_due(tmp_path):
    rec = Rec()
    assert go("entries", tmp_path, et(ENTRY, 9, 31), rec) == 0 and rec.steps == []        # before 09:35: not allowed yet
    assert go("entries", tmp_path, et(date(2026, 11, 4), 9, 40), rec) == 0 and rec.steps == []   # nothing due that day (only missed)
    assert go("entries", tmp_path, et(ENTRY, 9, 40), rec) == 0
    assert len(rec.steps) == 1 and rec.steps[0].argv[-2:] == ("tempo.paper_run", "entries")


def test_a_successful_entries_run_tells_you_once_what_happened(tmp_path):
    rec = Rec()
    go("entries", tmp_path, et(ENTRY, 9, 40), rec)
    assert len(rec.notes) == 1 and "3 order(s) completed" in rec.notes[0][1]


def test_exits_run_only_when_an_exit_is_due_and_inside_the_exit_window(tmp_path):
    ledger = make_ledger(tmp_path)
    paper = Journal(tmp_path / "paper.jsonl")
    rec = Rec()
    # an entered position whose exit day is today
    paper.append("paper_entry", signal_id=ledger.signals()[0]["signal_id"], symbol="AAA", direction=1, qty=5, partial=False,
                 ref_price=1.0, fill_price=1.0, entry_day="2026-11-03", exit_day="2026-11-09", order_ref="x")
    assert go("exits", tmp_path, et(date(2026, 11, 9), 14, 0), rec, ledger=ledger, paper=paper) == 0 and rec.steps == []   # too early
    assert go("exits", tmp_path, et(date(2026, 11, 9), 15, 47), rec, ledger=ledger, paper=paper) == 0
    assert rec.steps[0].argv[-2:] == ("tempo.paper_run", "exits")


def test_a_failing_job_exits_nonzero_and_alerts_on_the_first_failure_of_the_day_only(tmp_path):
    rec = Rec(rc=1, out="[FAIL] daily P&L not available")
    assert go("entries", tmp_path, et(ENTRY, 9, 40), rec) == 1
    assert len(rec.notes) == 1 and "FAILED" in rec.notes[0][0] and "P&L" in rec.notes[0][1]
    go("entries", tmp_path, et(ENTRY, 9, 55), rec)
    assert len(rec.notes) == 1                                       # the second failure the same day stays quiet
    go("entries", tmp_path, et(ENTRY, 15, 0), rec, final=True)
    assert len(rec.notes) == 2 and "LAST" in rec.notes[1][1]         # but the final attempt always speaks up


def test_a_new_day_alerts_again(tmp_path):
    rec = Rec(rc=1)
    go("entries", tmp_path, et(ENTRY, 9, 40), rec)
    go("entries", tmp_path, et(date(2026, 11, 3), 9, 41), rec)
    assert len(rec.notes) == 1
    (tmp_path / "l2").mkdir()
    ledger = make_ledger(tmp_path / "l2", signal_day=date(2026, 11, 3))        # these signals enter on Wed 2026-11-04
    go("entries", tmp_path, et(date(2026, 11, 4), 9, 40), rec, ledger=ledger)
    assert len(rec.notes) == 2


def test_an_unexpected_exception_is_reported_not_swallowed(tmp_path):
    rec = Rec()

    def boom(step):
        raise OSError("disk gone")

    rc = run_job("entries", now=et(ENTRY, 9, 40), ledger=make_ledger(tmp_path), paper=Journal(tmp_path / "p.jsonl"), run=boom,
                 notify=rec.notify, log=rec.log, alerts_path=tmp_path / "a.json")
    assert rc == 1 and rec.notes and "disk gone" in rec.notes[0][1]


def test_the_evening_job_commits_the_ledger_only_when_it_changed(tmp_path):
    rec = Rec()
    seen = []

    def run(step):
        seen.append(step.argv)
        # `git diff --cached --quiet` returns 1 when something is staged
        return (1, "") if step.argv[:3] == ("git", "diff", "--cached") else (0, "ok")

    rc = run_job("evening", now=et(ENTRY, 16, 20), ledger=make_ledger(tmp_path), paper=Journal(tmp_path / "p.jsonl"), run=run,
                 notify=rec.notify, log=rec.log, alerts_path=tmp_path / "a.json")
    assert rc == 0
    names = [a[0] if a[0] == "git" else a[-1] for a in seen]
    assert names == ["tempo.earnings_reaction", "tempo.analyst_actions", "tempo.weekly_reversal", "tempo.ledger_score", "tempo.ledger", "git", "git", "git", "git"]   # add, diff, commit, push
    seen.clear()
    run_job("evening", now=et(ENTRY, 16, 20), ledger=make_ledger(tmp_path), paper=Journal(tmp_path / "p.jsonl"), run=lambda st: (seen.append(st.argv), (0, "ok"))[1],
            notify=rec.notify, log=rec.log, alerts_path=tmp_path / "a.json")
    assert [a[0] if a[0] == "git" else a[-1] for a in seen] == ["tempo.earnings_reaction", "tempo.analyst_actions", "tempo.weekly_reversal", "tempo.ledger_score", "tempo.ledger", "git", "git"]   # add, diff: nothing staged, stop


def test_is_due_is_false_for_unknown_jobs(tmp_path):
    with pytest.raises(ValueError):
        is_due("nope", et(ENTRY, 9, 40), make_ledger(tmp_path), Journal(tmp_path / "p.jsonl"))


def test_step_is_hashable_and_immutable():
    s = Step(("a",), (("K", "V"),))
    with pytest.raises(AttributeError):
        s.argv = ("b",)  # type: ignore[misc]



def test_one_failing_evening_step_does_not_stop_the_others_or_the_commit_but_still_alerts(tmp_path):
    rec = Rec()
    seen = []

    def run(step):
        seen.append(step.argv)
        if step.argv[-1] == "tempo.earnings_reaction":
            return 1, "[FAIL] SEC feed down"
        return (1, "") if step.argv[:3] == ("git", "diff", "--cached") else (0, "ok")

    rc = run_job("evening", now=et(ENTRY, 16, 35), ledger=make_ledger(tmp_path), paper=Journal(tmp_path / "p.jsonl"), run=run,
                 notify=rec.notify, log=rec.log, alerts_path=tmp_path / "a.json")
    assert rc == 1
    assert ("git", "push") in seen and any(a[-1] == "tempo.ledger_score" for a in seen)
    assert rec.notes and "SEC feed down" in rec.notes[0][1]


def test_the_evening_job_starts_after_the_delayed_close_has_settled():
    import re
    script = (__import__("pathlib").Path(__file__).parents[1] / "tools" / "sched" / "register.ps1").read_text(encoding="utf-8")
    times = re.search(r'Add-Job "Tempo-Evening"\s+"evening"\s+@\(([^)]*)\)', script).group(1)
    assert '"16:20"' not in times and '"16:35"' in times


def test_ibkr_chatter_is_folded_so_the_real_summary_survives_the_tail():
    from tempo.sched import _tail
    out = "summary line\n" + "reqHistoricalNewsAsync: Timeout\n" * 20 + "Error 200, reqId 1: No security definition\n"
    tail = _tail(out, 12)
    assert "summary line" in tail and "21 repetitive IBKR notices folded" in tail and "Timeout" not in tail
