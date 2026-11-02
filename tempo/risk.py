"""Position sizing from risk rules. Pure functions: no IBKR, no I/O except load_rules."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

RULES_FILE = Path(__file__).resolve().parents[1] / "rules.json"


@dataclass(frozen=True)
class RiskRules:
    risk_per_trade_pct: float  # max loss if the stop is hit, as % of equity
    max_position_pct: float  # max position value, as % of equity

    def __post_init__(self) -> None:
        if not 0 < self.risk_per_trade_pct <= 100:
            raise ValueError(f"risk_per_trade_pct must be in (0, 100], got {self.risk_per_trade_pct}")
        if not 0 < self.max_position_pct <= 100:
            raise ValueError(f"max_position_pct must be in (0, 100], got {self.max_position_pct}")


@dataclass(frozen=True)
class SizeResult:
    shares: int
    notional: float
    risk_amount: float  # loss if the stop fills exactly at the stop price
    limited_by: str  # "risk" or "position cap"


def load_rules(path: Path = RULES_FILE) -> RiskRules:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = [k for k in ("risk_per_trade_pct", "max_position_pct") if k not in data]
    if missing:
        raise ValueError(f"{path}: missing {', '.join(missing)}")
    return RiskRules(float(data["risk_per_trade_pct"]), float(data["max_position_pct"]))


def position_size(equity: float, entry: float, stop: float, rules: RiskRules) -> SizeResult:
    """Whole shares for a LONG trade. `equity`, `entry` and `stop` must share one currency."""
    if equity <= 0:
        raise ValueError(f"equity must be positive, got {equity}")
    if entry <= 0 or stop <= 0 or stop >= entry:
        raise ValueError(f"long trade needs 0 < stop < entry, got entry={entry} stop={stop}")
    by_risk = math.floor(equity * rules.risk_per_trade_pct / 100 / (entry - stop))
    by_cap = math.floor(equity * rules.max_position_pct / 100 / entry)
    shares = min(by_risk, by_cap)
    return SizeResult(
        shares=shares,
        notional=shares * entry,
        risk_amount=shares * (entry - stop),
        limited_by="risk" if by_risk < by_cap else "position cap",
    )
