"""D2/D3/D4 dry run: what sizing + the exposure rules WOULD have done with one day's signals. Pure and report-only: no order is sent.

Input rows: {symbol, direction (+1/-1), price, vol20, beta}. A row without vol20 or price is listed as skipped ("no vol20"), never given a guessed
volatility; a sized row without a beta is an error (exposure.beta_exposure refuses it). Sector caps are not checked here: no sector map exists yet.

Usage (needs Gateway, client id 92): python -m tempo.dry_run [YYYY-MM-DD]   signals of that ET date (default: latest), TARGET_RISK_PCT below is a proposal.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable

from tempo.exposure import Hedge, gross, hedge_order, net, net_within_cap
from tempo.sizing import SizingRules, size_position

TARGET_RISK_PCT = 0.3   # PROPOSED, not yet chosen by the owner
FLOOR_PCT = 1.0


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


def rows_from_signals(signals: list[dict], beta_of: Callable[[str], float | None]) -> tuple[list[dict], list[tuple[str, str]]]:
    """Plan rows from ledger signals. A symbol with no beta is left out and named, never given beta 1."""
    rows, skipped = [], []
    for s in signals:
        beta = beta_of(s["symbol"])
        if beta is None:
            skipped.append((s["symbol"], "no beta (too little history)"))
            continue
        rows.append({"symbol": s["symbol"], "direction": s["direction"], "price": s.get("price"),
                     "vol20": s.get("features", {}).get("vol20"), "beta": beta})
    return rows, skipped


def main(argv: list[str]) -> int:  # pragma: no cover - needs Gateway
    import dataclasses

    from dotenv import load_dotenv

    from tempo.account import equity_usd
    from tempo.config import load_config
    from tempo.exec_score import beta_before
    from tempo.ibkr import connect
    from tempo.ledger import Ledger
    from tempo.ledger_score import ibkr_bars
    from tempo.tradeable import untradeable_reason
    load_dotenv()
    signals = [s for s in Ledger().signals() if untradeable_reason(s) is None]
    day = argv[0] if argv else max((s["date_et"] for s in signals), default=None)
    signals = [s for s in signals if s["date_et"] == day]
    ib = connect(dataclasses.replace(load_config(), client_id=92))
    ib.RequestTimeout = 60
    try:
        spy, cache = ibkr_bars(ib, "SPY"), {}
        if spy is None:
            raise RuntimeError("no SPY daily bars")
        equity = equity_usd(ib)

        def beta_of(symbol: str) -> float | None:
            if symbol not in cache:
                cache[symbol] = ibkr_bars(ib, symbol)
            stock = cache[symbol]
            return beta_before(stock, spy, "9999-99-99") if stock else None
        rows, no_beta = rows_from_signals(signals, beta_of)
    finally:
        ib.disconnect()
    plan = plan_day(rows, equity, SizingRules(TARGET_RISK_PCT, FLOOR_PCT))
    print(f"signals of {day}: {len(signals)}, equity {equity:,.0f}")
    print(render(Plan(plan.book, plan.skipped + tuple(no_beta), plan.hedge, plan.net_ok, plan.gross, plan.net), equity))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main(sys.argv[1:]))
