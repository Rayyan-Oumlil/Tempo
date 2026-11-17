"""Shared pieces of the fast-track history study (Workstream F in docs/plan-quant-v2.md, protocol frozen 2026-11-16).

Daily-bar approximation of the live exec_v2 score: enter at the OPEN of the entry day (live: 09:40), exit at the CLOSE `horizon`
sessions later (live: 15:45), excess = direction * (stock return - beta * SPY return) with the same trailing, Blume-shrunk beta as
live (tempo.exec_score.beta_before). A trade with no usable beta or bar has no score; it is counted by the caller, never guessed.

The verdict follows protocol rule 7 exactly: over the test years, KILL when the 95% interval of the net mean has a lower bound at or
below zero; FORWARD only when net t >= 2.8, the net mean is positive in every test year, still positive at 1.5 times the cost,
and there are at least 200 events. History can never promote anything to real money: FORWARD means "worth a forward test".
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from statistics import fmean

from tempo.exec_score import beta_before
from tempo.sequential import hac_variance_of_mean

TEST_YEARS = ("2023", "2024", "2025")
T_BAR = 2.8
MIN_EVENTS = 200
MIN_DAYS = 30
STRESS = 1.5


@dataclass(frozen=True)
class Series:
    """Daily bars. `pos` maps a date to its index so lookups are O(1)."""
    dates: list[str]
    open: list[float]
    close: list[float]
    volume: list[float]
    pos: dict[str, int] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "pos", {d: i for i, d in enumerate(self.dates)})


@dataclass(frozen=True)
class Trade:
    day: str          # entry day (YYYY-MM-DD)
    symbol: str
    gross: float      # signed excess return over the horizon, before costs


def load_series(path: Path) -> Series | None:
    """Bars from a CSV with columns date, open, close, volume (extra columns ignored). None if the file is absent or has no open column."""
    if not path.exists():
        return None
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or "open" not in rows[0]:
        return None
    return Series([r["date"] for r in rows], [float(r["open"]) for r in rows], [float(r["close"]) for r in rows], [float(r["volume"]) for r in rows])


def trade_excess(stock: Series, spy: Series, entry_day: str, direction: int, horizon: int) -> float | None:
    """Signed excess return from the open of `entry_day` to the close `horizon` SPY sessions later; None if a bar or the beta is missing."""
    if entry_day not in stock.pos or entry_day not in spy.pos:
        return None
    k = spy.pos[entry_day]
    if k + horizon >= len(spy.dates):
        return None
    exit_day = spy.dates[k + horizon]
    if exit_day not in stock.pos:
        return None
    beta = beta_before(stock, spy, entry_day)  # type: ignore[arg-type]  # duck-typed: only .dates and .close are read
    if beta is None:
        return None
    stock_ret = stock.close[stock.pos[exit_day]] / stock.open[stock.pos[entry_day]] - 1
    spy_ret = spy.close[k + horizon] / spy.open[k] - 1
    return direction * (stock_ret - beta * spy_ret)


@dataclass(frozen=True)
class Verdict:
    events: int
    days: int
    mean_net: float | None
    ci: tuple[float, float] | None
    t: float | None
    years: dict[str, tuple[int, float]]   # year -> (events, net mean)
    mean_net_stress: float | None
    decision: str                         # KILL, FORWARD, NOT PROVEN or NO VERDICT
    reasons: tuple[str, ...]


def judge(trades: list[Trade], cost: float, horizon: int, years: tuple[str, ...] = TEST_YEARS) -> Verdict:
    """Protocol rule 7 over the test years. Cohorts are entry days; the standard error is Newey-West with lag horizon - 1."""
    test = [t for t in trades if t.day[:4] in years]
    by_day: dict[str, list[float]] = defaultdict(list)
    by_year: dict[str, list[float]] = defaultdict(list)
    for t in test:
        by_day[t.day].append(t.gross)
        by_year[t.day[:4]].append(t.gross)
    year_stats = {y: (len(v), fmean(v) - cost) for y, v in sorted(by_year.items())}
    if len(by_day) < MIN_DAYS:
        return Verdict(len(test), len(by_day), None, None, None, year_stats, None, "NO VERDICT", (f"only {len(by_day)} entry days in the test years (< {MIN_DAYS})",))
    cohort = [fmean(v) for _, v in sorted(by_day.items())]
    gross = fmean(cohort)
    mean_net = gross - cost
    se = math.sqrt(hac_variance_of_mean(cohort, horizon - 1))
    ci = (mean_net - 1.96 * se, mean_net + 1.96 * se)
    t_stat = mean_net / se if se > 0 else None
    stress = gross - STRESS * cost
    if ci[0] <= 0:
        return Verdict(len(test), len(cohort), mean_net, ci, t_stat, year_stats, stress, "KILL",
                       (f"net mean {mean_net:+.2%}, 95% interval [{ci[0]:+.2%}, {ci[1]:+.2%}] reaches zero or below",))
    reasons = []
    if t_stat is None or t_stat < T_BAR:
        reasons.append(f"net t {t_stat:.2f} < {T_BAR}" if t_stat is not None else "no variance")
    missing = [y for y in years if y not in year_stats]
    weak = [y for y, (_, m) in year_stats.items() if m <= 0]
    if missing:
        reasons.append("no events in " + ", ".join(missing))
    if weak:
        reasons.append("net mean not positive in " + ", ".join(weak))
    if stress <= 0:
        reasons.append(f"net mean at {STRESS}x cost is {stress:+.2%}")
    if len(test) < MIN_EVENTS:
        reasons.append(f"{len(test)} events < {MIN_EVENTS}")
    decision = "FORWARD" if not reasons else "NOT PROVEN"
    return Verdict(len(test), len(cohort), mean_net, ci, t_stat, year_stats, stress, decision, tuple(reasons))
