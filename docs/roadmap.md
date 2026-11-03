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
| Gateway probe, 2026-11-02: market data limits, history depth, scanner, order types and rejections, shorting, brackets and OCA, kill switch, fees, FX | Findings in [ibkr-gotchas.md](ibkr-gotchas.md) |

State: **flat**, no open orders.

## Next

Foundations are hardened and the first feature, the daily loss limit, is built.

1. **Done 2026-11-03, 09:55 ET: live suite, 7 of 7 passing** (OCA-aware exit room, "flatten says why", the daily-loss exits all proven live). Honest record of the day: run 1 gave 7 errors (the Gateway accepted the socket but the API handshake timed out, transient; health check connected a minute later); run 2 gave 6 passed and 1 error (a `TimeoutError` in the crash-and-reconcile test, cause NOT found because that traceback was not kept; the test passed alone in 9 s); run 3 gave 7 passed. The account was flat with no open orders after each run. Open question: why one live connection timed out under the full suite.
2. **Saved for after the live run (from the 2026-11-02 evening audit, see [reference-audit.md](research/reference-audit.md)):** (a) DONE 2026-11-03: the journal records why the broker refused an order (listens to `errorEvent`; see ibkr-gotchas.md); (b) a `whatIfOrder` margin and commission check inside the order door; (c) multi-day drawdown lock and stop-out pause, only when an unattended loop is chosen; (d) round limit prices to the contract's `minTick`. None started.
3. **Then, in the owner's order:** a real strategy idea judged by `tempo.evidence`, paper trading of the survivor, a data subscription only if a strategy needs live intraday data, an unattended loop, a scanner with filters (see [foundations-plan.md](foundations-plan.md)).
4. **Routine:** run the live suite after any change to order code; update the market calendar from the NYSE page each December (entries are refused after 2027-12-31).

## Gate before real money

The numbers are pre-registered in `evidence/gate.json` and are checked by hand. An automatic checker was removed on 2026-11-02 because nothing produced the numbers it would check; build one when paper trading exists.

- Two to three months of paper results that stay positive after commissions and conversion costs, and match the backtest.
- The kill switch and daily loss limit tested.
- Employer compliance and study-permit/tax rules checked.
