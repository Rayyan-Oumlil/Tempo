"""The journal under real process death and real concurrency: the cases an in-process test cannot show."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from ib_async import MarketOrder

from tempo.journal import Journal, JournalLocked
from tempo.orders import Limits, OrderRefused, place
from tempo.reconcile import reconcile
from tests.fakes import OPEN_NOW, SPY, FakeIB, FakeTrade

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "tests" / "journal_worker.py"


def start(*args):
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    return subprocess.Popen([sys.executable, str(WORKER), *map(str, args)], cwd=ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def test_two_processes_appending_at_once_never_corrupt_or_lose_a_record(tmp_path):
    path = tmp_path / "j.jsonl"
    workers = [start("append", path, tag, 150) for tag in ("A", "B", "C")]
    for w in workers:
        _, err = w.communicate(timeout=120)
        assert w.returncode == 0, err
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 450 and all(json.loads(line)["kind"] == "tick" for line in lines)   # every line whole, none lost
    records = Journal(path).records()
    for tag in ("A", "B", "C"):
        assert [r["i"] for r in records if r["tag"] == tag] == list(range(150))            # each writer's own order intact


def test_a_lock_held_by_another_process_blocks_us_and_dies_with_that_process(tmp_path):
    path, sentinel = tmp_path / "j.jsonl", tmp_path / "ready"
    holder = start("hold", path, sentinel, 60)
    try:
        deadline = time.monotonic() + 30
        while not sentinel.exists():
            assert holder.poll() is None, holder.stderr.read()
            assert time.monotonic() < deadline, "the holder never took the lock"
            time.sleep(0.05)
        with pytest.raises(JournalLocked):
            with Journal(path).lock(timeout=0.3):
                pass
    finally:
        holder.kill()                                    # the holder dies without releasing anything
        holder.communicate(timeout=30)
    with Journal(path).lock(timeout=5):                  # the OS freed the lock with the process
        pass


def test_a_record_cut_off_by_a_crash_is_ignored_and_repaired_on_the_next_append(tmp_path):
    path = tmp_path / "j.jsonl"
    j = Journal(path, clock=lambda: 5.0)
    j.append("intent", ref="a")
    j.append("sent", ref="a")
    dead = start("torn", path)
    dead.communicate(timeout=30)
    assert dead.returncode == 1 and not path.read_text(encoding="utf-8").endswith("\n")   # half a line, no newline
    assert [r["kind"] for r in j.records()] == ["intent", "sent"]                         # readable, the fragment is not a record
    j.append("outcome", ref="a", status="Filled")
    assert [r["kind"] for r in j.records()] == ["intent", "sent", "outcome"]
    assert all(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())  # the fragment is gone, nothing glued
    assert (tmp_path / "j.jsonl.torn").read_text(encoding="utf-8").strip() == '{"ts": 1.0, "kind": "inte'   # kept for forensics


def test_a_complete_but_corrupt_line_still_fails_loudly_even_at_the_end(tmp_path):
    path = tmp_path / "j.jsonl"
    path.write_text('{"kind": "intent", "ref": "a"}\nnot json at all\n', encoding="utf-8")
    with pytest.raises(ValueError, match="line 2"):
        Journal(path).records()


def test_a_corrupt_line_in_the_middle_is_not_mistaken_for_a_torn_tail(tmp_path):
    path = tmp_path / "j.jsonl"
    path.write_text('{"kind": "a"}\nGARBAGE\n{"kind": "b"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="line 2"):
        Journal(path).records()


class DiesDuringSend(FakeIB):
    def placeOrder(self, contract, order):
        raise KeyboardInterrupt("the process is killed while the order is being sent")


def test_a_crash_during_send_leaves_an_unresolved_intent_that_blocks_entries_until_reconcile(tmp_path):
    journal = Journal(tmp_path / "j.jsonl")
    rules = dict(journal=journal, limits=Limits(max_position_pct=50.0, stale_intent_s=0.0), equity_usd=100_000.0, ref_price=100.0,
                 state_path=tmp_path / "state.json", now=OPEN_NOW)
    with pytest.raises(KeyboardInterrupt):
        place(DiesDuringSend(), SPY, MarketOrder("BUY", 1, orderRef="crashy"), reason="t", **rules)
    pending = journal.unresolved()
    assert len(pending) == 1 and pending[0]["ref"].startswith("crashy")                    # the intent survived, with no outcome
    time.sleep(0.01)
    with pytest.raises(OrderRefused, match="unresolved"):
        place(FakeIB(), SPY, MarketOrder("BUY", 1), reason="t", **rules)                  # new entries are blocked
    # the order did reach the broker before the process died: reconcile finds it working and clears the intent
    ib = FakeIB(fill=False)
    working = MarketOrder("BUY", 1)
    working.orderRef = pending[0]["ref"]
    ib.trades.append(FakeTrade(SPY, working, "Submitted"))
    checks = reconcile(ib, journal)
    assert any(c.name == "resolved" for c in checks) and journal.unresolved() == []
    place(FakeIB(), SPY, MarketOrder("BUY", 2), reason="t", **rules)                      # entries flow again (not a duplicate of the crashed one)


def test_a_whole_record_that_only_lacks_its_newline_is_kept_not_discarded(tmp_path):
    path = tmp_path / "j.jsonl"
    path.write_text('{"ts": 1.0, "kind": "intent", "ref": "a"}\n{"ts": 2.0, "kind": "sent", "ref": "a"}', encoding="utf-8")   # newline lost
    j = Journal(path, clock=lambda: 3.0)
    assert [r["kind"] for r in j.records()] == ["intent", "sent"]            # readable as it is
    j.append("outcome", ref="a", status="Filled")
    assert [r["kind"] for r in j.records()] == ["intent", "sent", "outcome"]  # nothing lost, nothing glued
    assert not (tmp_path / "j.jsonl.torn").exists()                           # and nothing was quarantined


def test_repair_does_nothing_to_a_healthy_file_and_a_new_file_is_fine(tmp_path):
    path = tmp_path / "j.jsonl"
    j = Journal(path, clock=lambda: 1.0)
    j.append("a")                                   # file does not exist yet
    before = path.read_bytes()
    j.append("b")
    assert path.read_bytes().startswith(before) and len(j.records()) == 2 and not (tmp_path / "j.jsonl.torn").exists()
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    Journal(empty, clock=lambda: 1.0).append("a")   # an empty file is fine too
    assert len(Journal(empty).records()) == 1


def test_a_torn_fragment_is_kept_for_forensics_each_time(tmp_path):
    path = tmp_path / "j.jsonl"
    j = Journal(path, clock=lambda: 1.0)
    for fragment in ('{"ts": 1.0, "kind": "i', '{"ts": 2.0, "ki'):
        j.append("ok")
        with path.open("a", encoding="utf-8") as f:
            f.write(fragment)
        j.append("after")
    kept = (tmp_path / "j.jsonl.torn").read_text(encoding="utf-8").splitlines()
    assert kept == ['{"ts": 1.0, "kind": "i', '{"ts": 2.0, "ki'] and len(j.records()) == 4
