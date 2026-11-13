"""C1 kill filter: does the live short_volume_v1 rule have any gross 5-day drift on history? Legs are judged separately.

Window: 2018-08 to 2025-12. FINRA publishes the CONSOLIDATED daily short-volume file (the series the live rule uses) only from about
late July 2018; before that there are per-venue files, a different series, so the plan's "since 2009" is not reachable honestly.

The live rule is reused, not copied: tempo.short_volume.zscores / candidates, tempo.daybars.liquid. Per signal day t:
  universe   S&P 500 members on t (point-in-time list fja05680/sp500, "Updated" file, delisted names included)
  baseline   the 20 previous sessions that have a FINRA file; z of today's short ratio against them
  picks      the first N_EACH names per side among the 30 most extreme that pass the liquidity filter (price >= 5, 20-day ADV >= 5M)
  entry      open of session t+1, exit close of session t+5 (live: 09:40 bar open to 15:45 bar open; the daily bars have no 5-minute data)
  drift      direction x (stock return - SPY return) over the same open-to-close window, gross, beta taken as 1
Survivorship, stated: IBKR serves no bars for delisted names, so those members drop out. The share of member-days lost is printed. That
flatters the long leg and understates the short leg; the rule is a KILL filter only (plan C2/C1): a pass proves nothing.
A leg is killed when its mean gross drift is below the source's registered 20 bps cost; the source is dropped only if BOTH legs are.

Usage (VPS; FINRA needs no Gateway, bars do; resumable, cached under data/history/shortvol):
  python -m tempo.history_shortvol fetch
  python -m tempo.history_shortvol report
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from statistics import fmean
from typing import Callable, Mapping

from tempo.daybars import DayBars, liquid
from tempo.history_earnings import judge
from tempo.short_volume import BASELINE_DAYS, N_EACH, ROUND_TRIP_COST, candidates, zscores

ROOT = Path(__file__).resolve().parents[1]
HIST = ROOT / "data" / "history" / "shortvol"
FIRST, LAST = date(2018, 8, 1), date(2025, 12, 31)
HORIZON = 5
MEMBERS_URL = "https://raw.githubusercontent.com/fja05680/sp500/master/S%26P%20500%20Historical%20Components%20%26%20Changes%20%28Updated%29.csv"
FinraDay = Mapping[str, tuple[float, float]]


@dataclass(frozen=True)
class Ohlc:
    dates: list[str]
    open: list[float]
    close: list[float]
    volume: list[float]

    def daybars(self) -> DayBars:
        return DayBars(self.dates, self.close, self.volume)


# ---- membership --------------------------------------------------------------------------------------------------------------

def parse_members(text: str) -> list[tuple[str, frozenset[str]]]:
    """[(date, tickers)] in date order from the 'date,tickers' file. Refuses an empty file, a bad header or an unsorted one."""
    csv.field_size_limit(10 ** 9)
    rows = list(csv.DictReader(text.splitlines()))
    if not rows or set(rows[0]) != {"date", "tickers"}:
        raise ValueError("membership file: expected columns date,tickers")
    out = [(r["date"], frozenset(t.strip() for t in r["tickers"].split(",") if t.strip())) for r in rows]
    if [d for d, _ in out] != sorted(d for d, _ in out):
        raise ValueError("membership file is not in date order")
    return out


def members_on(history: list[tuple[str, frozenset[str]]], day: str) -> frozenset[str]:
    """The list in force on `day` (the latest row dated on or before it). Before the first row there is no answer: an error, not empty."""
    current = [t for d, t in history if d <= day]
    if not current:
        raise ValueError(f"no membership row on or before {day}")
    return current[-1]


# ---- one signal day ----------------------------------------------------------------------------------------------------------

def pick_day(day: str, today: FinraDay, past: list[FinraDay], members: frozenset[str],
             bars: Callable[[str], Ohlc | None], n_each: int = N_EACH) -> tuple[list[tuple[str, int, float]], dict[str, int]]:
    """([(symbol, direction, z)], counts) exactly as the live rule picks: candidates by z, then the first n_each liquid ones per side."""
    z = zscores(today, past, sorted(members))
    longs, shorts = candidates(z)
    counts = {"members": len(members), "no_bars": 0, "illiquid": 0}
    picks: list[tuple[str, int, float]] = []
    for side, direction in ((longs, 1), (shorts, -1)):
        kept = 0
        for symbol in side:
            if kept == n_each:
                break
            b = bars(symbol)
            if b is None:
                counts["no_bars"] += 1
                continue
            if liquid(b.daybars(), day)["status"] != "ok":
                counts["illiquid"] += 1
                continue
            picks.append((symbol, direction, z[symbol]))
            kept += 1
    return picks, counts


def outcome(stock: Ohlc, spy: Ohlc, day: str, direction: int, horizon: int = HORIZON) -> float | None:
    """direction x (stock - SPY) from the open of the session after `day` to the close `horizon` sessions after `day`. None if a bar is missing."""
    if day not in spy.dates:
        return None
    j = spy.dates.index(day)
    if j + horizon >= len(spy.dates):
        return None
    entry, exit_ = spy.dates[j + 1], spy.dates[j + horizon]
    if entry not in stock.dates or exit_ not in stock.dates:
        return None
    s0, s1 = stock.open[stock.dates.index(entry)], stock.close[stock.dates.index(exit_)]
    b0, b1 = spy.open[j + 1], spy.close[j + horizon]
    if min(s0, b0) <= 0:
        return None
    return direction * ((s1 / s0 - 1) - (b1 / b0 - 1))


def simulate(calendar: list[str], finra: Callable[[str], FinraDay | None], membership: list[tuple[str, frozenset[str]]],
             bars: Callable[[str], Ohlc | None], spy: Ohlc, first: str, last: str) -> tuple[list[dict], dict[str, int]]:
    """Every signal day from `first` to `last` that has a FINRA file and BASELINE_DAYS earlier files in a row of sessions."""
    rows: list[dict] = []
    totals = {"days": 0, "days_skipped": 0, "members": 0, "no_bars": 0, "illiquid": 0}
    window: deque[FinraDay] = deque(maxlen=BASELINE_DAYS)
    for day in calendar:
        today = finra(day)
        if today is not None and first <= day <= last and len(window) == BASELINE_DAYS:
            picks, counts = pick_day(day, today, list(window), members_on(membership, day), bars)
            totals["days"] += 1
            for k in ("members", "no_bars", "illiquid"):
                totals[k] += counts[k]
            for symbol, direction, z in picks:
                stock = bars(symbol)
                assert stock is not None                      # pick_day only returns names with bars
                rows.append({"day": day, "symbol": symbol, "direction": direction, "z": z, "drift": outcome(stock, spy, day, direction)})
        elif first <= day <= last:
            totals["days_skipped"] += 1
        if today is not None:
            window.append(today)
        else:
            window.clear()                                    # a missing file breaks the baseline: never bridge a gap silently
    return rows, totals


# ---- verdict -----------------------------------------------------------------------------------------------------------------

def leg_verdicts(rows: list[dict]) -> dict[str, tuple[int, int, float | None, tuple[float, float] | None, str]]:
    out = {}
    for name, direction in (("long", 1), ("short", -1)):
        by_day: dict[str, list[float]] = defaultdict(list)
        n = 0
        for r in rows:
            if r["direction"] == direction and r["drift"] is not None:
                by_day[r["day"]].append(r["drift"])
                n += 1
        mean, ci, verdict = judge([fmean(v) for _, v in sorted(by_day.items())], ROUND_TRIP_COST)
        out[name] = (n, len(by_day), mean, ci, verdict)
    return out


def render(rows: list[dict], totals: dict[str, int]) -> str:
    lost = (totals["no_bars"] + totals["illiquid"])
    lines = [f"signal days {totals['days']} (skipped for a missing file or baseline: {totals['days_skipped']}); "
             f"candidates dropped for no bars (delisted or unknown to IBKR): {totals['no_bars']}, for illiquidity: {totals['illiquid']}"
             f" (member-days seen {totals['members']}, dropped {lost})"]
    verdicts = leg_verdicts(rows)
    for name, (n, days, mean, ci, verdict) in verdicts.items():
        if mean is None or ci is None:
            lines.append(f"{name:5} n={n:>5} days={days:>4}  {verdict}")
        else:
            lines.append(f"{name:5} n={n:>5} days={days:>4} mean {mean:+.2%} [{ci[0]:+.2%},{ci[1]:+.2%}] cost {ROUND_TRIP_COST:.2%}  {verdict}")
    both = all(v[4].startswith("KILL") for v in verdicts.values())
    lines.append("SOURCE: " + ("both legs killed: drop short_volume_v1" if both else "not dropped (a single failed leg kills that leg only; a pass proves nothing)"))
    return "\n".join(lines)


# ---- cache and glue ----------------------------------------------------------------------------------------------------------

def save_ohlc(path: Path, bars: Ohlc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(("date", "open", "close", "volume"))
        w.writerows(zip(bars.dates, bars.open, bars.close, bars.volume))


def load_ohlc(path: Path) -> Ohlc | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return Ohlc([r["date"] for r in rows], [float(r["open"]) for r in rows], [float(r["close"]) for r in rows], [float(r["volume"]) for r in rows])


def weekdays_between(first: date, last: date) -> int:
    return sum((first + timedelta(days=n)).weekday() < 5 for n in range((last - first).days + 1))


def all_symbols(membership: list[tuple[str, frozenset[str]]], first: str = FIRST.isoformat(), last: str = LAST.isoformat()) -> list[str]:
    """Everyone who was a member on any day of the window."""
    names: set[str] = set(members_on(membership, first))
    for d, t in membership:
        if first <= d <= last:
            names |= t
    return sorted(names)


def fetch_all() -> int:  # pragma: no cover - network and Gateway
    import dataclasses
    import time

    from dotenv import load_dotenv
    from ib_async import Stock

    from tempo.config import load_config
    from tempo.ibkr import connect
    from tempo.snapshots import collect_finra, http_get
    load_dotenv()
    HIST.mkdir(parents=True, exist_ok=True)
    members_path = HIST / "members.csv"
    if not members_path.exists():
        members_path.write_bytes(http_get(MEMBERS_URL))
    membership = parse_members(members_path.read_text(encoding="utf-8"))
    got = collect_finra(LAST, snap=HIST, backfill=weekdays_between(FIRST - timedelta(days=40), LAST))
    print(f"FINRA: saved {len(got['saved'])}, had {len(got['have'])}, not published {len(got['not_published'])} "
          "(holidays and the days before the consolidated file started)")
    ib = connect(dataclasses.replace(load_config(), client_id=96))
    ib.RequestTimeout = 60
    done = 0
    try:
        for symbol in ["SPY", *all_symbols(membership)]:
            path, none = HIST / "bars" / f"{symbol}.csv", HIST / "bars" / f"{symbol}.none"
            if path.exists() or none.exists():
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            contract = Stock(symbol, "SMART", "USD")
            raw = ib.reqHistoricalData(contract, "", "9 Y", "1 day", "TRADES", useRTH=True, formatDate=1) if ib.qualifyContracts(contract) else None
            if not raw:
                none.write_text("no bars", encoding="utf-8")
                continue
            save_ohlc(path, Ohlc([str(b.date) for b in raw], [float(b.open) for b in raw], [float(b.close) for b in raw], [float(b.volume) for b in raw]))
            done += 1
            if done % 50 == 0:
                print(f"{done} bar files fetched")
            time.sleep(0.3)
    finally:
        ib.disconnect()
    print(f"fetched {done} bar files")
    return 0


def report() -> int:  # pragma: no cover - reads the cache
    from tempo.snapshots import load_short_volume
    spy = load_ohlc(HIST / "bars" / "SPY.csv")
    if spy is None:
        raise SystemExit("no cached SPY bars: run fetch first")
    membership = parse_members((HIST / "members.csv").read_text(encoding="utf-8"))
    cache: dict[str, Ohlc | None] = {}

    def bars(symbol: str) -> Ohlc | None:
        if symbol not in cache:
            cache[symbol] = load_ohlc(HIST / "bars" / f"{symbol}.csv")
        return cache[symbol]
    rows, totals = simulate(spy.dates, lambda d: load_short_volume(date.fromisoformat(d), HIST), membership, bars, spy,
                            FIRST.isoformat(), LAST.isoformat())
    print(render(rows, totals))
    return 0


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - entry point
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["fetch"]:
        return fetch_all()
    if args[:1] == ["report"]:
        return report()
    raise SystemExit(__doc__)


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
