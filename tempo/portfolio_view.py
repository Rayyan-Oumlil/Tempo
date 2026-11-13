"""A5 portfolio view: the daily return of an equal-risk blend of all sources, the correlation between sources, and how many
independent bets that really is. Built on the exec_v2 scores (net excess after the source's registered cost).

APPROXIMATION, stated on purpose: scores carry entry and exit prices only, not a daily mark-to-market. Each trade's net excess is
spread evenly over the trading days it was open (entry day through exit day), and a source's daily return is the plain mean of its
open trades' daily shares (equal weight per trade, not dollars). A source with no open trade on a day contributes 0 that day (it is
flat). The blend weights each source by 1 / (its daily standard deviation on days it was open): equal RISK, with the whole sample's
volatility, so it is descriptive and must not be read as a tradeable weight. This is a guide, not a pre-registered test.

Effective number of bets = N^2 / sum of squared correlations (the participation ratio of the correlation matrix's eigenvalues: 1 when
every source moves together, N when none do).
Read-only. Usage: python -m tempo.portfolio_view
"""
from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date, timedelta
from itertools import combinations
from statistics import fmean, pstdev

from tempo.hours import is_trading_day

MIN_DAYS = 10           # a source with fewer open days has no volatility or correlation yet
MIN_OVERLAP = 10        # days two sources were both open before a correlation is shown


def trading_days(first: str, last: str) -> list[str]:
    d, end, out = date.fromisoformat(first), date.fromisoformat(last), []
    while d <= end:
        if is_trading_day(d):
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def daily_returns(scores: list[dict]) -> dict[str, dict[str, float]]:
    """source -> {day: mean over open trades of net_excess / days open}. Only days with at least one open trade appear."""
    shares: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for s in scores:
        days = trading_days(s["entry_date"], s["exit_date"])
        if not days:
            raise ValueError(f"{s['signal_id']}: no trading day between {s['entry_date']} and {s['exit_date']}")
        for day in days:
            shares[s["source"]][day].append(s["net_excess"] / len(days))
    return {src: {d: fmean(v) for d, v in sorted(by_day.items())} for src, by_day in sorted(shares.items())}


def correlation(a: dict[str, float], b: dict[str, float]) -> float | None:
    common = sorted(set(a) & set(b))
    if len(common) < MIN_OVERLAP:
        return None
    x, y = [a[d] for d in common], [b[d] for d in common]
    sx, sy = pstdev(x), pstdev(y)
    if sx == 0 or sy == 0:
        return None
    mx, my = fmean(x), fmean(y)
    return sum((p - mx) * (q - my) for p, q in zip(x, y)) / len(x) / (sx * sy)


def effective_bets(corr: dict[tuple[str, str], float | None], names: list[str]) -> float | None:
    """N^2 / sum of squared correlations over all ordered pairs. None if any pair has no correlation yet (never assume 0)."""
    if len(names) < 2:
        return None
    total = float(len(names))                                       # the diagonal
    for a, b in combinations(names, 2):
        r = corr.get((a, b))
        if r is None:
            return None
        total += 2 * r * r
    return len(names) ** 2 / total


def blend(series: dict[str, dict[str, float]]) -> tuple[dict[str, float], dict[str, float]]:
    """(weights, daily blend). Weight of source i = (1 / sd_i) / sum(1 / sd_j), over sources open at least MIN_DAYS days with sd > 0."""
    inv = {s: 1 / pstdev(list(r.values())) for s, r in series.items() if len(r) >= MIN_DAYS and pstdev(list(r.values())) > 0}
    if not inv:
        return {}, {}
    total = sum(inv.values())
    weights = {s: v / total for s, v in inv.items()}
    days = sorted({d for s in weights for d in series[s]})
    return weights, {d: sum(weights[s] * series[s].get(d, 0.0) for s in weights) for d in days}


def render(series: dict[str, dict[str, float]]) -> str:
    weights, daily = blend(series)
    lines = [f"{'source':26} {'open days':>9} {'cum net excess':>14} {'daily sd':>9} {'weight':>7}"]
    for s, r in series.items():
        sd = pstdev(list(r.values())) if len(r) > 1 else 0.0
        w = f"{weights[s]:.0%}" if s in weights else "-"
        lines.append(f"{s:26} {len(r):>9} {sum(r.values()):>+14.2%} {sd:>9.2%} {w:>7}")
    if daily:
        lines.append(f"{'BLEND (equal risk)':26} {len(daily):>9} {sum(daily.values()):>+14.2%} {pstdev(list(daily.values())):>9.2%} {'100%':>7}")
    else:
        lines.append(f"no source has {MIN_DAYS} open days yet: no blend, no correlations")
    names = list(weights)
    corr = {(a, b): correlation(series[a], series[b]) for a, b in combinations(names, 2)}
    if len(names) >= 2:
        lines.append("")
        lines.append("correlation of daily returns (days both open >= %d):" % MIN_OVERLAP)
        for a, b in combinations(names, 2):
            rho = corr[(a, b)]
            lines.append(f"  {a} / {b}: {'not enough common days' if rho is None else f'{rho:+.2f}'}")
        n_eff = effective_bets(corr, names)
        lines.append(f"effective independent bets: {'n/a (a pair has too few common days)' if n_eff is None else f'{n_eff:.1f}'} of {len(names)} sources")
    lines.append("net excess after the registered cost, trades spread evenly over their open days (see module note); weights are descriptive.")
    return "\n".join(lines)


def main() -> int:  # pragma: no cover - entry point
    from tempo.ledger import Ledger
    from tempo.tradeable import tradeable_scores
    ledger = Ledger()
    kept, _ = tradeable_scores(ledger.signals(), ledger.scores())
    print(render(daily_returns(kept)))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
