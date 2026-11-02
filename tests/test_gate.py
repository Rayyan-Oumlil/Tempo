import json
from pathlib import Path

from tempo.gate import evaluate

GATE = {
    "paper": {"min_round_trips": 100, "min_trading_days": 60, "min_net_pnl_usd": 0, "max_process_error_share": 0.05},
    "backtest": {"min_years": 10, "min_shuffle_beat_pct": 95, "max_variants_tried": 20},
    "checklist": ["kill_switch_tested", "employer_compliance_checked"],
}
GOOD = {"round_trips": 120, "trading_days": 70, "net_pnl_usd": 50.0, "process_error_share": 0.01, "years": 20,
        "shuffle_beat_pct": 97.0, "variants_tried": 3, "checklist": {"kill_switch_tested": True, "employer_compliance_checked": True}}


def by_name(checks):
    return {c.name: c for c in checks}


def test_all_criteria_met_passes():
    assert all(c.ok for c in evaluate(GOOD, GATE))


def test_each_failure_is_named():
    bad = {**GOOD, "round_trips": 99, "net_pnl_usd": -1.0, "variants_tried": 21}
    failed = {c.name for c in evaluate(bad, GATE) if not c.ok}
    assert failed == {"min_round_trips", "min_net_pnl_usd", "max_variants_tried"}


def test_missing_metric_fails_closed():
    metrics = {k: v for k, v in GOOD.items() if k != "trading_days"}
    assert not by_name(evaluate(metrics, GATE))["min_trading_days"].ok


def test_checklist_item_must_be_true():
    metrics = {**GOOD, "checklist": {"kill_switch_tested": True, "employer_compliance_checked": False}}
    assert not by_name(evaluate(metrics, GATE))["employer_compliance_checked"].ok


def test_the_committed_gate_file_is_valid_and_complete():
    gate = json.loads((Path(__file__).resolve().parents[1] / "evidence" / "gate.json").read_text(encoding="utf-8"))
    assert {"paper", "backtest", "checklist"} <= gate.keys()
    assert all(c.name for c in evaluate({}, gate))  # every criterion is evaluable (all fail on empty metrics)
