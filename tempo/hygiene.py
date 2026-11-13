"""B1: hygiene view of the insider sources, as a v2 and not an edit. The frozen sources keep emitting exactly what they registered;
this module only classifies their signals from the features they already carry, so a clean subset can be reported beside the full set.

Contaminated (the sensitivity rules written into evidence/insider_forward.json on 2026-11-03, before any return existed):
  placeholder or SPAC-like symbol   'NONE', or five letters ending in U or W (SPAC units and warrants)
  IPO allocation                    volume-weighted price is a whole-dollar number AND at least 3 insiders
NOT done here: 'listed under 90 days'. No free source gives a listing date and these records hold no bars; it needs IBKR history at
scoring time and stays open in the plan.
"""
from __future__ import annotations

from tempo.insider import PLACEHOLDER_SYMBOLS
from tempo.insider import SOURCE as CLUSTER
from tempo.insider_opp import SOURCE as OPPORTUNISTIC

SOURCES = (CLUSTER, OPPORTUNISTIC)
MIN_INSIDERS = 3
WHOLE_DOLLAR_TOL = 0.005          # a volume-weighted price within half a cent of a whole dollar
SUFFIX = " [clean]"


def spac_like(symbol: str) -> bool:
    return symbol in PLACEHOLDER_SYMBOLS or (len(symbol) == 5 and symbol[-1] in "UW")


def contamination(signal: dict) -> str | None:
    """Why the signal is not a clean open-market insider purchase, or None. Only the insider sources are judged."""
    if signal["source"] not in SOURCES:
        return None
    if spac_like(signal["symbol"]):
        return "placeholder or SPAC-like symbol"
    f = signal.get("features") or {}
    vwap, n = f.get("vwap"), f.get("n_insiders", f.get("n_opportunistic"))
    if vwap is not None and n is not None and n >= MIN_INSIDERS and abs(vwap - round(vwap)) <= WHOLE_DOLLAR_TOL:
        return "whole-dollar price with several insiders (IPO allocation)"
    return None


def clean_view(signals: list[dict], scores: list[dict]) -> list[dict]:
    """Copies of the insider scores whose signal is clean, relabelled `<source> [clean]` so reports list them as their own row."""
    known = {s["signal_id"]: s for s in signals}
    out = []
    for r in scores:
        sig = known.get(r["signal_id"])
        if sig is None:
            raise ValueError(f"score without a signal: {r['signal_id']}")
        if sig["source"] in SOURCES and contamination(sig) is None:
            out.append({**r, "source": r["source"] + SUFFIX})
    return out
