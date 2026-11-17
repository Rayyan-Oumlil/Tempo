"""Workstream N3 (docs/plan-quant-v2.md): deterministic quality labels for a headline. No model, no network.

Order matters: a roundup or an automatic price line is never 'substantive', whatever else it mentions.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable

ROUNDUP_MIN_SYMBOLS = 10
LABELS = ("roundup", "auto_move", "analyst", "filing", "press_release", "substantive")

_META = re.compile(r"^\{[^}]*\}")
_ROUNDUP = re.compile(r"Stocks That Explain Today's Market|Stocks to Watch|Biggest Movers|Stocks Moving|Movers? (?:From|On)\b|52-Week (?:High|Low)", re.I)
_AUTO = re.compile(r"\bStock (?:Slips|Falls|Sheds|Slides|Rises|Gains|Climbs|Jumps|Drops|Rallies|Surges|Tumbles|Sinks)\b.*\b(?:Underperforms|Outperforms)\b", re.I)
_ANALYST = re.compile(r"Price Target|Is Maintained at|Upgraded|Downgraded|Initiates Coverage|Raises Price Target|Lowers Price Target|Maintains (?:Buy|Hold|Neutral|Overweight|Underweight|Outperform|Sell)", re.I)
_FILING = re.compile(r"\b13F\b|Registers? [\d,]+ Of|Files 8-?K|Insider Review|Discloses Holdings|Increases Stake|Reduces Stake|Eliminates Stakes?|Reports New Stakes?|Sells [\d,]+ Of|Buys [\d,]+ Of", re.I)


def clean(headline: str) -> str:
    """Drop the provider's leading {A:...} metadata block and surrounding space."""
    return _META.sub("", headline).strip()


def roundup_texts(day_headlines: Iterable[tuple[str, str]], min_symbols: int = ROUNDUP_MIN_SYMBOLS) -> frozenset[str]:
    """Texts that one provider attached to at least `min_symbols` different symbols on the same day (market-wide roundups).

    `day_headlines` is (symbol, cleaned text) for one calendar day."""
    seen: dict[str, set[str]] = defaultdict(set)
    for symbol, text in day_headlines:
        seen[text].add(symbol)
    return frozenset(t for t, syms in seen.items() if len(syms) >= min_symbols)


def label(text: str, roundups: frozenset[str] = frozenset()) -> str:
    t = clean(text)
    if t in roundups or _ROUNDUP.search(t):
        return "roundup"
    if _AUTO.search(t):
        return "auto_move"
    if _ANALYST.search(t):
        return "analyst"
    if _FILING.search(t):
        return "filing"
    if t.lower().startswith("press release:"):
        return "press_release"
    return "substantive"
