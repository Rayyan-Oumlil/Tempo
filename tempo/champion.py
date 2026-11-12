"""Champion and challenger: improve a rule without fooling ourselves.

Usage: python -m tempo.champion

A challenger is a changed version of a signal source (a new source name, e.g. short_volume_v2) that runs on the same data
beside the unchanged champion. Each pair is registered in evidence/challengers/<challenger>.json BEFORE the challenger
records its first signal, with the change, the reason, and the promotion rule (all numbers fixed in advance).

The comparison is paired by signal day: for every day where both have scored signals at the champion's horizon, the
difference of the two days' mean net excess returns. One number per day, so the 10 or 20 correlated signals of a day
cannot inflate the evidence. Verdicts:
  INVALID           not registered strictly before the challenger's first signal day, or the registry is malformed
  TOO EARLY         fewer than min_days common days
  KEEP CHAMPION     enough days and the promotion rule is not met
  PROMOTE CANDIDATE every promotion condition is met. A human decides; this tool never changes any rule.
Promotion means writing a NEW pre-registered version number, never editing a frozen rule.
"""
from __future__ import annotations

import json
import statistics
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from tempo.ledger import Ledger
from tempo.overnight import t_statistic

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "evidence" / "challengers"
DEFAULT_HORIZON = 5
RULE_KEYS = ("min_days", "margin", "t_min")


class RegistryError(ValueError):
    pass


@dataclass(frozen=True)
class Pair:
    challenger: str
    champion: str
    registered: date
    change: str
    reason: str
    min_days: int
    margin: float
    t_min: float


def load_pair(path: Path) -> Pair:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        rule = raw["promotion_rule"]
        pair = Pair(raw["challenger"], raw["champion"], date.fromisoformat(raw["registered"]), raw["change"], raw["reason"],
                    int(rule["min_days"]), float(rule["margin"]), float(rule["t_min"]))
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise RegistryError(f"{path.name}: {type(exc).__name__}: {exc}") from exc
    if pair.challenger == pair.champion or path.stem != pair.challenger:
        raise RegistryError(f"{path.name}: challenger must differ from the champion and match the file name")
    if pair.min_days < 30 or pair.t_min < 1.5 or pair.margin < 0 or not pair.change.strip() or not pair.reason.strip():
        raise RegistryError(f"{path.name}: min_days >= 30, t_min >= 1.5, margin >= 0, and a stated change and reason are required")
    return pair


def load_registry(folder: Path = REGISTRY) -> list[Pair]:
    return [load_pair(p) for p in sorted(folder.glob("*.json"))] if folder.exists() else []


def require_registered(source: str, today: date, folder: Path = REGISTRY) -> Pair:
    """Gate for collectors: a challenger may record signals only if it was registered on an earlier day."""
    path = folder / f"{source}.json"
    if not path.exists():
        raise RegistryError(f"{source} is not registered in evidence/challengers/: it may not record signals")
    pair = load_pair(path)
    if pair.registered >= today:
        raise RegistryError(f"{source} was registered {pair.registered}; it may start recording on the next day")
    return pair


def daily_means(ledger: Ledger, source: str, horizon: int) -> dict[str, float]:
    sig = {s["signal_id"]: s["date_et"] for s in ledger.signals(source)}
    by_day: dict[str, list[float]] = {}
    for sc in ledger.scores(source):
        if sc["horizon"] == horizon and sc["signal_id"] in sig:
            by_day.setdefault(sig[sc["signal_id"]], []).append(sc["net_excess"])
    return {d: statistics.fmean(v) for d, v in by_day.items()}


def verdict(pair: Pair, champ: dict[str, float], chall: dict[str, float], first_challenger_signal: str | None) -> tuple[str, str]:
    if first_challenger_signal is not None and pair.registered >= date.fromisoformat(first_challenger_signal):
        return "INVALID", f"registered {pair.registered}, not strictly before its first signal ({first_challenger_signal}): the test is void"
    days = sorted(set(champ) & set(chall))
    diffs = [chall[d] - champ[d] for d in days]
    if len(days) < pair.min_days:
        return "TOO EARLY", f"{len(days)} of {pair.min_days} common signal days"
    mean, t = statistics.fmean(diffs), t_statistic(diffs)
    half = len(diffs) // 2
    first, second = statistics.fmean(diffs[:half]), statistics.fmean(diffs[half:])
    own = statistics.fmean(chall[d] for d in days)
    checks = {f"mean difference {mean:+.3%} >= margin {pair.margin:.3%}": mean >= pair.margin,
              f"t {t:.2f} >= {pair.t_min}": t >= pair.t_min,
              f"better in both halves ({first:+.3%}, {second:+.3%})": first > 0 and second > 0,
              f"challenger itself earns {own:+.3%} > 0": own > 0}
    detail = "; ".join(f"{'ok' if ok else 'FAIL'}: {name}" for name, ok in checks.items())
    return ("PROMOTE CANDIDATE" if all(checks.values()) else "KEEP CHAMPION"), f"{len(days)} days; {detail}"


def report(ledger: Ledger | None = None, folder: Path = REGISTRY) -> str:
    from tempo.paper_run import HORIZONS
    ledger = ledger or Ledger()
    pairs = load_registry(folder)
    if not pairs:
        return "CHALLENGERS: none registered (a challenger needs a pattern from tempo.autopsy first)"
    lines = [f"CHALLENGERS: {len(pairs)} registered"]
    for p in pairs:
        horizon = HORIZONS.get(p.champion, DEFAULT_HORIZON)
        sigs = sorted(s["date_et"] for s in ledger.signals(p.challenger))
        v, why = verdict(p, daily_means(ledger, p.champion, horizon), daily_means(ledger, p.challenger, horizon), sigs[0] if sigs else None)
        lines.append(f"  {p.challenger} vs {p.champion}: {v} ({why})")
        lines.append(f"    change: {p.change}")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    try:
        print(report())
    except (OSError, ValueError) as err:
        print(f"[FAIL] {type(err).__name__}: {err}", file=sys.stderr)
        raise SystemExit(1)
