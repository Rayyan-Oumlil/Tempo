from datetime import datetime
from zoneinfo import ZoneInfo

from tempo.data import Bars
from tempo.ledger import Ledger
from tempo.ledger_score import score_pending

ET = ZoneInfo("America/New_York")
DATES = ["2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06"]


def bars(opens, closes):
    return Bars(DATES, opens, [max(o, c) for o, c in zip(opens, closes)], [min(o, c) for o, c in zip(opens, closes)], closes)


SPY = bars([100.0, 100.0, 100.5, 101.0], [100.2, 100.4, 100.7, 101.1])
STOCKS = {"AAA": bars([10.0, 10.0, 10.5, 11.0], [10.2, 10.4, 10.9, 11.2]), "BBB": bars([20.0, 20.0, 19.5, 19.0], [20.1, 19.6, 19.1, 18.8])}


def ledger_with(tmp_path, symbols=("AAA", "BBB")):
    ledger = Ledger(tmp_path / "l.jsonl", clock=lambda: datetime(2026, 11, 3, 20, 0, tzinfo=ET).timestamp())
    for s in symbols:
        ledger.record_signal(source="src_v1", symbol=s, direction=1, event_id="e1")
    return ledger


def test_scores_what_can_be_scored_and_reports_what_must_wait(tmp_path):
    ledger = ledger_with(tmp_path)
    calls = []

    def get_bars(symbol):
        calls.append(symbol)
        return SPY if symbol == "SPY" else STOCKS[symbol]

    written, waiting = score_pending(ledger, get_bars, horizons=(1, 3, 5))
    assert written == 4            # horizons 1 and 3 for both symbols (entry 11-04, 3 days of data after the signal)
    assert waiting == 2            # horizon 5 needs days we do not have yet
    assert sorted(calls) == ["AAA", "BBB", "SPY"]  # each symbol fetched once


def test_running_it_twice_writes_nothing_new(tmp_path):
    ledger = ledger_with(tmp_path)
    get_bars = lambda s: SPY if s == "SPY" else STOCKS[s]
    score_pending(ledger, get_bars, horizons=(1, 3))
    assert score_pending(ledger, get_bars, horizons=(1, 3)) == (0, 0)


def test_a_symbol_without_bars_is_left_waiting_not_dropped(tmp_path):
    ledger = ledger_with(tmp_path, symbols=("AAA", "ZZZ"))
    get_bars = lambda s: None if s == "ZZZ" else (SPY if s == "SPY" else STOCKS[s])
    written, waiting = score_pending(ledger, get_bars, horizons=(1,))
    assert written == 1 and waiting == 1
    assert [r["symbol"] for r in ledger.scores()] == ["AAA"]


def test_nothing_to_do_without_signals(tmp_path):
    ledger = Ledger(tmp_path / "empty.jsonl")
    assert score_pending(ledger, lambda s: None, horizons=(1,)) == (0, 0)
