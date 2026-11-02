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
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

JOURNAL_FILE = Path(__file__).resolve().parents[1] / "journal" / "journal.jsonl"
CLOSING_KINDS = {"outcome", "resolution"}
STALE_INTENT_SECONDS = 60.0  # an unresolved intent older than this blocks new entries (and health flags it)


LOCK_TIMEOUT_SECONDS = 5.0


class JournalLocked(RuntimeError):
    """Another Tempo process holds the journal lock. Nothing was sent."""


class Journal:
    def __init__(self, path: Path = JOURNAL_FILE, clock: Callable[[], float] = time.time,
                 lock_timeout: float = LOCK_TIMEOUT_SECONDS):
        self.path = Path(path)
        self._clock = clock
        self._lock_timeout = lock_timeout

    @contextmanager
    def lock(self, timeout: float | None = None) -> Iterator[None]:
        """Hold an OS file lock so two Tempo processes cannot both pass the checks and both send.

        Fails loudly after `timeout` seconds instead of waiting forever. The OS drops the lock if the process dies.
        """
        wait = self._lock_timeout if timeout is None else timeout
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(self.path.with_suffix(".lock"), "a+b")
        deadline = time.monotonic() + wait
        try:
            while True:
                try:
                    _try_lock(handle)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise JournalLocked(f"another Tempo process holds {self.path.with_suffix('.lock')}") from None
                    time.sleep(0.05)
            try:
                yield
            finally:
                _unlock(handle)
        finally:
            handle.close()

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


def _try_lock(handle) -> None:
    handle.seek(0)
    if sys.platform == "win32":
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(handle) -> None:
    handle.seek(0)
    if sys.platform == "win32":
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
