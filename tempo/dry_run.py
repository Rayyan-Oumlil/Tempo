"""D2/D3/D4 dry run: what sizing + the exposure rules WOULD have done with one day's signals. Pure and report-only: no order is sent.

Input rows: {symbol, direction (+1/-1), price, vol20, beta}. A row without vol20 or price is listed as skipped ("no vol20"), never given a guessed
volatility; a sized row without a beta is an error (exposure.beta_exposure refuses it). Sector caps are not checked here: no sector map exists yet.
"""
from __future__ import annotations

from dataclasses import dataclass

from tempo.exposure import Hedge, gross, hedge_order, net, net_within_cap
from tempo.sizing import SizingRules, size_position


@dataclass(frozen=True)
class Plan:
    book: tuple[dict, ...]                 # sized positions: symbol, notional (signed), beta, shares
    skipped: tuple[tuple[str, str], ...]   # (symbol, reason)
    hedge: Hedge | None
    net_ok: bool
    gross: float
    net: float


def plan_day(rows: list[dict], equity: float, rules: SizingRules) -> Plan:
    book: list[dict] = []
    skipped: list[tuple[str, str]] = []
    for r in rows:
        if r.get("vol20") is None or r.get("price") is None:
            skipped.append((r["symbol"], "no vol20" if r.get("vol20") is None else "no price"))
            continue
        s = size_position(equity, r["price"], r["vol20"], rules)
        if s.shares == 0:
            skipped.append((r["symbol"], s.status))
            continue
        book.append({"symbol": r["symbol"], "notional": r["direction"] * s.notional, "beta": r["beta"], "shares": s.shares})
    return Plan(tuple(book), tuple(skipped), hedge_order(book, equity), net_within_cap(book, equity) if book else True, gross(book), net(book))


def render(plan: Plan, equity: float) -> str:
    lines = [f"dry run only, no orders: {len(plan.book)} sized, {len(plan.skipped)} skipped; gross {plan.gross / equity:.0%} net {plan.net / equity:+.1%} of equity"]
    lines.append("net within cap" if plan.net_ok else "NET EXPOSURE ABOVE CAP")
    lines.append(f"SPY hedge: {plan.hedge.side} {plan.hedge.notional:,.0f} USD" if plan.hedge else "SPY hedge: none needed")
    lines += [f"skipped {sym}: {why}" for sym, why in plan.skipped]
    return "\n".join(lines)
