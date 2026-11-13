"""Trade autopsy: why did each closed paper trade win or lose, and where does each signal source lose?

Usage: python -m tempo.autopsy

Two parts, both read-only and deterministic (fixed thresholds below, no tuning):

1. TRADES. Each closed paper trade is joined to the ledger's score for the same signal and horizon, and given ONE cause:
     win / lucky win          paper made money (lucky: the idea itself lost in the ledger)
     market move              paper lost, idea beat the market in the ledger, the market went against it
     wrong idea               paper lost and the ledger says the idea lost too
     execution                idea was right in the ledger, paper lost, and entry slippage was large
     timing                   idea was right in the ledger, paper lost, slippage was small (different entry/exit moments)
     noise                    paper lost, idea right, gap to the ledger small
     unscored                 the ledger has no score at that horizon yet
   plus the average gap between paper and ledger (an estimate of what execution costs) and entry slippage.

2. PATTERNS. Ledger net excess returns split by direction, VIX regime and weekday. A cell is reported as a CANDIDATE PATTERN
   only with at least MIN_CELL scores and a p-value that passes Benjamini-Hochberg at FDR (10%) over all the cells examined (the
   cells overlap and move together, the positive-dependence case BH is valid for; Bonferroni was too strict for about 90 cells).
   A candidate is a question for a challenger (tempo.champion), never a reason to change a rule: it nominates, the pre-registered
   forward test decides.
"""
from __future__ import annotations

import statistics
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from tempo.ledger import Ledger
from tempo.overnight import t_statistic
from tempo.paper_run import HORIZONS, PAPER_FILE, load_state

ROOT = Path(__file__).resolve().parents[1]
VIX_FILE = ROOT / "data" / "snapshots" / "fred" / "VIXCLS.csv"
DEFAULT_HORIZON = 5
GAP_TOL = 0.003         # a paper result more than 30 bps below the ledger's counts as a real gap
SLIP_TOL = 0.002        # entry slippage above 20 bps is blamed on execution
MIN_CELL = 30
VIX_HISTORY = 252
VIX_MIN_HISTORY = 100


@dataclass(frozen=True)
class Trade:
    signal_id: str
    source: str
    symbol: str
    direction: int
    paper_ret: float
    entry_slip: float            # positive = adverse (paid more on a long, sold lower on a short)
    ledger_ret: float | None     # direction-adjusted, from the open of the entry day to the close of the exit day
    ledger_bench: float | None
    ledger_net_excess: float | None


def build_trades(state: dict[str, dict], scores: list[dict]) -> list[Trade]:
    by_key = {(s["signal_id"], s["horizon"]): s for s in scores}
    out: list[Trade] = []
    for sid, st in sorted(state.items()):
        if st.get("status") != "exited" or not st.get("exit_fill_price") or not st.get("fill_price") or not st.get("ref_price"):
            continue
        d = st["direction"]
        source = sid.split(":", 1)[0]
        sc = by_key.get((sid, HORIZONS.get(source, DEFAULT_HORIZON)))
        out.append(Trade(sid, source, st["symbol"], d, d * (st["exit_fill_price"] / st["fill_price"] - 1),
                         d * (st["fill_price"] / st["ref_price"] - 1),
                         sc["ret"] if sc else None, sc["bench_ret"] if sc else None, sc["net_excess"] if sc else None))
    return out


def cause(t: Trade) -> str:
    if t.paper_ret > 0:
        return "win" if t.ledger_ret is None or t.ledger_ret > 0 else "lucky win"
    if t.ledger_ret is None or t.ledger_bench is None or t.ledger_net_excess is None:
        return "unscored"
    if t.ledger_ret <= 0:
        return "market move" if t.ledger_bench < 0 and t.ledger_net_excess >= 0 else "wrong idea"
    if t.paper_ret - t.ledger_ret < -GAP_TOL:
        return "execution" if t.entry_slip > SLIP_TOL else "timing"
    return "noise"


def trade_summary(trades: list[Trade]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for source in sorted({t.source for t in trades}):
        mine = [t for t in trades if t.source == source]
        both = [t for t in mine if t.ledger_ret is not None]
        causes: dict[str, int] = {}
        for t in mine:
            causes[cause(t)] = causes.get(cause(t), 0) + 1
        out[source] = {
            "n": len(mine), "win_rate": sum(t.paper_ret > 0 for t in mine) / len(mine),
            "mean_paper": statistics.fmean(t.paper_ret for t in mine),
            "mean_ledger": statistics.fmean(t.ledger_ret for t in both) if both else None,
            "mean_gap": statistics.fmean(t.paper_ret - t.ledger_ret for t in both) if both else None,   # type: ignore[operator]
            "mean_slip": statistics.fmean(t.entry_slip for t in mine), "causes": causes}
    return out


def load_vix(path: Path = VIX_FILE) -> dict[str, float]:
    if not path.exists():
        return {}
    out: dict[str, float] = {}
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        day, _, value = line.partition(",")
        try:
            out[day] = float(value)
        except ValueError:
            continue    # FRED writes '.' or blank for holidays
    return out


def vix_regime(vix: dict[str, float], day: str) -> str | None:
    """'high' if the VIX on `day` is above the median of the previous VIX_HISTORY readings, 'low' otherwise; None without history."""
    days = sorted(d for d in vix if d <= day)
    if not days or days[-1] != day:
        return None
    past = [vix[d] for d in days[:-1][-VIX_HISTORY:]]
    if len(past) < VIX_MIN_HISTORY:
        return None
    return "high" if vix[day] > statistics.median(past) else "low"


FDR = 0.10


def p_value(t: float) -> float:
    """Two-sided p from a t statistic, normal approximation (the t distribution is wider at small n, so this flatters a little:
    one more reason a candidate is only a nomination)."""
    return 2 * (1 - statistics.NormalDist().cdf(abs(t)))


def bh_threshold(pvals: list[float], q: float = FDR) -> float | None:
    """Benjamini-Hochberg: the largest p-value p_(k) with p_(k) <= k*q/m, or None if none passes (0.0 is a real threshold: a p-value can underflow to zero)."""
    m = len(pvals)
    passing = [p for k, p in enumerate(sorted(pvals), 1) if p <= k * q / m]
    return max(passing) if passing else None


def pattern_cells(signals: list[dict], scores: list[dict], vix: dict[str, float]) -> list[tuple[str, str, list[float]]]:
    sig = {s["signal_id"]: s for s in signals}
    cells: dict[tuple[str, str], list[float]] = {}
    for sc in scores:
        s = sig.get(sc["signal_id"])
        if s is None or sc["horizon"] != HORIZONS.get(s["source"], DEFAULT_HORIZON):
            continue
        dims = [("direction", "long" if s["direction"] == 1 else "short"),
                ("weekday", date.fromisoformat(s["date_et"]).strftime("%a"))]
        regime = vix_regime(vix, s["date_et"])
        if regime:
            dims.append(("vix", regime))
        for dim, value in dims:
            cells.setdefault((s["source"], f"{dim}={value}"), []).append(sc["net_excess"])
    return [(src, label, vals) for (src, label), vals in sorted(cells.items())]


def candidate_patterns(cells: list[tuple[str, str, list[float]]]) -> tuple[list[tuple[str, str, int, float, float]], float, int]:
    """(candidates, BH p threshold, cells examined). Only cells with MIN_CELL scores count as examined."""
    eligible = [c for c in cells if len(c[2]) >= MIN_CELL]
    if not eligible:
        return [], 0.0, 0
    ts = [t_statistic(v) for _, _, v in eligible]
    limit = bh_threshold([p_value(t) for t in ts])
    if limit is None:
        return [], 0.0, len(eligible)
    found = [(src, label, len(v), statistics.fmean(v), t) for (src, label, v), t in zip(eligible, ts) if p_value(t) <= limit]
    return found, limit, len(eligible)


def report(ledger: Ledger | None = None, paper_path: Path = PAPER_FILE, vix_path: Path = VIX_FILE) -> str:
    from tempo.journal import Journal
    ledger = ledger or Ledger()
    state = load_state(Journal(paper_path))
    trades = build_trades(state, ledger.scores())
    lines = [f"TRADE AUTOPSY: {len(trades)} closed paper trades"]
    skipped = [s for s in state.values() if s["status"] in ("skipped", "missed")]
    lines.append(f"  not traded: {sum(s['status'] == 'missed' for s in skipped)} missed, {sum(s['status'] == 'skipped' for s in skipped)} skipped")
    summary = trade_summary(trades)
    if not summary:
        lines.append("  no closed trades yet: nothing to learn from. The first exits arrive with the first 5-day horizons.")
    for source, s in summary.items():
        gap = "n/a" if s["mean_gap"] is None else f"{s['mean_gap']:+.2%}"
        led = "n/a" if s["mean_ledger"] is None else f"{s['mean_ledger']:+.2%}"
        lines.append(f"  {source}: n={s['n']}, win rate {s['win_rate']:.0%}, paper {s['mean_paper']:+.2%} vs ledger {led} "
                     f"(gap {gap}), entry slippage {s['mean_slip']:+.3%}; causes {s['causes']}")
    cells = pattern_cells(ledger.signals(), ledger.scores(), load_vix(vix_path))
    found, bar, examined = candidate_patterns(cells)
    lines.append(f"PATTERNS: {examined} cells with at least {MIN_CELL} scores examined; Benjamini-Hochberg at {FDR:.0%} FDR, a cell passes if p <= {bar:.4f}")
    lines += [f"  CANDIDATE {src} {label}: n={n}, mean net excess {mean:+.2%}, t={t:.2f}" for src, label, n, mean, t in found]
    if not found:
        lines.append("  none. Nothing in the data justifies a challenger yet.")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    try:
        print(report())
    except (OSError, ValueError, KeyError) as err:
        print(f"[FAIL] {type(err).__name__}: {err}", file=sys.stderr)
        raise SystemExit(1)
