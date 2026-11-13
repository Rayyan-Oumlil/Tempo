"""D5 event-risk log: headlines on names the paper account holds that suggest a halt, an executive change, M&A, a probe or a failure.
A record only: no order, no veto, no change to any source. It builds the sample (the NVDA case, 2026-11: CEO resignation while the
book was short on a rating downgrade) from which a rule could later be proposed and pre-registered.

Feeds (all on the paper account's news subscription): DJ-RTG, DJ-N (Dow Jones), BRFG (Briefing.com). Keywords are deliberately blunt,
matched on whole words, case-insensitive; a hit is a flag for a human to read, not a verdict.
Log: JSON lines at data/event_risk.jsonl, one per (signal, headline) pair, never written twice.
Usage: python -m tempo.event_risk      (needs Gateway; the late job runs it twice an evening, dedupe makes that harmless)
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, cast

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "data" / "event_risk.jsonl"
PROVIDERS = ("DJ-RTG", "DJ-N", "BRFG")
PER_FEED = 30
LOOKBACK_DAYS = 3
MAX_FAILED_SHARE = 0.2
CATEGORIES: dict[str, tuple[str, ...]] = {
    "halt": (r"halted", r"trading halt", r"suspends? trading"),
    "executive": (r"resign\w*", r"steps? down", r"ousted", r"fired", r"CEO (?:exit|departure|change)", r"names? new CEO",
                  r"abruptly (?:leaves|departs)"),
    "mna": (r"to acquire", r"acquires(?! [\d,]+ of)", r"takeover", r"buyout", r"merger", r"agrees to be (?:bought|acquired)", r"tender offer", r"bid for"),
    "probe": (r"SEC (?:probe|investigation|subpoena)", r"DOJ", r"investigation", r"subpoena", r"class action", r"short[- ]seller report"),
    "failure": (r"bankruptcy", r"chapter 11", r"going concern", r"delisting", r"delisted", r"defaults?", r"restat\w*", r"fraud"),
}
_PATTERNS = {cat: re.compile(r"\b(?:" + "|".join(words) + r")\b", re.IGNORECASE) for cat, words in CATEGORIES.items()}
_TAG = re.compile(r"^(?:\{[^}]*\})?!?")
News = list[tuple[datetime, str, str]]


def classify(headline: str) -> list[str]:
    """Categories whose keywords appear in the headline, sorted. Provider tags like '{A:800015:L:en}' are ignored."""
    text = _TAG.sub("", headline)
    return sorted(cat for cat, pat in _PATTERNS.items() if pat.search(text))


def headline_key(signal_id: str, headline: str) -> str:
    return hashlib.sha1(f"{signal_id}|{_TAG.sub('', headline).strip().lower()}".encode()).hexdigest()[:16]


def load_seen(path: Path = LOG) -> set[str]:
    if not path.exists():
        return set()
    return {json.loads(ln)["key"] for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()}


def scan(held: Iterable[dict], news: Callable[[str], News | None], seen: set[str], now: datetime,
         lookback_days: int = LOOKBACK_DAYS) -> tuple[list[dict], list[str]]:
    """(new flags, symbols whose news could not be fetched). `held` rows: signal_id, symbol, direction. `news(symbol)` returns
    (time, provider, headline) tuples or None on failure. A headline older than the lookback, or already logged, is skipped."""
    cutoff = now - timedelta(days=lookback_days)
    flags: list[dict] = []
    failed: list[str] = []
    cache: dict[str, News | None] = {}
    for h in held:
        sym = h["symbol"]
        if sym not in cache:
            cache[sym] = news(sym)
        items = cache[sym]
        if items is None:
            if sym not in failed:
                failed.append(sym)
            continue
        for when, provider, text in items:
            cats = classify(text)
            key = headline_key(h["signal_id"], text)
            if not cats or when < cutoff or key in seen:
                continue
            seen.add(key)
            flags.append({"key": key, "ts": now.timestamp(), "signal_id": h["signal_id"], "symbol": sym, "direction": h["direction"],
                          "categories": cats, "provider": provider, "headline_time": when.isoformat(),
                          "headline": _TAG.sub("", text).strip()})
    return flags, failed


def append(flags: list[dict], path: Path = LOG) -> None:
    if not flags:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for r in flags:
            f.write(json.dumps(r) + "\n")


def held_rows(state: dict[str, dict]) -> list[dict]:
    return [{"signal_id": sid, "symbol": t["symbol"], "direction": t["direction"]}
            for sid, t in sorted(state.items()) if t.get("status") == "entered"]


def too_many_failed(failed: list[str], held: list[dict]) -> bool:
    symbols = {h["symbol"] for h in held}
    return bool(symbols) and len(failed) / len(symbols) > MAX_FAILED_SHARE


def main() -> int:  # pragma: no cover - needs Gateway
    import dataclasses

    from dotenv import load_dotenv
    from ib_async import Stock

    from tempo.config import load_config
    from tempo.ibkr import connect
    from tempo.journal import Journal
    from tempo.paper_run import PAPER_FILE, load_state
    load_dotenv()
    held = held_rows(load_state(Journal(PAPER_FILE)))
    if not held:
        print("event risk: no held paper position")
        return 0
    ib = connect(dataclasses.replace(load_config(), client_id=94))
    ib.RequestTimeout = 30

    def news(symbol: str) -> News | None:
        contract = Stock(symbol, "SMART", "USD")
        if not ib.qualifyContracts(contract):
            return None
        out: News = []
        for provider in PROVIDERS:
            try:
                got = ib.reqHistoricalNews(contract.conId, provider, "", "", PER_FEED)
            except Exception:  # noqa: BLE001 - counted as a failed symbol by the caller
                return None
            if got is None:
                return None
            for n in cast(list, got):          # ib_async's stub types this as a single HistoricalNews; it is a list
                t = n.time if isinstance(n.time, datetime) else datetime.strptime(str(n.time)[:19], "%Y-%m-%d %H:%M:%S")
                out.append((t if t.tzinfo else t.replace(tzinfo=timezone.utc), provider, n.headline))
        return out
    try:
        flags, failed = scan(held, news, load_seen(), datetime.now(timezone.utc))
    finally:
        ib.disconnect()
    append(flags)
    for f in flags:
        print(f"EVENT RISK {f['symbol']} ({'long' if f['direction'] == 1 else 'short'}) {','.join(f['categories'])}: {f['headline'][:110]}")
    print(f"event risk: {len(held)} held, {len(flags)} new flag(s), {len(failed)} symbol(s) without news {failed[:10]}")
    return 1 if too_many_failed(failed, held) else 0


if __name__ == "__main__":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    raise SystemExit(main())
