"""A3: which short signals could not have been traded. A short with no shares to borrow is not a missed profit or a loss, it never
existed, so reports that judge a source's edge leave it out and say how many they left out.

Rule (written before any result): untradeable = direction short AND the daily borrow file knew the symbol AND it listed 0 shares
available. Unknown is NOT excluded (no file, symbol absent, or availability 'NA'): excluding on missing data would quietly shrink the
short leg. A high fee is not excluded either: a fee veto is a separate pre-registered test. Only signals recorded from 2026-11-13 on
carry borrow terms (earlier ones are unknown, hence kept).
"""
from __future__ import annotations

from collections import Counter


def untradeable_reason(signal: dict) -> str | None:
    if signal.get("direction") != -1:
        return None
    f = signal.get("features") or {}
    if f.get("borrow_known") is True and f.get("borrow_available") == 0:
        return "no shares available to borrow"
    return None


def tradeable_scores(signals: list[dict], scores: list[dict]) -> tuple[list[dict], Counter[str]]:
    """(scores of tradeable signals, excluded count per source). A score whose signal is missing from `signals` is an error."""
    bad = {s["signal_id"] for s in signals if untradeable_reason(s)}
    known = {s["signal_id"] for s in signals}
    orphans = [r["signal_id"] for r in scores if r["signal_id"] not in known]
    if orphans:
        raise ValueError(f"scores without a signal: {orphans[:3]}")
    kept = [r for r in scores if r["signal_id"] not in bad]
    return kept, Counter(r["source"] for r in scores if r["signal_id"] in bad)
