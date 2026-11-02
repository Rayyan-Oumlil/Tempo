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
| Gateway probe, 2026-11-02: market data limits, history depth, scanner, order types and rejections, shorting, brackets and OCA, kill switch, fees, FX | Findings in [ibkr-gotchas.md](ibkr-gotchas.md) |

State: **flat**, no open orders.

## Next

Detailed in [foundations-plan.md](foundations-plan.md), built from the [reference audit](research/reference-audit.md). A data subscription is only needed for live intraday work (quotes and bars are about 15 minutes delayed); 20 years of daily bars are free.

1. **Phase 1, one door for orders:** `orders.place` plus an append-only journal (intent before send).
2. **Phase 2, stop button:** `normal / reduce_only / halt` state, `tempo.kill` (global cancel, flatten longs and shorts, verify flat). Exits are never refused.
3. **Phase 3, reconcile at startup:** journal against open orders and executions; block trading until they agree.
4. **Phase 4, brackets:** parent, stop and take-profit in one OCA group; never cancel one leg.
5. **Phase 5, evidence harness:** pre-registered gate, backtester with measured costs, negative control, research log.
6. **After that:** strategy research on daily bars, safeguards (daily loss limit that blocks entries only), data decision, scanner with filters, unattended loop (Docker), journal in R-multiples.

## Gate before real money

- Two to three months of paper results that stay positive after commissions and conversion costs, and match the backtest.
- The kill switch and daily loss limit tested.
- Employer compliance and study-permit/tax rules checked.
