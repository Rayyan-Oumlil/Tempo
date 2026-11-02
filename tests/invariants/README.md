# Tempo invariants

A short list of things that must always be true, written out literally and kept apart from the unit tests (idea from `reference/mmr/tests/invariants`).

Rules for this folder:
1. Do not weaken an invariant to make code pass. A failing invariant is a finding: mark it `xfail(strict=True)` naming the bug, and fix the code in a separate change.
2. Every bug found later becomes a named regression test before it is fixed.
3. Write what is true and documented, not what the code happens to do.

| # | Invariant | Where |
|---|---|---|
| 1 | Only `orders.py` sends orders to the broker | `test_invariants.py` |
| 2 | The intent is on disk before the broker is called | `test_invariants.py` |
| 3 | A non-paper account never reaches the broker, through any tool | `test_invariants.py` |
| 4 | A bracket cannot be built without a stop | `test_invariants.py` |
| 5 | Flatten trades the opposite side, for exactly the held size | `test_invariants.py` |
| 6 | Exits are never refused by mode, hours or size limits | `tests/test_orders.py` (`reduce_only` tests) |
