from datetime import date, datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from tempo.data import Bars
from tempo.exec_score import Intraday
from tempo.ledger import Ledger
from tempo.ledger_score import ibkr_intraday, score_pending

ET = ZoneInfo("America/New_York")


def weekdays(n, start):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


HIST = weekdays(60, date(2026, 8, 3))
EVENT = ["2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06"]
DATES = HIST + EVENT
MKT = [100.0 * (1 + 0.004 * ((i * 7) % 5 - 2)) for i in range(len(DATES))]


def daily(closes):
    return Bars(DATES, closes, closes, closes, closes)


def intraday(entry_px, exit_px):
    """Entry bar on 11-04; an exit bar on 11-04 (1-day) and on 11-06 (3-day)."""
    return Intraday({("2026-11-04", "09:40"): entry_px, ("2026-11-04", "15:45"): exit_px, ("2026-11-06", "15:45"): exit_px})


DAILY = {"SPY": daily(MKT), "AAA": daily(MKT), "BBB": daily(MKT)}
INTRA = {"SPY": intraday(100.0, 100.5), "AAA": intraday(10.0, 10.4), "BBB": intraday(20.0, 19.6)}


def ledger_with(tmp_path, symbols=("AAA", "BBB")):
    ledger = Ledger(tmp_path / "l.jsonl", clock=lambda: datetime(2026, 11, 3, 20, 0, tzinfo=ET).timestamp())
    for s in symbols:
        ledger.record_signal(source="src_v1", symbol=s, direction=1, event_id="e1")
    return ledger


def test_scores_what_can_be_scored_and_reports_what_must_wait(tmp_path):
    ledger = ledger_with(tmp_path)
    calls, intra_calls = [], []

    def get_bars(symbol):
        calls.append(symbol)
        return DAILY.get(symbol)

    def get_intraday(symbol):
        intra_calls.append(symbol)
        return INTRA.get(symbol)

    written, waiting = score_pending(ledger, get_bars, get_intraday, horizons=(1, 3, 5))
    assert written == 4            # horizons 1 and 3 for both symbols (entry 11-04, three days of data from then)
    assert waiting == 2            # horizon 5 needs days we do not have yet
    assert sorted(calls) == ["AAA", "BBB", "SPY"] and sorted(intra_calls) == ["AAA", "BBB", "SPY"]   # each fetched once
    first = [r for r in ledger.scores() if r["symbol"] == "AAA" and r["horizon"] == 1][0]
    assert first["method"] == "exec_v2" and first["entry_px"] == 10.0 and first["exit_px"] == 10.4


def test_running_it_twice_writes_nothing_new(tmp_path):
    ledger = ledger_with(tmp_path)
    args = (lambda s: DAILY.get(s), lambda s: INTRA.get(s))
    score_pending(ledger, *args, horizons=(1, 3))
    assert score_pending(ledger, *args, horizons=(1, 3)) == (0, 0)


def test_a_symbol_without_bars_is_left_waiting_not_dropped(tmp_path):
    ledger = ledger_with(tmp_path, symbols=("AAA", "ZZZ"))
    written, waiting = score_pending(ledger, lambda s: DAILY.get(s), lambda s: INTRA.get(s), horizons=(1,))
    assert written == 1 and waiting == 1
    assert [r["symbol"] for r in ledger.scores()] == ["AAA"]


def test_a_symbol_without_intraday_bars_is_left_waiting_too(tmp_path):
    ledger = ledger_with(tmp_path)
    written, waiting = score_pending(ledger, lambda s: DAILY.get(s), lambda s: None if s == "BBB" else INTRA.get(s), horizons=(1,))
    assert (written, waiting) == (1, 1)


def test_nothing_to_do_without_signals(tmp_path):
    ledger = Ledger(tmp_path / "empty.jsonl")
    assert score_pending(ledger, lambda s: None, lambda s: None, horizons=(1,)) == (0, 0)


def test_ibkr_intraday_keys_bars_by_new_york_date_and_start_time():
    utc_bar = datetime(2026, 11, 12, 14, 40, tzinfo=ZoneInfo("UTC"))          # 09:40 in New York (EST)
    rows = [SimpleNamespace(date=utc_bar, open=159.56), SimpleNamespace(date="2026-11-12 15:45:00", open=164.36)]
    fake = SimpleNamespace(qualifyContracts=lambda c: [c], reqHistoricalData=lambda *a, **k: rows)
    out = ibkr_intraday(fake, "NVDA")
    assert out.open_at("2026-11-12", "09:40") == 159.56 and out.open_at("2026-11-12", "15:45") == 164.36
    assert ibkr_intraday(SimpleNamespace(qualifyContracts=lambda c: [], reqHistoricalData=None), "ZZZ") is None
    assert ibkr_intraday(SimpleNamespace(qualifyContracts=lambda c: [c], reqHistoricalData=lambda *a, **k: []), "ZZZ") is None
