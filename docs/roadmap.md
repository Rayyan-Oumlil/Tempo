# Roadmap

Paper account `DUR239224` only. Tempo refuses any non-paper account.

## Done

| Step | Evidence |
|---|---|
| Connect, health check | `python -m tempo.health` |
| Read-only API smoke tests (qualify, details, snapshot, history, daily bars) | `python -m tempo.smoke SPY` |
| Order round trip: place a far limit, see it, cancel it, confirm clean | `IBKR_READONLY=0 python -m tempo.roundtrip` |
| Risk rules and position sizing (`rules.json`: 2% risk per trade, 100% max position) | `python -m tempo.size SPY 740` |
| Overnight order test: buy filled; sell did not fill (thin market) | see [ibkr-gotchas.md](ibkr-gotchas.md) |
| Regular-session market sell (`IBKR_READONLY=0 python -m tempo.flatten SPY`), 2026-11-02 09:37 ET | Sold 1 SPY @ 759.53 (cost 760.64), commission 1.02 USD |
| Lifecycle tool (`IBKR_READONLY=0 python -m tempo.lifecycle SPY 1`): buy, confirm, sell, P&L and cash | Live run: bought 760.24, sold 760.19, net -2.07 USD, CAD cash -2.88 |
| Foundations phases 1 to 5 (order door and journal, kill switch and modes, reconcile, brackets, evidence harness and gate), 2026-11-02 | 122 tests; live paper: lifecycle, bracket with resting stop, kill switch on a long plus a short; `python -m tempo.evidence SPY` |
| Daily loss limit (`max_daily_loss_pct`, blocks entries only, fails closed), 2026-11-02 | 349 offline tests; live: refusal and acceptance verified; market-hours live checks pending |
| Live suite after the exit-room fix and loss limit, 2026-11-03: 7 of 7 | Run 3 of 3 clean; two earlier runs hit Gateway connection timeouts (see log.md) |
| Broker rejection reasons in the journal, 2026-11-03 | 385 offline tests; live: 110, 391 and a real 201 compared against IBKR, plus a permanent live test (8 checks now) |
| Strategy research, 2026-11-03: five pre-registered tests on daily data, **none passed** | SMA 200 trend, 12-1 momentum rotation, pairs, overnight drift, mean reversion. Results and numbers in [research/log.md](research/log.md); evidence in [research/swing-trading-research.md](research/swing-trading-research.md) |
| Forward test of the frozen mean reversion rules, registered 2026-11-03 | `evidence/forward_test.json`; run `python -m tempo.data SPY --ohlc; python -m tempo.data QQQ --ohlc; python -m tempo.forward`; no verdict before 60 pooled round trips or 2028-11-03 |
| Signal ledger, 2026-11-03: `tempo/ledger.py` (append-only, clock-stamped, no backdating, scored from the next trading day against SPY, no verdict before 30 scored signals) | 503 offline tests, mutation-checked; `python -m tempo.ledger` prints the state. No signal source is attached yet |
| Claude earnings-reading forward test, pilot 2026-11-03: 10 calls recorded before any reaction | `evidence/llm_earnings_forward.json`; `ledger/ledger.jsonl`; score with `python -m tempo.ledger_score` after each trading day, read with `python -m tempo.ledger`; SEC EDGAR client `tempo/edgar.py` (contact string in `.env`) |
| Insider-purchase forward test, registered 2026-11-03 (`evidence/insider_forward.json`) | Collector `python -m tempo.insider DATE...` (SEC Form 4 via the daily index; run each morning for the previous trading day, in order, after any gap); signals go to the ledger as `insider_cluster_v1` with a 50 bps cost assumption; scored by `python -m tempo.ledger_score`; no verdict before 30 scored signals, full test needs 100 at 21 days |
| Paper execution of the forward signals, built 2026-11-03 (`evidence/paper_run.json`, `tempo/paper_run.py`) | Plan shows what is due: `python -m tempo.paper_run plan [DATE]`. With Gateway on the paper account, Read-Only API unticked and `IBKR_READONLY=0`: at 09:35 ET or later on the entry day `python -m tempo.paper_run entries`; at 15:45 ET or later on the exit day `python -m tempo.paper_run exits`. First live run is 2026-11-04 (25 entries); earnings exits 2026-11-10, insider exits 2026-12-03. Missed entry days are recorded, never traded late. Not yet run live: expect to find things the offline tests cannot show |
| Gateway probe, 2026-11-02: market data limits, history depth, scanner, order types and rejections, shorting, brackets and OCA, kill switch, fees, FX | Findings in [ibkr-gotchas.md](ibkr-gotchas.md) |

State: **flat**, no open orders.

## Next

Foundations are hardened and the first feature, the daily loss limit, is built.

1. **Done 2026-11-03, 09:55 ET: live suite, 7 of 7 passing** (OCA-aware exit room, "flatten says why", the daily-loss exits all proven live). Honest record of the day: run 1 gave 7 errors (the Gateway accepted the socket but the API handshake timed out, transient; health check connected a minute later); run 2 gave 6 passed and 1 error (a `TimeoutError` in the crash-and-reconcile test, cause NOT found because that traceback was not kept; the test passed alone in 9 s); run 3 gave 7 passed. The account was flat with no open orders after each run. Open question: why one live connection timed out under the full suite.
2. **Saved for after the live run (from the 2026-11-02 evening audit, see [reference-audit.md](research/reference-audit.md)):** (a) DONE 2026-11-03: the journal records why the broker refused an order (listens to `errorEvent`; see ibkr-gotchas.md); (b) a `whatIfOrder` margin and commission check inside the order door; (c) multi-day drawdown lock and stop-out pause, only when an unattended loop is chosen; (d) round limit prices to the contract's `minTick`. None started.
3. **Strategy state (2026-11-03):** six pre-registered tests on daily data (SMA 200 trend, 12-1 momentum rotation, pairs, overnight drift, mean reversion, tactical asset allocation), none passed. Pattern: ideas that trade often are eaten by costs (overnight drift broke even at about 1 bp of slippage per side); ideas that trade rarely survive costs (mean reversion broke even near 20 bps) but no longer beat buy and hold since 2010. The only evidence that cannot be overfitted is the **forward test** of the frozen mean reversion rules (check it every month or so; it prints NOT ENOUGH TRIPS until 60 pooled round trips exist, about 15 to 24 months). Remaining queue if the search continues, each to be pre-registered first: large-cap short-term reversal with a VIX filter, sector-ETF momentum, high-volume premium. Not yet decided by the owner: keep searching, or treat Tempo as finished infrastructure.
   - Paper trading **cannot measure real slippage** (simulated fills, delayed quotes); only tiny real-money trades could, and that is gated by `evidence/gate.json`.
   - **Waiting on the owner:** an API spend cap, and whether to automate, for scaling the Claude earnings reading beyond the 10-signal pilot (about 2.5 thousand tokens of reading per release in-session; an API run would be billed). The SEC contact string was given on 2026-11-03 and lives in `.env`. Both forward-test sources (Claude earnings readings, insider purchases) are attached to the ledger; the routine is: each morning run `python -m tempo.insider <previous trading day>`, each evening after the close run the earnings reading if wanted, and `python -m tempo.ledger_score` then `python -m tempo.ledger` to see where things stand.
   - Not started and not needed yet: data subscription, unattended loop (the runbook lists what an unattended day would need: Gateway logged in at 09:25 ET, then the scheduled commands), scanner, `whatIfOrder` check in the order door (the paper runner's dry run already asks the broker what an order would cost), tick rounding, multi-day drawdown lock.
4. **Until Friday 2026-11-06 (PC and Gateway unavailable):** the code-quality plan in [plan-to-friday.md](plan-to-friday.md) (nothing in it needs the Gateway). **Friday:** first live preflight, dry run and real run of the paper runner, then the insider catch-up; steps in [runbook.md](runbook.md).
5. **Routine:** run the live suite after any change to order code; update the market calendar from the NYSE page each December (entries are refused after 2027-12-31).

## Gate before real money

The numbers are pre-registered in `evidence/gate.json` and are checked by hand. An automatic checker was removed on 2026-11-02 because nothing produced the numbers it would check; build one when paper trading exists.

- Two to three months of paper results that stay positive after commissions and conversion costs, and match the backtest.
- The kill switch and daily loss limit tested.
- Employer compliance and study-permit/tax rules checked.
