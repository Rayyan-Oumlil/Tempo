from types import SimpleNamespace as NS

from tempo.smoke import run_test


class FakeEvent:
    def __init__(self):
        self.handlers = []

    def __iadd__(self, h):
        self.handlers.append(h)
        return self

    def __isub__(self, h):
        self.handlers.remove(h)
        return self

    def emit(self, *args):
        for h in list(self.handlers):
            h(*args)


def test_passing_test_reports_ok():
    ib = NS(errorEvent=FakeEvent())
    r = run_test(ib, "t", lambda ib, s: f"hello {s}", "SPY")
    assert (r.ok, r.detail) == (True, "hello SPY")


def test_exception_becomes_fail_not_crash():
    ib = NS(errorEvent=FakeEvent())

    def boom(ib, s):
        raise RuntimeError("nope")

    r = run_test(ib, "t", boom, "SPY")
    assert not r.ok and "RuntimeError: nope" in r.detail


def test_ib_error_codes_are_attached_but_info_codes_are_not():
    ib = NS(errorEvent=FakeEvent())

    def noisy(ib, s):
        ib.errorEvent.emit(1, 2104, "farm ok")
        ib.errorEvent.emit(1, 10089, "needs subscription")
        return "done"

    r = run_test(ib, "t", noisy, "SPY")
    assert "[10089] needs subscription" in r.detail and "2104" not in r.detail
    assert ib.errorEvent.handlers == []  # handler is always detached
