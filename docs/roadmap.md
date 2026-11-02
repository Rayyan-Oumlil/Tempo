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

**Hardening only, by decision (2026-11-02).** No new features until these are done and the accepted limitations in [research/log.md](research/log.md) have been reviewed.

Done in the hardening pass: reconcile proven live, stop firing proven live, entry cap and price check fixed, fills journaled, calendar fails closed, connection code tested, invariants written, unproven gate checker removed.

Still to harden, in this order:
1. **Watch a bracket take-profit fire live** (the stop was seen firing; the take-profit was not) and confirm the OCA partner cancels and reconcile journals it.
2. **Add a lock to the journal** (or enforce one process at a time) before anything runs unattended.
3. **Tests for `smoke.py` and `size.py`** (0% and 42% covered) or delete what is not used.
4. **Update the market calendar for 2027** from the NYSE calendar before 2026-12-31.

Features that wait until then: daily loss limit, a real strategy, data subscription, unattended loop, scanner (see [foundations-plan.md](foundations-plan.md) and the list in git history).

## Gate before real money

The numbers are pre-registered in `evidence/gate.json` and are checked by hand. An automatic checker was removed on 2026-11-02 because nothing produced the numbers it would check; build one when paper trading exists.

- Two to three months of paper results that stay positive after commissions and conversion costs, and match the backtest.
- The kill switch and daily loss limit tested.
- Employer compliance and study-permit/tax rules checked.
