"""Small helpers shared by the order tools."""
from __future__ import annotations

from pathlib import Path

from tempo.journal import Journal
from tempo.orders import Limits
from tempo.risk import load_rules

POLL_SECONDS = 0.5


def wait_until(ib, predicate, timeout: float) -> bool:
    waited = 0.0
    while waited < timeout and not predicate():
        ib.sleep(POLL_SECONDS)
        waited += POLL_SECONDS
    return predicate()


def default_limits(rules_path: Path | None = None) -> Limits:
    rules = load_rules(rules_path) if rules_path else load_rules()
    return Limits(max_position_pct=rules.max_position_pct)


def default_journal() -> Journal:
    return Journal()
