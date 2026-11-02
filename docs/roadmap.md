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

State: **long 1 SPY** (average cost 760.64 USD) left over from the overnight test. Sell it in the regular session.

## Next

1. **Monday 09:30 ET, about 10:00:** sell the 1 SPY with a market order; record the fill, commission, and CAD/USD cash changes.
2. **Lifecycle tool:** one command that buys, confirms the fill, sells, and reports P&L and cash by currency.
3. **Order management:** bracket orders (parent, take-profit, stop) so stops rest at IBKR; trailing stops optional.
4. **Kill switch:** cancel all orders and flatten all positions.
5. **Data:** intraday bars stored locally, downloaded within IBKR pacing limits; decide on a live data subscription (the US exchange bundle is about 4.50 USD/month, unverified).
6. **Backtester** with commissions (1 USD per order seen), USD/CAD cost, and slippage; avoid survivorship bias.
7. **Strategy research:** one or two simple strategies, judged on data they were not tuned on.
8. **Safeguards:** daily loss limit, max open positions, no new trades near the close, position reconciliation.
9. **Gap scanner:** IBKR's built-in scanner (`TOP_PERC_GAIN`, `STK.US.MAJOR`); test whether it works without a subscription.
10. **Unattended loop:** scheduler, market calendar, logging, restarts (Docker + IBC), Telegram alerts.
11. **Journal:** ledger of every trade plus a short "learnings" file, in R-multiples.

## Gate before real money

- Two to three months of paper results that stay positive after commissions and conversion costs, and match the backtest.
- The kill switch and daily loss limit tested.
- Employer compliance and study-permit/tax rules checked.
