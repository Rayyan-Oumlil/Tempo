# Handoff to another PC (written 2026-11-04)

## Setup (new PC)
1. Install Python (same major version as the old PC), Git, and IB Gateway/TWS (only needed for broker work).
2. `git clone https://github.com/Rayyan-Oumlil/Tempo.git && cd Tempo`
3. `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements-dev.txt`
4. `copy .env.example .env` and fill it in by hand. `.env` holds secrets and is never in Git.
5. `data/` and `goldens/data/` are now committed, so no re-download is needed.
6. Verify: `python -m ruff check . && python -m pytest -q` (expect ~625 passed, 8 skipped; skips are the live-broker suite).

## Journal and state (read before trading)
`handoff/journal-snapshot/` and `handoff/state-snapshot.json` are a SNAPSHOT of the trading PC at 2026-11-04. The live paths (`journal/`, `state.json`) stay git-ignored.
- To make the new PC the trading machine: copy them into `journal/` and `state.json` at the repo root.
- NEVER run the paper runner from two PCs. Each journal would be blind to the other's orders (double-order risk). Use the second PC for code and research only.

## Where we are
Direction: hardening only, no new features (few solid parts beat many weak ones). Strategy tests so far all FAIL honestly (docs/research/log.md).
Done (latest commit a1e89eb): coverage 77% -> 89%, CI (lint + tests + mutation check), noise-must-not-PASS tests, paper_run preflight/--dry-run, runbook, silent-failure audit, three live-order bugs fixed, and the journal crash repair (torn last line quarantined to `<journal>.torn`) with real two-process tests and a journal mutation check.

## Next steps, in order
1. Property-based tests for the order door (`tempo/orders.py`): random orders vs its safety rules (hypothesis).
2. Type checking on core modules (mypy/pyright).
3. Update docs/roadmap to mention the journal repair (not yet done).
4. Check the first CI run on Linux: `tests/journal_worker.py` runs in separate processes and was only verified on Windows.
5. Optional, needs the owner's yes: cloud insider-data collection (email in a cloud secret); automating Claude earnings reading (needs a spending cap first).

## Friday 2026-11-06 (needs the Gateway, on the trading PC)
Start Gateway on the paper account and untick Read-Only API. Run `paper_run preflight`, then `entries --dry-run`, and read every line. Catch up insider collection for 11-03, 11-04, 11-05 in order, then score the ledger. The 25 entries planned for 11-04 show as missed by design. See docs/runbook.md.
