"""Logic that lives in the commands' entry points: refusals, report text, wiring. No broker, no network."""
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

import tempo.forward as forward
import tempo.insider as insider
import tempo.ledger_score as ledger_score
import tempo.paper_run as paper_run
from tempo.data import Bars
from tempo.ledger import Ledger, report, score_signal
from tests.test_forward import ibs_bars

ET = ZoneInfo("America/New_York")


def ledger_at(path, y=2026, m=11, d=3):
    return Ledger(path, clock=lambda: datetime(y, m, d, 20, 0, tzinfo=ET).timestamp())


# --- forward test: the verdict branch -------------------------------------------------------------------------

def test_forward_report_prints_a_verdict_once_enough_round_trips_exist(monkeypatch):
    bars = ibs_bars([0.5, 0.1, 0.5, 0.9, 0.5] * 24, start="2026-10-01")     # a trade every few days, well past the freeze date
    monkeypatch.setattr(forward, "load_ohlc", lambda path: bars)
    monkeypatch.setattr(forward, "MIN_POOLED_TRIPS", 5)
    text = forward.report(today=date(2027, 3, 1))
    assert "NOT ENOUGH" not in text and "VERDICT:" in text
    assert text.count("[PASS]") + text.count("[FAIL]") == 3                   # exactly the three registered criteria
    assert "pooled:" in text and "SPY ibs" in text and "QQQ rsi2" in text


# --- paper_run: refusals happen before any connection ------------------------------------------------------------

@pytest.fixture
def cli(monkeypatch, tmp_path):
    ledger = ledger_at(tmp_path / "ledger.jsonl", 2026, 11, 2)
    ledger.record_signal(source="claude_earnings_v1", symbol="AAA", direction=1, event_id="e1")
    monkeypatch.setattr(paper_run, "PAPER_FILE", tmp_path / "paper.jsonl")
    monkeypatch.setattr(paper_run, "Ledger", lambda: ledger)
    monkeypatch.setattr("tempo.config.load_config", lambda: SimpleNamespace(readonly=True))
    monkeypatch.setattr("tempo.ibkr.connect", lambda cfg: pytest.fail("a refusal must happen before connecting to the broker"))
    return SimpleNamespace(tmp_path=tmp_path)


def test_a_real_run_needs_orders_enabled(cli):
    with pytest.raises(RuntimeError, match="IBKR_READONLY=0"):
        paper_run.main(["entries"])


def test_a_real_run_outside_its_time_window_is_refused(cli, monkeypatch):
    monkeypatch.setattr("tempo.config.load_config", lambda: SimpleNamespace(readonly=False))
    monkeypatch.setattr(paper_run, "entries_allowed", lambda now: False)
    with pytest.raises(RuntimeError, match="not allowed now"):
        paper_run.main(["entries"])
    monkeypatch.setattr(paper_run, "exits_allowed", lambda now: False)
    with pytest.raises(RuntimeError, match="not allowed now"):
        paper_run.main(["exits"])


def test_as_of_is_only_for_dry_runs_and_commands_are_checked(cli):
    with pytest.raises(ValueError, match="--as-of only works together with --dry-run"):
        paper_run.main(["entries", "--as-of", "2026-11-04 09:40"])
    with pytest.raises(ValueError, match="usage"):
        paper_run.main(["frobnicate"])


def test_plan_and_status_print_without_touching_the_broker(cli, capsys):
    assert paper_run.main(["plan", "2026-11-03"]) == 0
    assert "enter ['AAA']" in capsys.readouterr().out
    assert paper_run.main(["status"]) == 0
    assert "0 signals tracked" in capsys.readouterr().out


# --- ledger report -------------------------------------------------------------------------------------------------

def test_the_ledger_report_for_an_empty_ledger_and_for_scored_signals(tmp_path):
    ledger = ledger_at(tmp_path / "l.jsonl")
    assert report(ledger) == "ledger is empty: no signals recorded yet"
    sig = ledger.record_signal(source="src_v1", symbol="AAA", direction=1, event_id="e1")
    days = ["2026-11-03", "2026-11-04", "2026-11-05"]
    stock = Bars(days, [10.0, 10.0, 10.5], [10.2, 10.4, 10.9], [9.9, 9.9, 10.4], [10.1, 10.4, 10.9])
    bench = Bars(days, [100.0, 100.0, 100.5], [100.2, 100.4, 100.7], [99.9, 99.9, 100.4], [100.1, 100.4, 100.7])
    ledger.record_scores([score_signal(sig, stock, bench, 1)])
    text = report(ledger)
    assert "src_v1: 1 signals (2026-11-03 to 2026-11-03)" in text
    assert " 1-day: n=1" in text and "NOT ENOUGH SCORED SIGNALS" in text and " 5-day: n=0" in text


# --- insider: bad XML and the entry point --------------------------------------------------------------------------

def test_malformed_xml_gives_no_purchases_instead_of_crashing():
    assert insider.parse_form4("<ownershipDocument><issuer></ownershipDocument>", "2026-11-02", "A1") == []


def test_the_insider_command_processes_days_in_order_then_records_signals_for_the_last_day(monkeypatch, tmp_path, capsys):
    processed = []
    monkeypatch.setattr(insider, "process_day", lambda day, **kw: processed.append(day) or {"filings": 0, "new": 0, "purchases": 0, "failed": 0})
    buys = [{"accession": f"a{i}", "filing_date": "2026-11-02", "trade_date": "2026-11-02", "issuer_cik": "5", "symbol": "ACME",
             "owners": [str(i)], "shares": 10_000.0, "price": 15.0, "value": 150_000.0} for i in (1, 2)]
    monkeypatch.setattr(insider, "load_cache", lambda *a, **k: (set(), buys))
    ledger = ledger_at(tmp_path / "l.jsonl")
    monkeypatch.setattr(insider, "Ledger", lambda: ledger)
    assert insider.main(["2026-11-02", "2026-10-30"]) == 0
    assert processed == [date(2026, 11, 2), date(2026, 10, 30)]                     # in the order given
    assert "clusters as of 2026-10-30: 0" in capsys.readouterr().out                # signals are computed as of the LAST date given
    assert insider.main(["2026-10-30", "2026-11-02"]) == 0
    assert "new signals recorded: 1" in capsys.readouterr().out and [s["symbol"] for s in ledger.signals()] == ["ACME"]


# --- scorer: the IBKR wrapper and the command ---------------------------------------------------------------------

def fake_history(rows):
    return SimpleNamespace(qualifyContracts=lambda c: [c] if rows is not None else [], reqHistoricalData=lambda *a, **k: rows or [])


def test_ibkr_bars_turns_ib_bars_into_finished_daily_bars_only():
    today = date.today()
    rows = [SimpleNamespace(date=today - timedelta(days=2), open=1.0, high=2.0, low=0.5, close=1.5),
            SimpleNamespace(date=today, open=1.5, high=2.0, low=1.0, close=1.8)]          # today's bar is unfinished
    bars = ledger_score.ibkr_bars(fake_history(rows), "AAA")
    assert bars.dates == [(today - timedelta(days=2)).isoformat()] and bars.close == [1.5]


def test_ibkr_bars_is_none_when_the_symbol_is_unknown_or_has_no_history():
    assert ledger_score.ibkr_bars(fake_history(None), "ZZZ") is None
    assert ledger_score.ibkr_bars(fake_history([]), "ZZZ") is None


def test_the_scoring_command_connects_scores_and_always_disconnects(monkeypatch, tmp_path, capsys):
    ledger = ledger_at(tmp_path / "l.jsonl")
    ledger.record_signal(source="src_v1", symbol="AAA", direction=1, event_id="e1")
    log = []
    fake_ib = SimpleNamespace(disconnect=lambda: log.append("disconnected"))
    monkeypatch.setattr("tempo.ibkr.connect", lambda cfg: fake_ib)
    monkeypatch.setattr("tempo.config.load_config", lambda: SimpleNamespace())
    monkeypatch.setattr(ledger_score, "Ledger", lambda: ledger)
    monkeypatch.setattr(ledger_score, "ibkr_bars", lambda ib, symbol: None)                 # no prices yet: everything must wait
    assert ledger_score.main() == 0
    assert "scores written: 0; still waiting: 3" in capsys.readouterr().out and log == ["disconnected"]


# --- every order tool refuses to run with orders disabled, and does so BEFORE connecting ------------------------------

import tempo.bracket as bracket_tool
import tempo.flatten as flatten_tool
import tempo.kill as kill_tool
import tempo.lifecycle as lifecycle_tool
import tempo.roundtrip as roundtrip_tool

ORDER_TOOLS = [
    (kill_tool, lambda m: m.main()),
    (flatten_tool, lambda m: m.main(None)),
    (lifecycle_tool, lambda m: m.main("SPY", 1)),
    (bracket_tool, lambda m: m.main("SPY", 700.0, None, None)),
    (roundtrip_tool, lambda m: m.main("SPY")),
]


@pytest.mark.parametrize("module,call", ORDER_TOOLS, ids=[m.__name__.split(".")[-1] for m, _ in ORDER_TOOLS])
def test_each_order_tool_refuses_when_orders_are_disabled_before_it_connects(module, call, monkeypatch):
    monkeypatch.setattr(module, "load_config", lambda: SimpleNamespace(readonly=True))
    monkeypatch.setattr(module, "connect", lambda cfg: pytest.fail(f"{module.__name__} connected to the broker with orders disabled"))
    with pytest.raises(RuntimeError, match="IBKR_READONLY=0"):
        call(module)


def test_the_kill_command_reports_failure_in_its_exit_code_and_always_disconnects(monkeypatch, capsys):
    from tempo.health import Check
    log = []
    monkeypatch.setattr(kill_tool, "load_config", lambda: SimpleNamespace(readonly=False))
    monkeypatch.setattr(kill_tool, "connect", lambda cfg: SimpleNamespace(disconnect=lambda: log.append("disconnected")))
    monkeypatch.setattr(kill_tool, "kill", lambda ib, **kw: [Check("flat", True, "ok"), Check("orders", False, "one order still open")])
    assert kill_tool.main() == 1
    out = capsys.readouterr().out
    assert "[OK] flat" in out and "[FAIL] orders" in out and log == ["disconnected"]
    monkeypatch.setattr(kill_tool, "kill", lambda ib, **kw: [Check("flat", True, "ok")])
    assert kill_tool.main() == 0
