"""Append-only journal of every order Tempo sends: one JSON object per line.

Record kinds, tied together by `ref` (the order's unique orderRef):
  intent      written BEFORE the order is sent, so a crash cannot hide a live order
  sent        the broker accepted the call (carries the orderId)
  outcome     the final state (Filled, Cancelled, error, ...)
  resolution  written by reconcile when an unconfirmed intent has been matched to the broker's records
  fill        written by reconcile for each broker execution of a journaled order (deduplicated by exec_id),
              so fills that happen after an order was resolved (a stop or take-profit firing) are not lost

An `intent` with no `outcome` and no `resolution` is "unresolved".
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Callable

JOURNAL_FILE = Path(__file__).resolve().parents[1] / "journal" / "journal.jsonl"
CLOSING_KINDS = {"outcome", "resolution"}
STALE_INTENT_SECONDS = 60.0  # an unresolved intent older than this blocks new entries (and health flags it)


class Journal:
    def __init__(self, path: Path = JOURNAL_FILE, clock: Callable[[], float] = time.time):
        self.path = Path(path)
        self._clock = clock

    def now(self) -> float:
        return self._clock()

    def append(self, kind: str, **fields) -> dict:
        record = {"ts": self._clock(), "kind": kind, **fields}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return record

    def records(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for n, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except ValueError as exc:
                raise ValueError(f"{self.path}: line {n} is not valid JSON ({exc})") from exc
        return out

    def unresolved(self) -> list[dict]:
        records = self.records()
        closed = {r.get("ref") for r in records if r.get("kind") in CLOSING_KINDS}
        return [r for r in records if r.get("kind") == "intent" and r.get("ref") not in closed]
