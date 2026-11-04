# Plan: now to Friday 2026-11-06 (the PC is unavailable until then)

Goal set by the owner: **the current code should be the best it can be first; new features and ideas after.** Nothing in this plan needs IB Gateway, so all of it can run while the Gateway is off. Everything that needs the Gateway waits for the Friday session (section "Friday").

Starting point (2026-11-03 night): 562 offline tests, 77% line coverage, 3 forward tests running, the paper runner built but never run live.

## Objectives, in order

| # | Objective | Why it comes in this order | Done when |
|---|---|---|---|
| 1 | **Trust the verdict code.** The five strategy report runners (rotation, pairs, overnight, mean reversion, tactical) and the forward test sit at 40 to 61% coverage: the pure verdict functions are tested but the wiring that feeds them data is not. Capture each runner's real output now as a golden file, add end-to-end tests on synthetic data, then remove the duplicated helpers with the golden outputs staying byte-identical. | These produced every number we reported. A silent wiring bug would be the worst kind. | Each runner has an end-to-end test; goldens unchanged after the refactor |
| 2 | **Repository hygiene and automatic checking.** CI that runs the tests on every push; line-ending normalisation (the CRLF warnings); lint and type checks installed as dev tools and their real findings fixed (no style churn); README and a runbook that match what exists. | So a mistake cannot reach `main` unnoticed, and anyone (including a cloud agent) can pick the project up cold. | CI green on GitHub; lint clean; README lists every command |
| 3 | **Make the first live run of the paper runner safe.** A `preflight` command (Gateway reachable, paper account, read-only flag, mode normal, journal clean, time window right) and a `--dry-run` that does everything except send orders. | The runner has never met the real broker and every earlier module surprised us at its first live run. A dry run is how we find the surprise without orders. | Both exist, tested offline; run on Friday before any order |
| 4 | **Raise coverage where it matters most: the order path.** `kill`, `bracket`, `flatten`, `lifecycle`, `roundtrip` and the SEC client and ledger scorer, with tests on their main paths and failure paths using the fake broker. Audit for silent fallbacks (the rule: fail hard and say why). | The order path is the code that will one day matter with real money. | Each of those modules at 85% or more, or a written reason why not |
| 5 | **A reusable mutation-check tool.** The scratch scripts used to attack each module are not in the repo. Move them into `tools/` as one generic script. | The most effective test-quality check we found, and currently not repeatable. | `python tools/mutate.py` works for a module and test file |
| 6 | **Docs consistency.** One current-state page; stale statements removed from the roadmap; every pre-registered test linked to its result. | Documents that disagree with the code mislead the next session. | A cold read of README and roadmap matches `git log` |

## Status (updated as work finishes)

| # | State | Evidence |
|---|---|---|
| 1 Trust the verdict code | **Done** | `tools/golden.py` (7 runners, outputs match every number reported), end-to-end tests that feed each runner pure noise (none passes), shared helpers with byte-identical outputs after the refactor |
| 2 Hygiene and automatic checking | **Done** | GitHub Actions on every push (ruff, 609 offline tests, mutation check), `.gitattributes`, `ruff.toml`, `requirements-dev.txt`, README commands, `docs/runbook.md` |
| 3 First live run made safe | **Done offline, awaiting Friday** | `paper_run preflight`, `entries --dry-run [--as-of]`, tested with 23 tests and mutations; nothing has met the real broker yet |
| 4 Order path and data plumbing | **Mostly done** | coverage 77% to 89%; the remainder is `main()` wiring covered by the live suite; refusal tests for every order tool; audit found no silent fallback (7 broad handlers, all re-raise, journal the error, or return an explicit failed check) |
| 5 Reusable mutation tool | **Done** | `tools/mutate.py` plus six per-module mutation files, run in CI; its first run caught a stale mutation |
| 6 Docs consistency | **Done** | runbook, roadmap and docs index updated |

## After that (only when 1 to 6 are done): new features and ideas
Held on purpose. Candidates, none started: automate the Claude earnings reading through the API (needs a spending cap from the owner), a cloud routine for the insider collection, a cleaner insider rule as a new source, the `whatIfOrder` check and tick rounding, sector-ETF momentum as a further forward test.

## Friday (needs the PC and the Gateway)
1. Start IB Gateway on the paper account, Read-Only API unticked, `IBKR_READONLY=0`.
2. `python -m tempo.paper_run preflight`, then `python -m tempo.paper_run entries --dry-run`. Fix anything it shows.
3. Catch up in order: `python -m tempo.insider 2026-11-03`, then `2026-11-04`, then `2026-11-05`.
4. `python -m tempo.ledger_score`, then `python -m tempo.ledger`.
5. The 25 entries planned for 2026-11-04 will have been recorded as missed (by design). The earnings exits for 2026-11-10 only exist for positions actually entered, so none are due. Resume with new signals.

## Rules while working through this
* No change to any verdict code without the golden output proving identical results.
* Every change is committed in small steps with the tests green; pushed at the end of each objective.
* Nothing is added that is not on this list, except fixes found while doing it (written down in `docs/research/log.md`).
