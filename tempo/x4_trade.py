"""Daily X4 BTC trader for the PAPER account. Dry run unless X4_LIVE=1 is set in the environment.

Usage: python -m tempo.x4_trade        (cron, once a day, after the 00:00 UTC daily close)

Safety, in order:
  * X4_LIVE must be exactly "1" to send an order. Anything else logs what it WOULD do and sends nothing.
  * X4_SLEEVE_USD (the size of the BTC sleeve) must be set explicitly; there is no default.
  * every order goes through tempo.orders.place: paper-only account check, kill-switch mode, position cap, daily-loss
    limit, duplicate guard and the order journal all apply. A refusal is logged and the job exits non-zero.
  * stale or missing price data stops the job (no silent fallback).
Execution rules that are NOT part of the frozen X4 backtest (and so are stated here): a marketable limit order 0.5% through
the last close with tif IOC, trades smaller than max(2% of the sleeve, 10 USD) are skipped, and the order is sent right
after the daily close instead of one day later.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tempo.x4_signal import X4Signal, compute_signal, describe, fetch_closes

LIVE_ENV, SLEEVE_ENV = "X4_LIVE", "X4_SLEEVE_USD"
CLIENT_ID_OFFSET = 40  # never share a client id with the other Tempo jobs
LIMIT_THROUGH = 0.005
MIN_TRADE_FRAC, MIN_TRADE_USD = 0.02, 10.0
QTY_DECIMALS = 8
LOG_FILE = Path(__file__).resolve().parent.parent / "logs" / "x4.jsonl"


@dataclass(frozen=True)
class Plan:
    action: str  # BUY, SELL or HOLD
    qty: float
    target_qty: float
    held_qty: float
    note: str


def plan_trade(sig: X4Signal, held_qty: float, sleeve_usd: float) -> Plan:
    if sleeve_usd <= 0:
        raise ValueError("sleeve must be positive")
    target = round(sig.target_weight * sleeve_usd / sig.close, QTY_DECIMALS)
    diff = round(target - held_qty, QTY_DECIMALS)
    floor = max(MIN_TRADE_FRAC * sleeve_usd, MIN_TRADE_USD)
    if target == 0 and held_qty > 0:
        if held_qty * sig.close >= MIN_TRADE_USD:
            return Plan("SELL", round(held_qty, QTY_DECIMALS), target, held_qty, "signal off: exit")
        return Plan("HOLD", 0.0, target, held_qty, "signal off, holding only dust")
    if abs(diff) * sig.close < floor:
        return Plan("HOLD", 0.0, target, held_qty, f"difference {abs(diff) * sig.close:,.0f} USD is under the {floor:,.0f} USD floor")
    return Plan("BUY" if diff > 0 else "SELL", abs(diff), target, held_qty, "resize to target")


def limit_price(action: str, close: float, tick: float = 0.25) -> float:
    raw = close * (1 + LIMIT_THROUGH) if action == "BUY" else close * (1 - LIMIT_THROUGH)
    return round(round(raw / tick) * tick, 2)


def build_order(plan: Plan, close: float, tick: float = 0.25):  # type: ignore[no-untyped-def]
    from ib_async import Order

    return Order(action=plan.action, orderType="LMT", totalQuantity=plan.qty, lmtPrice=limit_price(plan.action, close, tick),
                 tif="IOC", outsideRth=True, orderRef="tempo-x4")


def require_fresh(sig: X4Signal, now: datetime) -> None:
    expected = (now.astimezone(timezone.utc).date() - timedelta(days=1)).isoformat()
    if sig.as_of != expected:
        raise RuntimeError(f"price data is stale: last completed day is {sig.as_of}, expected {expected}. Refusing to trade.")


def parse_env(env: dict[str, str]) -> tuple[bool, float | None]:
    live = env.get(LIVE_ENV, "") == "1"
    raw = env.get(SLEEVE_ENV, "").strip()
    sleeve = float(raw) if raw else None
    if live and sleeve is None:
        raise RuntimeError(f"{LIVE_ENV}=1 but {SLEEVE_ENV} is not set: refusing to guess the size of the BTC sleeve.")
    return live, sleeve


def log_line(record: dict, path: Path = LOG_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


def run_once(ib, contract, sig: X4Signal, sleeve_usd: float, live: bool, sender, now: datetime, tick: float = 0.25) -> dict:  # type: ignore[no-untyped-def]
    held = sum(p.position for p in ib.positions() if p.contract.conId == contract.conId)
    plan = plan_trade(sig, held, sleeve_usd)
    record: dict = {"ts": now.isoformat(), "live": live, "signal": asdict(sig), "plan": asdict(plan), "sleeve_usd": sleeve_usd, "sent": False}
    if plan.action != "HOLD" and live:
        trade = sender(ib, contract, build_order(plan, sig.close, tick), reason="x4 daily", close=sig.close)
        record.update(sent=True, order_id=getattr(getattr(trade, "order", None), "orderId", None))
    return record


def main() -> int:  # pragma: no cover - needs the Gateway
    from ib_async import Crypto

    from tempo.account import equity_usd
    from tempo.config import load_config
    from tempo.ibkr import connect
    from tempo.ibutil import default_journal, default_limits
    from tempo.orders import place, record_outcome

    now = datetime.now(timezone.utc)
    live, sleeve = parse_env(dict(os.environ))
    sig = compute_signal(fetch_closes())
    require_fresh(sig, now)
    print(describe(sig, sleeve))
    if sleeve is None:
        print("X4_SLEEVE_USD not set: signal only, no connection to the broker.")
        log_line({"ts": now.isoformat(), "live": False, "signal": asdict(sig), "note": "no sleeve configured"})
        return 0
    cfg = load_config()
    cfg = replace(cfg, client_id=cfg.client_id + CLIENT_ID_OFFSET, readonly=not live)
    ib = connect(cfg)
    try:
        contract = ib.qualifyContracts(Crypto("BTC", "PAXOS", "USD"))[0]
        tick = ib.reqContractDetails(contract)[0].minTick
        journal, limits = default_journal(), default_limits()

        def sender(ib_, contract_, order, *, reason, close):  # type: ignore[no-untyped-def]
            return place(ib_, contract_, order, reason=reason, journal=journal, limits=limits, equity_usd=equity_usd(ib_), ref_price=close, now=now)

        record = run_once(ib, contract, sig, sleeve, live, sender, now, tick)
        print(f"{'LIVE' if live else 'DRY RUN'}: {record['plan']['action']} {record['plan']['qty']} BTC ({record['plan']['note']})")
        if record["sent"]:
            ib.sleep(5)
            for t in ib.trades():
                if t.order.orderId == record["order_id"]:
                    record["outcome"] = record_outcome(journal, t)
                    print(f"outcome: {record['outcome']}")
        log_line(record)
    finally:
        ib.disconnect()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - a failed run must be loud and logged
        log_line({"ts": datetime.now(timezone.utc).isoformat(), "error": repr(exc)})
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1)
