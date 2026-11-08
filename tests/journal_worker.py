"""Helper process for tests/test_journal_crash.py. Run as: python tests/journal_worker.py MODE PATH ARGS...

  append PATH TAG N         append N records, taking the lock for each one
  count PATH COUNTER N      N times, under the lock: read the number in COUNTER, pause, write it plus one (loses updates without the lock)
  hold PATH SENTINEL SECS   take the lock, touch SENTINEL, keep the lock for SECS seconds
  torn PATH                 write half a record with no newline, then die without cleaning up (a crash mid-write)
"""
import os
import sys
import time
from pathlib import Path

from tempo.journal import Journal

mode, path = sys.argv[1], Path(sys.argv[2])
journal = Journal(path, lock_timeout=30.0)

if mode == "append":
    tag, n = sys.argv[3], int(sys.argv[4])
    for i in range(n):
        with journal.lock():
            journal.append("tick", tag=tag, i=i)
elif mode == "count":
    counter, n = Path(sys.argv[3]), int(sys.argv[4])
    for _ in range(n):
        with journal.lock():
            value = int(counter.read_text(encoding="utf-8"))
            time.sleep(0.002)
            counter.write_text(str(value + 1), encoding="utf-8")
elif mode == "hold":
    with journal.lock():
        Path(sys.argv[3]).touch()
        time.sleep(float(sys.argv[4]))
elif mode == "torn":
    with path.open("a", encoding="utf-8") as f:
        f.write('{"ts": 1.0, "kind": "inte')
        f.flush()
        os.fsync(f.fileno())
    os._exit(1)
