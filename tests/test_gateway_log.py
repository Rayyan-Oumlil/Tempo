from tempo.gateway_log import login_problems

LOG = """2026-11-13 00:15:56:036 IBC: detected frame entitled: Connecting to server...; event=Opened
2026-11-13 00:17:00:668 IBC: detected dialog entitled: Unrecognized Username or Password; event=Activated
2026-11-13 00:17:00:672 IBC: detected dialog entitled: Unrecognized Username or Password; event=Focused
2026-11-13 02:00:00:001 IBC: detected dialog entitled: Unrecognized Username or Password; event=Opened
remove Client 98
"""


def test_a_clean_log_has_no_problem():
    assert login_problems("2026-11-13 06:00:00:000 IBC: Login has completed\nremove Client 98\n") == []
    assert login_problems("") == []


def test_failed_login_is_counted_with_first_and_last_time():
    assert login_problems(LOG) == ["Gateway login: 'Unrecognized Username or Password' x3 (first 2026-11-13 00:17:00, last 2026-11-13 02:00:00)"]


def test_each_kind_is_reported_separately_and_a_line_without_stamp_still_counts():
    out = login_problems("Second Factor Authentication window\n2026-11-13 03:00:00:000 IBC: Existing session detected\n")
    assert len(out) == 2 and "x1 (first ?, last ?)" in out[0] and "first 2026-11-13 03:00:00" in out[1]
