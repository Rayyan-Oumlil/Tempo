# Runbook: operating Tempo

Paper account only. Commands run from the repo root with the virtual environment active. PowerShell sets orders-enabled with `$env:IBKR_READONLY=0`; Git Bash with `IBKR_READONLY=0 python ...`.

## What runs where
| Part | Needs IB Gateway? | Needs internet? |
|---|---|---|
| `tempo.insider` (SEC insider collection), `tempo.edgar` (earnings releases) | no | yes (SEC) |
| `tempo.ledger`, `tempo.forward`, all `*_report` runners, `tempo.paper_run plan\|status` | no | no (saved data) |
| `tempo.ledger_score`, `tempo.data`, `tempo.health` | yes (read-only is enough) | no |
| `tempo.paper_run preflight\|entries\|exits`, `lifecycle`, `bracket`, `kill`, `flatten` | yes; orders need Read-Only API unticked and `IBKR_READONLY=0` | no |

## A normal trading day
1. **Morning, any time after about 06:00 ET:** `python -m tempo.insider <previous trading day>`. The SEC builds a day's index overnight. After any gap, give the missed days in order, oldest first: `python -m tempo.insider 2026-11-03 2026-11-04 2026-11-05` (signals are computed as of the last date).
2. **Before the open:** start IB Gateway on the paper account; untick Read-Only API (one-time setting). `python -m tempo.paper_run preflight` must show no `[FAIL]`.
3. **09:35 ET or later:** first re-run `preflight` and require `[OK] daily P&L readable`. IBKR often cannot give the daily P&L overnight, around its nightly reset (about 00:15 to 01:45 ET) and at weekends (seen 2026-11-08: OK at one point, FAIL at 01:13 ET). With the P&L unreadable the order door refuses every entry (fail closed, by design) and the runner records each signal as skipped, which cannot be undone. So do not run `entries` until that line is OK; if it stays red after 09:30, wait and retry rather than running. Then `python -m tempo.paper_run entries`. Entries are only possible on a signal's entry day; if the day passes, the signal is recorded as missed and never traded late.
4. **15:45 ET or later on exit days:** `python -m tempo.paper_run exits`. `python -m tempo.paper_run plan` shows what is due.
5. **After the close:** `python -m tempo.ledger_score` then `python -m tempo.ledger`. Scores need days to pass (1, 5 and 21 trading days after entry).
6. **Occasionally:** `python -m tempo.forward` (the frozen mean-reversion rules; prints NOT ENOUGH TRIPS for a long time).
7. **Earnings readings (optional, in a Claude session, evening after the close):** read releases with `python -m tempo.edgar TICKER DATE brief`, record each call at once with `python -m tempo.ledger add claude_earnings_v1 TICKER long|short 2026Q3 --confidence N --reason "..."`, following `evidence/llm_earnings_forward.json`. No prices or market reaction may be looked at first.

## First live run of the paper runner (never done yet)
1. Gateway up, Read-Only API unticked, `IBKR_READONLY=0`.
2. `python -m tempo.paper_run preflight`: fix any `[FAIL]`.
3. `python -m tempo.paper_run entries --dry-run` (add `--as-of "YYYY-MM-DD HH:MM"` to rehearse an entry day): it uses the real broker and the order door's real checks, asks the broker what each order would cost, and sends and records nothing. Read every line.
4. Only then `python -m tempo.paper_run entries` with a small set due, watching the output. Each earlier module showed a surprise at its first live run; expect one.
5. After any change to order code: `TEMPO_LIVE=1 pytest tests/live -v` (regular hours).

## When something goes wrong
| Symptom | What it means / what to do |
|---|---|
| `Gateway not reachable` / timeout | Gateway is closed or logged out (IBKR logs out daily and asks for a fresh login about weekly). Log in again; a missed entry day stays missed. |
| `paper_run needs IBKR_READONLY=0` | Orders are disabled on purpose. Set the variable and untick Read-Only API. |
| `not allowed now` | Entries need 09:35 ET or later, exits 15 minutes before the close, regular hours only. |
| `[FAIL] journal ... unresolved` | A previous order has no recorded outcome. `python -m tempo.reconcile` (add `--accept-missing` for cancelled ones). New entries are blocked until this is clear. |
| `mode reduce_only` | Entries are blocked (kill switch or manual). `python -m tempo.state normal "why"` to resume once understood. |
| SEC `HTTP 403` or `429` | Too many requests or a missing/invalid `SEC_USER_AGENT` in `.env`. The client waits 0.25 s between requests; wait and re-run the same days. The collector retries any failed filing next time. |
| SEC `HTTP 404` on an index | That day's index does not exist yet (or the day was not a trading day). |
| Skipped signal ("cannot qualify", "no price", "too small") | Expected for a few: tickers like `NONE`, SPAC units, brand-new listings. Skips are counted in `python -m tempo.paper_run status`. |

## Rules that must not be bent
* `evidence/*.json` are pre-registered. A change needs a dated entry in `docs/research/log.md` saying why. Results are never used to edit them.
* The ledger (`ledger/ledger.jsonl`) is append-only. Never edit or delete a signal; commit it so git is a second witness of the timestamps.
* Paper P&L never feeds a strategy verdict. Only the ledger's criteria do.
* Every order goes through `tempo/orders.py`. Nothing else calls `ib.placeOrder`.
* Secrets (`.env`, including the SEC contact string) are never committed.

## Where things live
| Path | What | In git? |
|---|---|---|
| `ledger/ledger.jsonl` | every forward signal and score | yes |
| `journal/` | every order Tempo sent, and the paper runner's state | no (account details) |
| `data/` | downloaded prices and the SEC insider cache | no (market data) |
| `evidence/` | pre-registered tests and the gate | yes |
| `goldens/` | the exact saved outputs of the report runners (`goldens/data` is a frozen price snapshot, not in git) | outputs yes |
| `docs/research/log.md` | dated findings, append-only | yes |

## Developing
* `pytest` (offline suite; GitHub Actions also runs `ruff check .` and the mutation check on every push).
* `python tools/mutate.py [module...]` breaks the code on purpose and shows whether the tests notice.
* `python tools/golden.py check` proves a change to a report runner altered none of its saved numbers. Refresh the frozen snapshot with `python tools/golden.py snapshot` only deliberately, and re-record with `record`.
* Dev tools: `pip install -r requirements-dev.txt`.
