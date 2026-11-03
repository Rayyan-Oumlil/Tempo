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

## 2026-11-02: daily loss limit (first feature after the hardening pass)

Built on the owner's go-ahead once the hardening list was done. Design from the references: block NEW entries only, never exits (`ibkr-algo-trader` `risk.py`, `ECOSYSTEM_REVIEW.md`), and fail closed on new exposure when the input cannot be read (`mmr` `SAFETY_ROADMAP.md`). The figure is IBKR's own daily P&L (realized plus unrealized, base currency), with start-of-day equity = NetLiquidation minus daily P&L, so Tempo keeps no day-start state of its own. The limit is `max_daily_loss_pct` in `rules.json` (5.0 for now; required, no silent default), applied inside `orders._check_entry` after the cheap checks, so it covers `place`, `lifecycle`, `bracket` and anything else that goes through the order door.

**A live-only bug, caught by comparing against the broker:** the first version returned 0.00% while IBKR's daily P&L was -151.55 (0.0602%). The first `reqPnL` callback can carry a stale figure and the real one follows about a second later, so "first known value" under-reports a loss, which is the unsafe direction for a limit. Fix: always wait 2 s before reading. Two tests reproduce the bug (a stale zero, and "never returns before the settle time"). Without the live comparison this would have shipped passing every offline test.

**Verified live (market closed):** with a limit just below the account's real loss an entry is refused and nothing reaches the broker; with room to spare it is accepted. **Not yet verified live:** the six market-hours checks, including "exits still work when the limit is hit", because the session had closed. They run first thing next trading day.

**Known limits:** the percentage is of start-of-day equity as IBKR defines the day, and deposits would distort it (irrelevant on paper). It measures the whole account, not per strategy. Each new entry costs about 2 s.

## 2026-11-02 evening: second audit, and the first real strategy test is pre-registered

Audit of five more references (freqtrade, thetagang, vnpy, qlib, icli) is in `reference-audit.md`; four hardening gaps are saved in `roadmap.md` for after the live run.

**Research on 12-1 momentum** (web search summaries, not the papers; none of the figures below was checked against a primary text):
- Stocks: Jegadeesh-Titman 1993, about 1% a month before costs on US stocks 1965-89; edge fades after about 12 months. Monthly turnover of about 31-33% makes costs matter, though an AQR-based analysis says costs would need to be 5x live levels to erase it.
- ETFs: unclear. One working paper finds profits on 2-4 year lookbacks; a Copenhagen thesis finds none once bond ETFs are included. No clean 12-1 ETF study found.
- Risk: momentum crashes (Daniel and Moskowitz), worst in rebounds after bear markets. The time-series version (Moskowitz-Ooi-Pedersen) reports Sharpe about 1.0 on futures, but a replication says much of that is volatility scaling.
- Antonacci dual momentum: headline 17.4% a year vs 11.4% (1974-2013) is the author's own backtest on partly non-tradable data; no clean post-2013 out-of-sample study found.
- mmr's own pre-registered 12-1 momentum: Sharpe 0.26 after costs on a survivorship-free universe. That is the realistic expectation.

**Decision:** test it for real, because the goal is a strategy that could make money, not code that runs. Pre-registered in `evidence/momentum_rotation.json` before any ETF other than SPY was downloaded or any result existed. A multi-asset backtester is needed (the existing one is one symbol); it is built test-first. Variants tried: 5. Result will be appended below, pass or fail.

### 2026-11-03: universe amended before any result (data availability)
Downloading the pre-registered universe showed IBKR serves TLT history only from 2016-02 and IEF only from 2017-08 (NASDAQ-listed iShares ETFs lose their older history; confirmed also for BND and SHY, while ARCA-listed AGG, LQD and TIP return 20 years). The common sample would have been 9 years, under the 10-year gate. Changed TLT to AGG and IEF to TIP in `evidence/momentum_rotation.json`; no result existed when this was decided and the choice was made on history length only. Cost: no long-duration Treasury sleeve (it mattered in 2008 and 2022). Every other criterion is unchanged.

### 2026-11-03: result, 12-1 momentum rotation over ten ETFs: FAIL (3 of 5 criteria failed)
Run once, `python -m tempo.rotation_report`, 10 ETFs (SPY QQQ IWM EFA EEM VNQ AGG TIP GLD DBC), 2006-11-08 to 2026-11-02 (19.8 years), costs included, 5 variants tried.

| | CAGR | Sharpe | maxDD | 1st half | 2nd half | orders | costs USD |
|---|---|---|---|---|---|---|---|
| **12-1 top3 (primary)** | 8.4% | 0.62 | -31.8% | 0.45 | 0.77 | 759 | 3,953 |
| 6-1 top3 | 7.1% | 0.50 | -39.6% | 0.41 | 0.60 | 833 | 5,485 |
| 9-1 top3 | 7.3% | 0.54 | -37.0% | 0.27 | 0.81 | 771 | 3,621 |
| 12-1 top2 | 8.2% | 0.57 | -42.3% | 0.29 | 0.83 | 527 | 3,824 |
| 12-1 top4 | 8.7% | 0.67 | -27.0% | 0.54 | 0.79 | 953 | 3,548 |
| equal weight all (benchmark) | 7.5% | 0.58 | -41.9% | 0.38 | 0.85 | 2,223 | 2,374 |
| SPY buy and hold (benchmark) | 10.9% | 0.63 | -54.9% | 0.43 | 0.87 | 1 | 15 |

Negative control (200 same-permutation shuffles): real Sharpe 0.62, shuffled mean 0.48, best 0.87, real beats 84%.

Criteria: FAIL Sharpe above SPY and equal-weight (0.62 vs 0.63 and 0.58: above one, not the other); PASS drawdown shallower than SPY; PASS positive in both halves; FAIL beats 95% of shuffles (84%); FAIL 4 of 5 variants beat equal weight (only 12-1 top3 and top4 do).

**What it says.** Momentum rotation made less money than buying SPY (8.4% against 10.9% a year) at about the same risk-adjusted return (Sharpe 0.62 against 0.63) and with a much smaller worst drawdown (-32% against -55%). That is the same trade the SMA 200 test showed: less return for less pain, not an edge. It did not beat plain equal weight by a convincing margin, and it did not beat the shuffles. Consistent with mmr's pre-registered 12-1 momentum at Sharpe 0.26. No retuning was done and none is allowed: the registered verdict stands as FAIL.

**Limits of this test.** Survivorship bias flatters it (all ten ETFs still exist). AGG is missing about 30 days, so those days were dropped for all assets. No long-duration Treasury sleeve (see the amendment above). Cash earns 0.

## 2026-11-03: strategy scan after the momentum failure (reading, no code)
Read in `Trading/reference/`: mmr `STRATEGY_EVALUATION.md` and `RESEARCH_LOG.md`, pysystemtrade docs, Lean's `Algorithm.Python` examples. Searched the literature for two ideas (summaries only, not the papers).

**mmr's record (their own paper and backtest work, not independently checked):** every price-derived signal failed or had a low ceiling (opening-range breakout: Sharpe 3.46 in the sweep, +0.097% walk-forward, buy and hold +13.97%; "more price-derived signals will not raise the ceiling"). Their ONE construction that beat its benchmark was a long-only small-cap or high sales-to-price tilt, equal weight, monthly, on a point-in-time universe with SEC filings (Sharpe 1.15 to 1.26 against 1.04 for equal weight of the same names; gains held after pricing terminal-loss bias). It needs paid fundamentals data and a ~60-name monthly book, so it does not transfer to Tempo directly. Their own caveat: the claim is the spread over the benchmark in a strong decade, nothing else.

**Lean examples** are API demos, not evidence (`ETFGlobalRotationAlgorithm` is the strategy we just tested). **pysystemtrade** docs describe a framework for futures trend and carry; its performance claims live in a book, not in the repo.

**Literature, two ideas (search summaries):**
- Volatility-managed portfolios (scale exposure by inverse recent volatility): Cederburg et al. (JFE 2020) report real-time versions across 103 equity strategies do not systematically beat the unmanaged ones; a replication found 53 wins for managed against 50 for unmanaged (a coin flip); Barroso and Detzel say it does not survive transaction costs.
- Size premium: it averaged 30 bps a month 1926-1981 and 8 bps 1982-2017; Asness et al. say it is robust once junk is controlled for; a later paper says that depends on the short side and that a generic long-only small-cap tilt earns little.
- McLean and Pontiff (JF 2016): 97 published predictors earn 26% less out of sample and 58% less after publication. Any published edge we test starts from a discount.

## 2026-11-03: where Tempo's cost numbers come from, checked against published sources
Rayya asked whether the cost model rests only on what the paper Gateway reported. It did. What is measured, what was assumed, and what published sources say (IBKR's own pages returned 403 to our fetcher, so IBKR figures below come from search summaries of the IBKR Canada pages; SEC from the SEC advisory):

| Item | In `Costs()` | Evidence |
|---|---|---|
| Commission 0.005 USD/share, min 1.00 | measured on paper fills (1.00 USD on 1 share; 7.70 USD on a 300-share round trip) | Matches IBKR Canada **Pro Fixed**: 0.005/share, min 1.00, max 1% of trade value. IBKR Pro **Tiered** is 0.0035/share, min 0.35, plus pass-through fees. IBKR Lite ($0) is for eligible US and Singapore clients, not Canadians. |
| Sell-side fee 20.6 per million | inferred from paper fills | **Confirmed**: SEC Section 31 rate for fiscal 2026 is 20.60 per million, effective 2026-04-04 (it was 0 before that date), per the SEC fee rate advisory. |
| FINRA trading activity fee | **not in the model** | Reported (secondary sources) as 0.000195/share sold, capped at 9.79, from 2026-01-01; a FINRA filing (SR-FINRA-2026-021) proposes pausing it 2026-10-01 to 2026-12-31, status unconfirmed. About 0.0025 USD on a 13-share sale: negligible. |
| Slippage 1 bp each way | **assumed, never measured** | The largest cost line for larger positions, and the least known. |
| Market data | not in the model | Non-professional US streaming about 4.50 USD/month (secondary); a day-trading setup with depth data is quoted at 15 to 40 USD/month by one blog. Check IBKR's page. |

**Caveats.** Third-party pages claim IBKR paper accounts charge no commissions; our own account did charge 1.00 USD, so that claim does not match what we saw. Whether the paper plan equals the live plan is not established: the real account's pricing plan (Fixed or Tiered) must be read in Client Portal. Under Tiered the order minimum falls from 1.00 to 0.35 but exchange and clearing fees are added, which would cut small-position costs, not remove them.

### 2026-11-03 (later): what I stated that was sourced, inferred, or invented, after Rayya asked
**Sourced (primary or academic):** Barber and Odean (Taiwan: over 8 in 10 day traders lose in a typical six months); Chague et al. (Brazil: of those who persisted over 300 days, 97% lost); McLean and Pontiff 2016 (97 predictors: 26% lower out of sample, 58% lower after publication); Cederburg et al. 2020 (volatility management); SEC Section 31 advisory (20.60 per million from 2026-04-04); FINRA/SEC removal of the $25,000 day-trading minimum (effective 2026-06-04, brokers phasing in). Read directly from files: mmr's own results (its Sharpe 0.26 for 12-1 momentum, the opening-range breakout post-mortem).
**Sourced but weak (vendor blogs, forums, search summaries):** IBKR commission schedules (IBKR pages returned 403; figures from search summaries of IBKR pages), market-data prices (4.50 vs 15 to 40 USD per month, sources conflict), "80% of backtests fail live", "90% underperform in year one" (attributed to FINRA with no FINRA source found: NOT used), "8 to 15% realistic after costs", "10 to 15% of day traders profitable per year".
**My own arithmetic, resting on assumed inputs:** the round-trip and monthly cost tables (Fixed plan, 1 bp assumed slippage; "4.4% a month to break even on 10,000" is arithmetic, not a finding).
**My own judgment, unsourced:** the "honest odds" in the shortlist, the 4-row income outcome table, "simple rules rarely beat SPY" (consistent with the weak sources, not proven by them), the suggestion to treat Tempo as finished after one or two failed tests.
**Not researched at all:** Canadian tax treatment of frequent trading, employer rules, IBKR Canada account-specific plan and fees.
**Cannot be measured on paper:** real slippage and queue position. Practitioner sources agree paper fills are too clean. Only small live trades measure it.

## 2026-11-03, 09:55 ET: live suite after the exit-room fix and the daily loss limit
Run 1: 7 errors, `ConnectionError` (port open, API handshake timed out; `tempo.health` connected about a minute later, so Gateway was likely still syncing after login). Run 2: 6 passed, 1 error (`TimeoutError` in `test_a_crashed_process_is_reconciled_from_a_fresh_connection`; traceback not saved, cause unknown; the test passes alone in 9 s). Run 3 (output kept): **7 passed in 94 s**. Account flat, no open orders, journal 0 unresolved after every run. Result: the two changes that were only proven offline (OCA-aware exit room, daily loss limit including "exits still work when the limit is hit") are now proven against the real broker. Unexplained: the one intermittent timeout. If it recurs, capture the full traceback before anything else.

## 2026-11-03: broker rejection reasons in the journal (hardening gap 1 from the reference audit)
Idea from thetagang's order supervision. First version read the error from `trade.log` (ib_async 2.1.0 puts an error code there). **Compared against the real broker, it would have missed the main case:** a 201 rejection (20,000 SPY, far over the account's margin) arrives as status `Inactive` with no error code in `trade.log`; the code exists only on `ib.errorEvent`. 110 and 391 appear in both. 202 ("Order Canceled - reason:") has a blank reason and is also sent for our own cancels, so my planned "cancelled by broker" label was unprovable and was dropped. Final design: a per-connection `errorEvent` listener stores the last informative error on each trade; `record_outcome` journals `reason_code`, `reason_kind`, `reason_text` for orders that did not fully fill. Also learned: a module-level registry keyed by (clientId, orderId) collided across tests (the fake reuses ids), so the listener keeps its state per connection. One probe of mine crashed on the duplicate-order guard (identical order inside the window), which is that guard working. Live: 4 of 4 cases matched IBKR; new permanent live test; full live suite 8 of 8; 385 offline.

## 2026-11-03: what people actually build with Interactive Brokers and Claude (scan of the references plus a GitHub search)
Method and limits: read the READMEs and research files of the cloned repos (agentic-trading-mcp/Valet, quant-trader, ibkr-algo-trader, mmr, thetagang, icli), read the READMEs of six more repos found by `gh search` (13 IBKR/MCP/Claude projects in total, a small and search-biased sample, not the whole world), and counted strategy words in the code. Keyword counts are crude and only used as a hint.

**Finding 1: public IBKR plus Claude work is mostly plumbing, not strategies.** Most hits are MCP connectors for account monitoring, read-only portfolio tools, or order execution behind guards (code-rabi/interactive-brokers-mcp, the most starred at 228, says "Alpha state" and offers read-only mode). Several say outright that the decision stays with the human or the prompt (Valet: "the investment decision stays with you"). None of the 13 publishes verified live P&L.

**Finding 2: where a style is visible, it is not day trading.**
| Project | Style (from its own docs) |
|---|---|
| Valet plus Vizier skill | Research-driven, multi-horizon (`core` long-term and `tactical`), human in the loop, a deliberate ladder: shadow (journal only) to paper to live read-only to real-money autonomy last |
| mmr | LLM proposes, human reviews, then approves; ATR-based sizing; its own research found intraday strategies failed and its one survivor is a slow monthly tilt |
| quant-trader | Daily workflow (morning brief, intraday monitoring, end-of-day summary), classic indicator strategies, decision support, no results reported |
| thetagang | Options income (the wheel) and portfolio rebalancing; the most starred IBKR-specific bot we found (about 2.8k) |
| axiom-iq-labs ibkr-mcp-server | The only day-trading-flavoured one: 0DTE SPX options MCP, 7 stars, no results |
| icli | A manual command-line tool for fast discretionary trading (scalping and 0DTE keywords), human-operated |
| ibkr-algo-trader | Built a 5-minute intraday bot, then its own `RESEARCH.md` concluded: paper P&L is an upper bound with near-zero live predictive power (IBKR paper fills are top-of-book simulations, delayed data makes 5-minute signals stale), retail day-trader base rates are devastating, the only intraday template with positive claims is opening-range breakout with a relative-volume filter and that evidence is practitioner-grade; the best-evidenced item in its five research reports is inverse-volatility scaling (which Cederburg et al. dispute) |

**Finding 3 (my inference, not a source):** Claude-driven trading clusters at slow horizons (days and longer, human approval) because intraday needs real-time data, low latency and honest fill models that retail IBKR paper accounts do not provide. The builders who did try intraday documented why it is unreliable.

**For Tempo:** nobody in this sample combines a hard order door with pre-registered, honest strategy testing; that is Tempo's niche. Two ideas worth taking: Valet/Vizier's autonomy ladder (a shadow mode that journals decisions without orders), and ibkr-algo-trader's rule to count a resting limit as filled only if price trades through it by at least a tick.

## 2026-11-03: pairs trading pre-registered (before any data was downloaded)
Reordered from the earlier plan: the pairs test goes before shadow mode, because shadow mode has no strategy to feed yet and would be infrastructure ahead of need. Literature (search summaries, papers not read): Gatev et al. (1962-1997) found positive returns; Do and Faff extended to 2009 and found a downward trend, and with commissions, market impact and short fees pairs profits stay positive but much more modest; a review says after realistic costs the distance approach largely disappears in recent years outside turbulent periods. IBKR borrow: annualized, charged every calendar day, can change intraday and general-collateral names can turn hard to borrow; one academic study puts general-collateral fees around 17 bps on average (older sample), so 0.3% is a conservative assumption, 1.5% the stress case. Everything is fixed in `evidence/pairs_trading.json`: ten pairs chosen by industry rationale, one primary rule plus four fragility variants, eight pass criteria. Stated expectation: FAIL is the likely result. Result will be appended below, pass or fail.
