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
| Gateway probe, 2026-11-02: market data limits, history depth, scanner, order types and rejections, shorting, brackets and OCA, kill switch, fees, FX | Findings in [ibkr-gotchas.md](ibkr-gotchas.md) |

State: **flat**, no open orders.

## Next

Foundations are built ([foundations-plan.md](foundations-plan.md)). What is left before any strategy deserves paper trading:

1. **Daily loss limit** that blocks new entries only (the gate checklist needs it). It plugs into `orders._check_entry`.
2. **A real strategy idea, judged by the harness:** write the idea and the number of variants down first, run `tempo.evidence`, record the result in [research/log.md](research/log.md). The first run (SPY, SMA 200) earned less than buy and hold with a smaller drawdown; it is a baseline, not a finding.
3. **Paper-trade the survivor** for the gate's minimum (100 round trips and 60 trading days), journal every trade, review in R-multiples.
4. **Data decision:** only if a strategy needs live intraday data (quotes are about 15 minutes delayed without a subscription). Verify price and API availability at purchase; TSX data is separate.
5. **Cheap backstops:** dead-man's ping, order-rate ceiling that trips `reduce_only`, price plausibility check, early-close calendar for 2027, no API jobs 23:30 to 01:00 ET.
6. **Unattended loop:** scheduler, logging, Docker Gateway (`AUTO_RESTART_TIME`, 2FA handling), Telegram alerts. Only after 1 to 3.
7. **Scanner with filters** (works without a subscription; raw gainers are micro-caps).

## Gate before real money

The numbers are pre-registered in `evidence/gate.json`; check them with `python -m tempo.gate`.

- Two to three months of paper results that stay positive after commissions and conversion costs, and match the backtest.
- The kill switch and daily loss limit tested.
- Employer compliance and study-permit/tax rules checked.
