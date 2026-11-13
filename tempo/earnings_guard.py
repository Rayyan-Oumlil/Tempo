"""B3 measurement: would skipping stocks that report earnings inside the holding window have lowered the noise of the NON-earnings sources?

Plan rule: measure the effect on the variance after 30 days, keep the guard only if the variance falls. This module only measures; no source
is changed. Earnings-based sources (earnings_reaction*, claude_earnings) are left out: earnings are their event.

A scored signal "has earnings in its window" when an 8-K item 2.02 for its issuer has a reaction session between the entry date and the exit
date inclusive (a release accepted during the session counts on its own date). Hindsight is fine here: it is a measurement, whereas a live
guard would need an earnings calendar that is known in advance (the next-earnings date is not available from any free source we have).
Read-only; needs SEC_USER_AGENT.   Usage: python -m tempo.earnings_guard
"""
from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date, datetime
from statistics import fmean, stdev

from tempo.earnings_reaction import ET, reaction_day

EXCLUDED_SOURCES = ("earnings_reaction_v1", "earnings_reaction_small_v1", "claude_earnings_v1")
MIN_PER_ARM = 10


def effective_day(accepted: datetime) -> date:
    """The session a release moves the stock: its reaction day, or its own date when it was accepted during the session."""
    return reaction_day(accepted) or accepted.astimezone(ET).date()


def has_earnings(filings: list[datetime], entry_date: str, exit_date: str) -> bool:
    lo, hi = date.fromisoformat(entry_date), date.fromisoformat(exit_date)
    return any(lo <= effective_day(a) <= hi for a in filings)


def split(scores: list[dict], filings_by_symbol: dict[str, list[datetime]]) -> list[dict]:
    """Scores of the non-earnings sources with an `earnings` flag. A symbol absent from the map is an error (unknown, not 'no earnings')."""
    out = []
    for s in scores:
        if s["source"] in EXCLUDED_SOURCES:
            continue
        out.append({**s, "earnings": has_earnings(filings_by_symbol[s["symbol"]], s["entry_date"], s["exit_date"])})   # KeyError if unknown
    return out


def _sd(v: list[float]) -> float | None:
    return stdev(v) if len(v) >= 2 else None


def summarize(rows: list[dict]) -> dict[str, dict]:
    """Per source and horizon, plus ALL: n with earnings, sd of net excess with all trades and without the earnings ones."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[f"{r['source']} h{r['horizon']}"].append(r)
        groups[f"ALL h{r['horizon']}"].append(r)
    out = {}
    for name, rs in sorted(groups.items()):
        kept = [r["net_excess"] for r in rs if not r["earnings"]]
        every = [r["net_excess"] for r in rs]
        out[name] = {"n": len(rs), "n_earnings": len(rs) - len(kept), "mean": fmean(every), "mean_kept": fmean(kept) if kept else None,
                     "sd": _sd(every), "sd_kept": _sd(kept)}
    return out


def verdict(s: dict) -> str:
    if s["n_earnings"] < MIN_PER_ARM or s["n"] - s["n_earnings"] < MIN_PER_ARM:
        return f"too few (need {MIN_PER_ARM} in each arm)"
    if s["sd"] is None or s["sd_kept"] is None:
        return "no spread"
    return "variance falls: keep the guard" if s["sd_kept"] < s["sd"] else "variance does not fall: drop the idea"


def render(summary: dict[str, dict]) -> str:
    def pct(x: float | None) -> str:
        return "-" if x is None else f"{x:+.2%}"
    lines = [f"{'group':34} {'n':>4} {'w/ earn':>7} {'mean':>8} {'mean kept':>10} {'sd':>7} {'sd kept':>8}  verdict"]
    for name, s in summary.items():
        sd = "-" if s["sd"] is None else f"{s['sd']:.2%}"
        sdk = "-" if s["sd_kept"] is None else f"{s['sd_kept']:.2%}"
        lines.append(f"{name:34} {s['n']:>4} {s['n_earnings']:>7} {pct(s['mean']):>8} {pct(s['mean_kept']):>10} {sd:>7} {sdk:>8}  {verdict(s)}")
    if not summary:
        lines.append("no scored signal from a non-earnings source yet")
    lines.append("measurement only (hindsight earnings flag); the plan keeps a guard only if the spread falls after 30 days.")
    return "\n".join(lines)


def main() -> int:  # pragma: no cover - network
    import json

    from tempo import edgar
    from tempo.history_earnings import SUBMISSIONS, earnings_filings
    from tempo.ledger import Ledger
    scores = [r for r in Ledger().scores() if r["source"] not in EXCLUDED_SOURCES]
    mapping = json.loads(edgar.fetch("https://www.sec.gov/files/company_tickers.json"))
    filings: dict[str, list[datetime]] = {}
    unknown: list[str] = []
    for symbol in sorted({r["symbol"] for r in scores}):
        cik = edgar.cik_for(symbol, mapping)
        if cik is None:
            unknown.append(symbol)
            continue
        sub = json.loads(edgar.fetch(SUBMISSIONS.format(cik=int(cik))))
        filings[symbol] = [t for _, t in earnings_filings(sub, lambda name: json.loads(edgar.fetch("https://data.sec.gov/submissions/" + name)),
                                                          first=date(2026, 1, 1), last=date(2027, 12, 31))]
    usable = [r for r in scores if r["symbol"] in filings]
    print(render(summarize(split(usable, filings))))
    if unknown:
        print(f"left out, no SEC ticker match: {len(unknown)} symbol(s) {unknown[:15]}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
