"""Daily snapshot of SPY and QQQ option implied volatility from IBKR (free delayed data), for the volatility-premium shadow test.

Usage: python -m tempo.option_snapshot      after the close (the late job runs it); needs Gateway; saves once per day.

Also rewrites data/snapshots/vol_series/{SPY,QQQ}_{IV,HV}.csv, IBKR's own 30-day implied and historical volatility series
(5 years, so the volatility-premium history exists from day one; this is the reliable part).
Writes data/snapshots/options/YYYYMMDD.json, best effort: for each underlying, the spot, the 20-day realised volatility, and for three
expiries (about 7, 30 and 60 days out) the calls and puts at the money and 5% either side: implied volatility, delta,
last, close, bid, ask (last and close are delayed and often stale: the implied volatility is the product). The point is a point-in-time history: implied minus realised volatility can be studied (and a
defined-risk spread tracked on paper) once a few months exist. Nothing is traded.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Sequence
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data" / "snapshots" / "options"
SERIES_FOLDER = ROOT / "data" / "snapshots" / "vol_series"
UNDERLYINGS = ("SPY", "QQQ")
TARGET_DTE = (7, 30, 60)
STRIKE_OFFSETS = (-0.05, 0.0, 0.05)
MIN_VALID_SHARE = 0.8        # of the at-the-money contracts expected to carry an implied volatility (a warning, not a failure, below it)
ET = ZoneInfo("America/New_York")


def pick_expiries(expirations: Sequence[str], today: date, targets: Sequence[int] = TARGET_DTE) -> list[str]:
    """The listed expiry nearest to each target number of days (expiries today or earlier are ignored), without repeats."""
    future = sorted({e for e in expirations if (datetime.strptime(e, "%Y%m%d").date() - today).days >= 1})
    picked: list[str] = []
    for target in targets:
        if not future:
            break
        best = min(future, key=lambda e: abs((datetime.strptime(e, "%Y%m%d").date() - today).days - target))
        if best not in picked:
            picked.append(best)
    return picked


def pick_strikes(strikes: Sequence[float], spot: float, offsets: Sequence[float] = STRIKE_OFFSETS) -> list[float]:
    wide = [s for s in strikes if s % 5 == 0] or list(strikes)   # 5-point strikes are listed at every expiry; odd ones often are not
    out: list[float] = []
    for off in offsets:
        k = min(wide, key=lambda s: abs(s - spot * (1 + off)))
        if k not in out:
            out.append(k)
    return out


def realized_vol(closes: Sequence[float], n: int = 20) -> float | None:
    """Annualised standard deviation of the last n daily log returns, or None without n+1 closes."""
    if len(closes) < n + 1:
        return None
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(len(closes) - n, len(closes))]
    mean = sum(rets) / n
    return math.sqrt(sum((r - mean) ** 2 for r in rets) / (n - 1)) * math.sqrt(252)


def good(value) -> float | None:
    """A usable number from an IBKR tick, or None (IBKR uses -1, nan and None for 'no value')."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v > 0 else None


def valid_share(records: Sequence[dict]) -> float:
    return sum(1 for r in records if r["iv"] is not None) / len(records) if records else 0.0


def series_csv(bars) -> str:
    """Daily bars of an IBKR volatility series as 'date,value' lines (the close of each bar)."""
    lines = ["date,value", *(f"{b.date},{float(b.close):.6f}" for b in bars)]
    return "\n".join(lines) + "\n"


def collect_vol_series(ib, folder: Path = SERIES_FOLDER, duration: str = "5 Y") -> dict[str, int]:  # pragma: no cover - IBKR
    """30-day implied (OPTION_IMPLIED_VOLATILITY) and historical volatility of SPY and QQQ, whole history rewritten each run."""
    from ib_async import Stock
    folder.mkdir(parents=True, exist_ok=True)
    rows: dict[str, int] = {}
    for name in UNDERLYINGS:
        stock = Stock(name, "SMART", "USD")
        ib.qualifyContracts(stock)
        for what, tag in (("OPTION_IMPLIED_VOLATILITY", "IV"), ("HISTORICAL_VOLATILITY", "HV")):
            bars = ib.reqHistoricalData(stock, "", duration, "1 day", what, useRTH=True, formatDate=1)
            if not bars or len(bars) < 200:
                raise RuntimeError(f"{name} {what}: IBKR returned {len(bars or [])} bars")
            partial = folder / f"{name}_{tag}.partial"
            partial.write_text(series_csv(bars), encoding="utf-8")
            partial.replace(folder / f"{name}_{tag}.csv")
            rows[f"{name}_{tag}"] = len(bars)
    return rows


def run(now: datetime, ib, folder: Path = FOLDER, say=print) -> int:  # pragma: no cover - glue, exercised live
    from ib_async import Option, Stock

    from tempo.daybars import day_bars
    from tempo.hours import is_trading_day
    day = now.astimezone(ET).date()
    target = folder / f"{day:%Y%m%d}.json"
    if not is_trading_day(day):
        say(f"option snapshot: {day} is not a trading day; nothing to do")
        return 0
    say(f"volatility series refreshed (bars): {collect_vol_series(ib)}")   # the robust part: whole history, every run
    if target.exists():
        say(f"option snapshot: {target.name} already saved")
        return 0
    if now.astimezone(ET).time() < datetime.strptime("16:20", "%H:%M").time():
        say("not recording: option snapshots are taken after the close (16:20 ET)")
        return 0
    ib.reqMarketDataType(3)
    out: dict[str, dict] = {}
    for name in UNDERLYINGS:
        stock = Stock(name, "SMART", "USD")
        ib.qualifyContracts(stock)
        bars = day_bars(ib, name, "2 M")
        if bars is None or day.isoformat() not in bars.dates:
            raise RuntimeError(f"no daily bar for {name} on {day}")
        spot = bars.close[bars.dates.index(day.isoformat())]
        chain = next((c for c in ib.reqSecDefOptParams(name, "", "STK", stock.conId) if c.exchange == "SMART" and c.tradingClass == name), None)
        if chain is None:
            raise RuntimeError(f"no SMART option chain for {name}")
        wanted = pick_strikes(sorted(chain.strikes), spot)
        atm_strike = min(wanted, key=lambda k: abs(k - spot))
        contracts = [Option(name, e, k, r, "SMART") for e in pick_expiries(chain.expirations, day) for k in wanted for r in ("C", "P")]
        contracts = [c for c in ib.qualifyContracts(*contracts) if c is not None and c.conId]   # unlisted strikes come back as None
        tickers = [ib.reqMktData(c, "106", False, False) for c in contracts]
        ib.sleep(8)
        records = []
        for c, t in zip(contracts, tickers):
            g = t.modelGreeks
            records.append({"expiry": c.lastTradeDateOrContractMonth, "strike": c.strike, "right": c.right, "atm": c.strike == atm_strike,
                            "iv": good(t.impliedVolatility) or (good(g.impliedVol) if g else None), "delta": float(g.delta) if g and g.delta is not None and math.isfinite(g.delta) else None,
                            "last": good(t.last), "close": good(t.close), "bid": good(t.bid), "ask": good(t.ask)})
            ib.cancelMktData(c)
        share = valid_share([r for r in records if r["atm"]])
        if share < MIN_VALID_SHARE:   # the delayed per-contract tick is intermittent: keep what came, say so, never fail the job
            say(f"warning: {name}: only {share:.0%} of the at-the-money contracts carried an implied volatility (delayed ticks are patchy)")
        out[name] = {"spot": spot, "rv20": realized_vol(bars.close), "atm_iv_share": share, "contracts": records}
        say(f"{name}: spot {spot}, rv20 {out[name]['rv20']:.3f}, {len(records)} contracts, {share:.0%} of at-the-money with implied vol, {valid_share(records):.0%} overall")
    folder.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".partial")
    partial.write_text(json.dumps({"date": day.isoformat(), "taken_at_et": now.astimezone(ET).isoformat(), "data": out}), encoding="utf-8")
    partial.replace(target)
    say(f"saved {target.name}")
    return 0


def main() -> int:  # pragma: no cover - entry point
    from dotenv import load_dotenv

    from tempo.config import load_config
    from tempo.ibkr import connect

    load_dotenv()
    ib = connect(load_config())
    ib.RequestTimeout = 30
    try:
        return run(datetime.now(ET), ib)
    finally:
        ib.disconnect()


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    try:
        raise SystemExit(main())
    except Exception as err:  # noqa: BLE001 - fail loudly with a clear line, non-zero exit
        print(f"[FAIL] {type(err).__name__}: {err}", file=sys.stderr)
        raise SystemExit(1)
