# Research log

Append-only. Add new dated entries at the bottom. If an earlier entry turns out wrong, write the correction **underneath it** and leave the original: the reasoning that produced a wrong answer is usually the more useful record.

## 2026-11-02: costs, fees and the first probe

- **Commission is real, in USD, and depends on size.** BUY is 0.005 USD per share with a 1.00 minimum; SELL adds about 0.0157 USD per share at a price near 760 (about 20.6 USD per million sold; likely the SEC fee, inferred). Measured with 1, 10, 100 and 300 share orders. A 300-share round trip cost 7.70 USD.
- **No visible CAD-to-USD markup.** A 300-share round trip's CAD cash change was -18.09 against a net of -12.95 USD at USD.CAD 1.3967 (implied 1.3970). Paper account only; a real account may charge for conversion or interest on a USD debit.
- **Correction (same day):** I first reported market-order latency of about 50 ms. That was wrong. Without an explicit `tif`, ib_async briefly marks the order `Cancelled` (error 10349 notice), so `isDone()` was true before the fill. All Tempo orders now set `tif`.
- **Correction (same day):** I first told the user the day's loss was "a few dollars". After the probes it was 74.70 CAD (about 53 USD), all commissions and spread across about 40 one-to-300 share round trips.
- **Bracket probe:** cancelling the take-profit leg of an OCA pair cancelled the stop too and left the position unprotected. Tempo's bracket tool therefore never cancels one leg.

## 2026-11-02: evidence harness, first run (SPY, 2006-11-07 to 2026-11-02, 19.9 years)

Setup: signal at close t, fill at close t+1; costs 0.005 USD per share (min 1.00), sell fee 20.6 per million, slippage 1 bp (assumed). ADJUSTED_LAST daily bars. One variant tried (SMA window 200, fixed up front by convention, not tuned): **variants tried = 1**.

| Strategy | Total | CAGR | Sharpe | Max drawdown | Orders | Costs (USD) |
|---|---|---|---|---|---|---|
| Flat | 0% | 0% | 0.00 | 0% | 0 | 0 |
| Buy and hold | 679.8% | 10.8% | 0.63 | -55.4% | 1 | 15 |
| SMA 200 trend | 359.6% | 7.9% | 0.72 | -23.6% | 107 | 2,666 |

Negative control (200 shuffled-order versions of the same daily returns): real SMA Sharpe 0.72, shuffled mean 0.47, shuffled best 0.76; the real run beats 99% of shuffles.

**What this does and does not say**
- The trend rule earned **less** than buy and hold (7.9% against 10.8% a year) with a **smaller** drawdown (-23.6% against -55.4%) and a slightly higher Sharpe. It does not beat the market; it trades return for lower risk, a well-known property of trend rules.
- Costs were 2,666 USD on 107 orders against 15 USD for one order, so costs matter for anything that trades often.
- Beating 99% of shuffles is **not** evidence of an edge. Shuffling also removes volatility clustering, and a trend rule benefits from avoiding the big crashes without predicting anything. The gate asks for 95+ as a necessary check, not a sufficient one.
- This is one instrument over one history. Nothing here is a reason to trade money. The harness exists so the next idea is judged by the same rules before it is believed.

## 2026-11-02: hardening pass (no new features)

Decision: stop adding features until what exists is solid. Method borrowed from `reference/mmr/tests/invariants` (a small, literal spec that is never weakened to make code pass) and from the reference audit.

**Proven live on the paper account**
- Reconcile, from a fresh client id after a simulated crash (three orders placed, no outcomes recorded, process killed): the working order was found among open orders, the filled order was found in executions, and the cancelled order was correctly left unresolved. All matched by `orderRef`.
- A stop order fires and fills at IBKR, and its execution carries our tag. Reconcile then journaled 8 fills once (a second run added none).
- The hardened order checks did not break the real tools: roundtrip (a far-below-market limit is still allowed), lifecycle, bracket, kill.

**Bug found and fixed:** the entry size cap used the caller's reference price, not the order's own price. A limit buy priced far above the reference would have been checked at a fraction of its real size. The cap now uses the highest price the order could pay (limit or stop), and a limit more than 10% on the wrong side of the reference price is refused as a likely fat-finger (an idea from `ibkr-algo-trader`'s review).

**Other changes:** reconcile now journals every execution of our orders once, keyed by `execId`, including fills of orders already resolved (a bracket stop or take-profit that fires later). The market calendar fails closed: after 2026-12-31 entries are refused until `tempo/hours.py` is updated. The gate checker (`gate.py`) was removed: nothing produced the numbers it checked. The pre-registered criteria stay in `evidence/gate.json`. Connection and account code, previously 33% and 85% covered, now have tests, and `tests/invariants/` holds six literal invariants.

**Accepted limitations (written down, not fixed)**
- The journal assumes one writer at a time; there is no file lock.
- The reference price is the last daily close; after a big gap the 10% band can refuse a legitimate order.
- Two resting exit orders that are each no larger than the position can together exceed it. Bracket OCA pairs are the intended use, and `kill` and `flatten` cancel before they sell.
- Cancelled orders need a manual `--accept-missing`.
- The sell-side fee rate is inferred and slippage is assumed, so backtest costs are estimates.
- Bracket take-profit firing was not seen live (the stop firing was).

### Update, same day: hardening pass part 2 (corrections and resolutions to the entry above)
- **Resolved: "bracket take-profit firing was not seen live."** It was seen. A marketable take-profit filled at once after the entry, the stop was cancelled by OCA, and the account was flat. Live testing exposed a bug: `confirm_bracket` reported "UNPROTECTED" for that case. Fixed with two tests.
- **New finding:** re-placing a bracket's take-profit from a second connection cancelled it (the stop survived). Bracket legs are not to be modified.
- **Resolved: "the journal assumes one writer."** `place` and `place_bracket` now hold an OS file lock around the checks and the send. Verified across two real processes: while one held the lock, a trade attempt from another was refused cleanly and sent nothing; after release it traded normally.
- **Resolved: calendar ends 2026-12-31.** Extended through 2027-12-31 from the NYSE Group announcement (ICE press release of 2025-12-23), read directly rather than from search summaries.
- **Resolved: `smoke.py` and `size.py` untested.** Both are now covered (every smoke check, both `main` paths, and size's zero-share and bad-input cases).
- **Still accepted:** a stale reference price after gaps, two oversize exits together, manual `--accept-missing` for cancelled orders, estimated backtest costs.

### Update, same day: hardening pass part 3
- **Correction to my own earlier claim:** I wrote that the reference price "is the last daily close; after a big gap the 10% band can refuse a legitimate order". I had not checked. Checked against the broker: during regular hours the newest daily bar is today's, within 0.03% of the delayed quote (SPY 754.84 vs 755.07; NVDA 203.79 vs 204.01). So for regular-hours entries the reference is the latest delayed trade and the gap worry mostly does not apply. It is the previous close only before the open or for `outsideRth` entries. The limitation is struck from the accepted list; no code change was needed.
- **Added: a repeatable live test suite** (`tests/live`, runs only with `TEMPO_LIVE=1` during regular hours). Five checks on the paper account: a lifecycle round trip; a bracket whose stop rests at IBKR and is cleared by `kill`; a marketable take-profit that closes the position and cancels the stop; `kill` closing a long and a short with a resting order; and a simulated crash reconciled from a fresh client id. All passed, twice in a row, and each run leaves the account flat with no open orders.

### Update, same day: limitations review
- **Fixed: two exits that fit alone but not together.** `is_exit` now subtracts what other resting orders on the same side (any client id) have already claimed. Long 5 with a resting SELL 5: a further SELL 1 is no longer an exit, so `reduce_only` refuses it instead of letting two orders flip the account short. If open orders cannot be read the order is treated as an entry. Five tests plus a 100-case invariant; the live suite passed again afterwards.
- **Accepted, now with evidence: cancelled orders need `--accept-missing`.** I tried to find an automatic match. Completed orders from another session return `orderId` 0, `clientId` 0 and an empty `orderRef`; only `permId` remains. No safe key exists, so the manual step stays by design (the same choice agentic-trading-mcp makes).
- **Accepted:** backtest costs are estimates (sell-side fee rate inferred, slippage assumed).
