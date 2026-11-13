"""exec_v2 scoring (amendment logged in docs/research/log.md, 2026-11-12).

Why it exists: the original scoring entered at the official open print and exited at the close, but the paper runner
enters at 09:40 ET and exits from 15:46 ET. On 2026-11-12 the gap between the two was -250 to +577 bps per trade (NVDA:
the ledger's short scored -10.1%, the executable one -4.1%). A ledger that scores a trade nobody can make cannot be
checked against the paper account. exec_v2 scores:

  entry  = open of the 5-minute bar that starts at 09:40 ET on the entry day (the entries cron runs at 09:40)
  exit   = open of the 5-minute bar that starts 15 minutes before that day's close (15:45; 12:45 on early-close days)
  excess = direction * (stock return - beta * SPY return); beta = trailing 60-day beta to SPY measured strictly before
           the entry day, Blume-shrunk toward 1 (2/3 raw + 1/3). A signal with too little history has no score: it stays
           "waiting" and is counted as unscorable, never scored with a guessed beta.

Scores carry method="exec_v2". Rows written before the amendment have no method; they are kept and never counted.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from tempo.data import Bars
from tempo.hours import session_close
from tempo.ledger import METHOD, ROUND_TRIP_COST

__all__ = ["METHOD", "Intraday", "beta_before", "exit_hhmm", "score_signal_exec"]

ENTRY_HHMM = "09:40"
EXIT_MINUTES_BEFORE_CLOSE = 15
BETA_DAYS = 60
MIN_BETA_DAYS = 40
SHRINK = 2 / 3


@dataclass(frozen=True)
class Intraday:
    """Open price of each 5-minute bar, keyed by (YYYY-MM-DD, 'HH:MM') of the bar's start in New York time."""
    opens: dict[tuple[str, str], float]

    def open_at(self, day: str, hhmm: str) -> float | None:
        return self.opens.get((day, hhmm))


def exit_hhmm(day: date) -> str:
    close = datetime.combine(day, session_close(day))
    return (close - timedelta(minutes=EXIT_MINUTES_BEFORE_CLOSE)).strftime("%H:%M")


def beta_before(stock: Bars, bench: Bars, before: str) -> float | None:
    """Shrunk beta of daily close-to-close returns that END strictly before `before`; None if under MIN_BETA_DAYS returns."""
    s, m = dict(zip(stock.dates, stock.close)), dict(zip(bench.dates, bench.close))
    days = sorted(d for d in s.keys() & m.keys() if d < before)
    pairs = [(s[b] / s[a] - 1, m[b] / m[a] - 1) for a, b in zip(days, days[1:])][-BETA_DAYS:]
    if len(pairs) < MIN_BETA_DAYS:
        return None
    mean_s, mean_m = sum(p[0] for p in pairs) / len(pairs), sum(p[1] for p in pairs) / len(pairs)
    var_m = sum((p[1] - mean_m) ** 2 for p in pairs)
    if var_m == 0:
        return None
    raw = sum((p[0] - mean_s) * (p[1] - mean_m) for p in pairs) / var_m
    return SHRINK * raw + (1 - SHRINK)


def score_signal_exec(signal: dict, daily: Bars, bench_daily: Bars, intra: Intraday, bench_intra: Intraday,
                      horizon: int) -> dict | None:
    """Score one signal at one horizon, or None if it cannot be scored yet (days missing, a bar missing, no beta)."""
    entry = next((i for i, d in enumerate(daily.dates) if d > signal["date_et"]), None)
    if entry is None or entry + horizon - 1 >= len(daily.dates):
        return None
    entry_date, exit_date = daily.dates[entry], daily.dates[entry + horizon - 1]
    exit_time = exit_hhmm(date.fromisoformat(exit_date))
    entry_px = intra.open_at(entry_date, ENTRY_HHMM)
    exit_px = intra.open_at(exit_date, exit_time)
    bench_entry = bench_intra.open_at(entry_date, ENTRY_HHMM)
    bench_exit = bench_intra.open_at(exit_date, exit_time)
    if entry_px is None or exit_px is None or bench_entry is None or bench_exit is None:
        return None
    beta = beta_before(daily, bench_daily, entry_date)
    if beta is None:
        return None
    d = signal["direction"]
    cost = signal["features"].get("round_trip_cost", ROUND_TRIP_COST)
    ret = d * (exit_px / entry_px - 1)
    bench_ret = beta * d * (bench_exit / bench_entry - 1)
    return {"signal_id": signal["signal_id"], "source": signal["source"], "symbol": signal["symbol"], "horizon": horizon,
            "method": METHOD, "entry_date": entry_date, "exit_date": exit_date, "ret": ret, "bench_ret": bench_ret,
            "excess": ret - bench_ret, "net_excess": ret - bench_ret - cost, "round_trip_cost": cost, "beta": beta,
            "entry_px": entry_px, "exit_px": exit_px}
