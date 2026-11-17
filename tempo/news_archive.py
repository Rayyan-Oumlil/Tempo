"""Workstream N1 and N2 (docs/plan-quant-v2.md): keep every headline the three feeds return, and say how complete the pull was.

Append-only `data/news_archive/YYYY-MM.jsonl`. Dedupe key is (symbol, provider, article id). A symbol whose lookup fails after the retries is
LISTED as unavailable, never treated as 'no news'. Coverage under MIN_COVERAGE fails the job loudly.
"""

from __future__ import annotations

import json
import sys
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import cast
from datetime import datetime, timezone
from pathlib import Path

PROVIDERS = ("DJ-RTG", "DJ-N", "BRFG")
PER_FEED = 30
RETRIES = 3
BACKOFF_S = 3.0
MIN_COVERAGE = 0.90
ARCHIVE = Path("data/news_archive")
UNIVERSE = "evidence/universe_sp500_20261111.txt"


@dataclass(frozen=True)
class Item:
    symbol: str
    provider: str
    article_id: str
    time_utc: str  # ISO 8601, UTC
    headline: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.symbol, self.provider, self.article_id)


def to_utc_iso(t: object) -> str:
    """A datetime (naive means UTC) or an IBKR 'YYYY-MM-DD HH:MM:SS' string to ISO UTC."""
    if isinstance(t, datetime):
        dt = t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    else:
        dt = datetime.strptime(str(t)[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def month_file(archive: Path, time_utc: str) -> Path:
    return archive / f"{time_utc[:7]}.jsonl"


def load_keys(archive: Path) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for f in sorted(archive.glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                keys.add((r["symbol"], r["provider"], r["article_id"]))
    return keys


def new_items(items: Iterable[Item], known: set[tuple[str, str, str]]) -> list[Item]:
    """Items not yet archived. One row per (symbol, provider, article id): the same roundup attached to many symbols must stay visible
    as many rows, because the roundup label counts symbols."""
    out: list[Item] = []
    seen = set(known)
    for it in items:
        if it.key not in seen:
            seen.add(it.key)
            out.append(it)
    return out


def append(archive: Path, items: Iterable[Item], fetched_at: datetime) -> int:
    archive.mkdir(parents=True, exist_ok=True)
    n = 0
    for it in items:
        row = {"symbol": it.symbol, "provider": it.provider, "article_id": it.article_id, "time_utc": it.time_utc,
               "headline": it.headline, "fetched_at": fetched_at.astimezone(timezone.utc).isoformat()}
        with month_file(archive, it.time_utc).open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        n += 1
    return n


def coverage(ok: int, total: int) -> float:
    if total <= 0:
        raise ValueError("no symbols to cover")
    return ok / total


def fetch_with_retries(fetch: Callable[[str], list[Item] | None], symbol: str, retries: int = RETRIES,
                       sleep: Callable[[float], None] = time.sleep, backoff: float = BACKOFF_S) -> list[Item] | None:
    """`fetch` returns None on a timeout or any failure. Try `retries` times with growing waits; None if every try failed."""
    for attempt in range(retries):
        got = fetch(symbol)
        if got is not None:
            return got
        if attempt < retries - 1:
            sleep(backoff * (attempt + 1))
    return None


def run(symbols: list[str], fetch: Callable[[str], list[Item] | None], archive: Path, now: datetime,
        sleep: Callable[[float], None] = time.sleep) -> tuple[dict, list[str]]:
    """Fetch every symbol, archive new items, return (stats, unavailable symbols)."""
    known = load_keys(archive) if archive.exists() else set()
    unavailable: list[str] = []
    added = 0
    for s in symbols:
        got = fetch_with_retries(fetch, s, sleep=sleep)
        if got is None:
            unavailable.append(s)
            continue
        fresh = new_items(got, known)
        known.update(i.key for i in fresh)
        added += append(archive, fresh, now)
    cov = coverage(len(symbols) - len(unavailable), len(symbols))
    return {"symbols": len(symbols), "unavailable": len(unavailable), "coverage": round(cov, 4), "added": added}, unavailable


def main() -> int:  # pragma: no cover - needs the Gateway
    from ib_async import Stock

    from tempo.config import load_config
    from tempo.daybars import load_universe
    from tempo.ibkr import connect

    ib = connect(load_config())

    def fetch(symbol: str) -> list[Item] | None:
        contract = Stock(symbol, "SMART", "USD")
        if not ib.qualifyContracts(contract):
            return None
        out: list[Item] = []
        for provider in PROVIDERS:
            try:
                got = ib.reqHistoricalNews(contract.conId, provider, "", "", PER_FEED)
            except Exception:  # noqa: BLE001 - counted as unavailable by the caller
                return None
            if got is None:
                return None
            out.extend(Item(symbol, provider, str(n.articleId), to_utc_iso(n.time), str(n.headline)) for n in cast(list, got))
        return out

    try:
        stats, unavailable = run(load_universe(UNIVERSE), fetch, ARCHIVE, datetime.now(timezone.utc))
    finally:
        ib.disconnect()
    print(f"news archive: {stats}")
    if unavailable:
        print(f"unavailable ({len(unavailable)}): {' '.join(unavailable[:60])}")
    if stats["coverage"] < MIN_COVERAGE:
        print(f"[FAIL] coverage {stats['coverage']:.0%} is under {MIN_COVERAGE:.0%}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
