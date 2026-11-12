import json
from datetime import datetime
from zoneinfo import ZoneInfo

from tempo.watchdog import ALERT_AFTER, RESTART_AFTER, STILL_DOWN_AFTER, State, in_maintenance, load_state, run_once, step

ET = ZoneInfo("America/New_York")


def at(h, m=0):
    return datetime(2026, 11, 11, h, m, tzinfo=ET)


def test_the_nightly_gateway_restart_window_is_not_counted_as_an_outage():
    assert in_maintenance(at(23, 59)) and in_maintenance(at(0, 10)) and in_maintenance(at(23, 50))
    assert not in_maintenance(at(23, 49)) and not in_maintenance(at(0, 26)) and not in_maintenance(at(13, 0))
    state, actions = step(State(1, False), ok=False, now=at(23, 59))
    assert state == State(1, False) and actions == []


def test_a_healthy_check_is_silent_and_a_single_failure_is_not_an_alert():
    assert step(State(), True, at(10)) == (State(), [])
    state, actions = step(State(), False, at(10))
    assert state == State(1, False) and actions == []


def test_second_failure_alerts_third_restarts_sixth_says_the_restart_did_not_help():
    state = State()
    seen = []
    for i in range(1, 8):
        state, actions = step(state, False, at(10))
        seen.append((i, actions))
    assert (ALERT_AFTER, ["alert_down"]) in seen
    assert (RESTART_AFTER, ["restart"]) in seen
    assert (STILL_DOWN_AFTER, ["alert_still_down"]) in seen
    assert [a for _, a in seen if a] == [["alert_down"], ["restart"], ["alert_still_down"]]      # exactly once each


def test_recovery_is_announced_only_if_an_outage_was_alerted_and_resets_the_counters():
    assert step(State(ALERT_AFTER, False), True, at(10)) == (State(), ["recovered"])
    assert step(State(RESTART_AFTER, True), True, at(10)) == (State(), ["recovered"])
    assert step(State(ALERT_AFTER - 1, False), True, at(10)) == (State(), [])      # a blip that never alerted


def test_state_survives_a_missing_or_corrupt_file(tmp_path):
    assert load_state(tmp_path / "nope.json") == State()
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert load_state(bad) == State()


def test_run_once_wires_check_restart_alert_and_persists_state(tmp_path):
    path = tmp_path / "state.json"
    calls = {"restart": 0, "alerts": []}

    def run(ok, now):
        return run_once(now=now, check=lambda: (ok, "detail"), restart=lambda: calls.__setitem__("restart", calls["restart"] + 1) or 0,
                        notify=lambda t, b: calls["alerts"].append(t), state_path=path, heartbeat_path=tmp_path / "hb.json", log=lambda s: None)

    run(False, at(10)); run(False, at(10, 10)); run(False, at(10, 20))
    assert calls["restart"] == 1 and len(calls["alerts"]) == 2          # down alert, then the restart notice
    assert json.loads(path.read_text(encoding="utf-8"))["failures"] == 3
    run(True, at(10, 30))
    assert calls["alerts"][-1].endswith("recovered") and json.loads(path.read_text(encoding="utf-8"))["failures"] == 0
    assert json.loads((tmp_path / "hb.json").read_text(encoding="utf-8"))["ok"] is True


def test_ping_goes_to_the_url_when_ok_and_to_fail_when_not_and_never_raises():
    from tempo.watchdog import make_ping
    calls = []
    ping = make_ping("https://hc.example/abc/", lambda url, timeout: calls.append((url, timeout)))
    ping(True), ping(False)
    assert calls == [("https://hc.example/abc/", 10), ("https://hc.example/abc/fail", 10)]
    make_ping("https://x", lambda url, timeout: (_ for _ in ()).throw(OSError("down")))(True)     # reported, not raised
    make_ping(None, lambda *a, **k: calls.append("never"))(True)
    assert len(calls) == 2


def test_run_once_pings_last_and_a_failing_ping_cannot_stop_the_state_being_written(tmp_path):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from tempo.watchdog import run_once
    seen = []
    state = run_once(now=datetime(2026, 11, 11, 12, 0, tzinfo=ZoneInfo("America/New_York")), check=lambda: (True, "ok"), restart=lambda: 0,
                     notify=lambda t, b: None, state_path=tmp_path / "s.json", heartbeat_path=tmp_path / "h.json", log=lambda s: None,
                     ping=lambda ok: seen.append((ok, (tmp_path / "h.json").exists())))
    assert state.failures == 0 and seen == [(True, True)]                                         # heartbeat already on disk when pinged
