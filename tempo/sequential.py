"""A2 sequential evidence report: for each (source, horizon), what do the exec_v2 scores say, and how sure can we be?

Observations are ENTRY-DAY COHORTS: the mean net excess return of all trades whose entry day is the same, so one number per day
(trades entered together share the market that day). Holding periods overlap, so neighbouring cohorts are correlated: the
standard error uses Newey-West (Bartlett weights, lag = horizon - 1), never the naive sigma/sqrt(n).

Reported per row: n trades, n cohort days, mean net excess, HAC standard error and 95% interval, t-statistic, minimum detectable
effect at 80% power (2.8 x SE), cohort days still needed to detect a +1% mean, an always-valid p-value (mSPRT) and a deflated
Sharpe ratio across all rows (Bailey and Lopez de Prado), which charges for having looked at several sources and uses the
effective (overlap-corrected) number of days, not the raw count.

APPROXIMATION, stated on purpose: the plan's ideal is mSPRT on the book's daily mark-to-market return. Scores carry only entry and
exit prices, so this runs on cohort means with the variance replaced by its HAC estimate (an effective-sample-size correction for
the overlap). It is a guide, not the pre-registered pass test; the registered rule for each source still decides.

Read-only. Usage: python -m tempo.sequential
"""
from __future__ import annotations

import math
import sys
from collections import defaultdict
from dataclasses import dataclass, replace
from statistics import NormalDist, mean, pstdev, variance

from tempo.ledger import Ledger

N = NormalDist()
MIN_DAYS = 10            # fewer cohort days than this: no interval or p-value is shown
TAU = 0.01               # mSPRT prior scale for the mean net excess per cohort day: effects of about 1% are what we test for
TARGET = 0.01
Z_POWER = 2.8            # 1.96 + 0.84: 5% two-sided test at 80% power


def cohorts(scores: list[dict]) -> dict[tuple[str, int], list[tuple[str, float, int]]]:
    """(source, horizon) -> [(entry_date, mean net_excess, trades)] in date order."""
    by: dict[tuple[str, int], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for s in scores:
        by[(s["source"], s["horizon"])][s["entry_date"]].append(s["net_excess"])
    return {k: [(d, mean(v), len(v)) for d, v in sorted(days.items())] for k, days in by.items()}


def hac_variance_of_mean(x: list[float], lag: int) -> float:
    """Newey-West (Bartlett) variance of the sample mean."""
    n = len(x)
    m = mean(x)
    d = [v - m for v in x]
    lag = min(lag, n - 1)
    s = sum(v * v for v in d) / n
    for k in range(1, lag + 1):
        s += 2 * (1 - k / (lag + 1)) * sum(d[i] * d[i - k] for i in range(k, n)) / n
    return max(s, 1e-12) / n


def msprt_p(x: list[float], lag: int, tau: float = TAU) -> float:
    """Always-valid p-value: 1 / the running maximum of the mixture likelihood ratio, with the per-observation variance set to n x HAC
    variance of the mean (so overlap shrinks the effective sample), re-estimated on every prefix. Never above 1."""
    best = 1.0
    for k in range(MIN_DAYS, len(x) + 1):
        pre = x[:k]
        sigma2 = k * hac_variance_of_mean(pre, lag)
        xbar = mean(pre)
        v = sigma2 + k * tau * tau
        log_l = 0.5 * math.log(sigma2 / v) + (k * k * tau * tau * xbar * xbar) / (2 * sigma2 * v)
        best = max(best, math.exp(min(log_l, 700)))
    return min(1.0, 1.0 / best)


def effective_n(x: list[float], lag: int) -> float:
    """Independent observations the series is worth: n shrinks by the ratio of the HAC to the naive variance of the mean."""
    n = len(x)
    naive = pstdev(x) ** 2 / n
    return max(2.0, min(float(n), n * naive / hac_variance_of_mean(x, lag)))


def sharpe_stats(x: list[float]) -> tuple[float, float, float]:
    m, sd = mean(x), pstdev(x)
    if sd == 0:
        return 0.0, 0.0, 3.0
    z = [(v - m) / sd for v in x]
    return m / sd, sum(v ** 3 for v in z) / len(z), sum(v ** 4 for v in z) / len(z)


def deflated_sharpe(sr: float, n: float, skew: float, kurt: float, sr_all: list[float]) -> float | None:
    """Probability that the true Sharpe exceeds the best you would expect from pure luck among len(sr_all) tries. None if < 2 tries."""
    k = len(sr_all)
    if k < 2 or n < 3:
        return None
    g = 0.5772156649
    sr0 = math.sqrt(variance(sr_all)) * ((1 - g) * N.inv_cdf(1 - 1 / k) + g * N.inv_cdf(1 - 1 / (k * math.e)))
    denom = 1 - skew * sr + (kurt - 1) / 4 * sr * sr
    if denom <= 0:
        return None
    return N.cdf((sr - sr0) * math.sqrt(n - 1) / math.sqrt(denom))


@dataclass(frozen=True)
class Evidence:
    source: str
    horizon: int
    trades: int
    days: int
    mean: float
    ci: tuple[float, float] | None = None
    t: float | None = None
    mde: float | None = None
    days_needed: int | None = None
    p: float | None = None
    sharpe: float | None = None
    dsr: float | None = None


def analyse(scores: list[dict]) -> list[Evidence]:
    rows: list[Evidence] = []
    stats: dict[int, tuple[float, float, float]] = {}
    neff: dict[int, float] = {}
    for (source, horizon), days in sorted(cohorts(scores).items()):
        x = [m for _, m, _ in days]
        base = Evidence(source, horizon, sum(c for _, _, c in days), len(x), mean(x))
        if len(x) >= MIN_DAYS:
            lag = max(horizon - 1, 0)
            se = math.sqrt(hac_variance_of_mean(x, lag))
            stats[len(rows)] = sharpe_stats(x)
            neff[len(rows)] = effective_n(x, lag)
            base = replace(base, ci=(base.mean - 1.96 * se, base.mean + 1.96 * se), t=base.mean / se, mde=Z_POWER * se,
                           days_needed=math.ceil((Z_POWER * se * math.sqrt(len(x)) / TARGET) ** 2), p=msprt_p(x, lag),
                           sharpe=stats[len(rows)][0])
        rows.append(base)
    srs = [sr for sr, _, _ in stats.values()]
    for i, (sr, skew, kurt) in stats.items():
        rows[i] = replace(rows[i], dsr=deflated_sharpe(sr, neff[i], skew, kurt, srs))
    return rows


def render(rows: list[Evidence]) -> str:
    head = f"{'source':22} {'h':>3} {'trades':>6} {'days':>4} {'mean net':>9} {'95% interval':>17} {'t':>5} {'MDE':>6} {'days for 1%':>11} {'always-valid p':>14} {'DSR':>5}"
    out = [head]
    for r in rows:
        if r.ci is None or r.t is None or r.mde is None or r.p is None:
            out.append(f"{r.source:22} {r.horizon:>3} {r.trades:>6} {r.days:>4} {r.mean:>+9.2%}   (fewer than {MIN_DAYS} cohort days: no interval yet)")
            continue
        dsr = "-" if r.dsr is None else f"{r.dsr:.2f}"
        out.append(f"{r.source:22} {r.horizon:>3} {r.trades:>6} {r.days:>4} {r.mean:>+9.2%} "
                   f"[{r.ci[0]:+.2%},{r.ci[1]:+.2%}] {r.t:>5.1f} {r.mde:>6.2%} {r.days_needed:>11} {r.p:>14.3f} {dsr:>5}")
    out.append("net excess after the source's registered cost; cohort = trades sharing an entry day; HAC lag = horizon - 1; "
               "p is approximate (see module note); the registered pass rule still decides.")
    return "\n".join(out)


def main() -> int:  # pragma: no cover - entry point
    from tempo.tradeable import tradeable_scores
    ledger = Ledger()
    from tempo.hygiene import clean_view
    signals = ledger.signals()
    kept, excluded = tradeable_scores(signals, ledger.scores())
    print(render(analyse(kept + clean_view(signals, kept))))
    if excluded:
        print("left out, short with no shares to borrow: " + ", ".join(f"{k} {v}" for k, v in sorted(excluded.items())))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
