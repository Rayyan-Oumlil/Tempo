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

**Hardening only, by decision (2026-11-02).** Done: bracket take-profit seen firing, journal lock, `smoke` and `size` tested, calendar through 2027, reference-price question settled by measurement, and a repeatable live suite (`TEMPO_LIVE=1 pytest tests/live`, five checks, passed twice).

What remains is small. In order:
1. **Run `TEMPO_LIVE=1 pytest tests/live` after every change to order code**, and once on each new trading day before trusting the tools.
2. **Update the calendar from the NYSE page each December** (the code refuses entries after 2027-12-31).
3. **Review the accepted limitations** in [research/log.md](research/log.md) before building anything on top: two oversize exits together, manual `--accept-missing` for cancelled orders, estimated backtest costs.

Features that wait until the owner says hardening is done: daily loss limit, a real strategy, data subscription, unattended loop, scanner (see [foundations-plan.md](foundations-plan.md)).

## Gate before real money

The numbers are pre-registered in `evidence/gate.json` and are checked by hand. An automatic checker was removed on 2026-11-02 because nothing produced the numbers it would check; build one when paper trading exists.

- Two to three months of paper results that stay positive after commissions and conversion costs, and match the backtest.
- The kill switch and daily loss limit tested.
- Employer compliance and study-permit/tax rules checked.
