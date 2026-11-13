# Plan v2: making Tempo a research instrument that can actually find (or kill) an edge

Written 2026-11-12 night, after the first full paper day. Replaces nothing: `plan-argent-reel.md` (gates to real money) and
`plan-vps-edge.md` still stand. This plan is about the **research engine**, from the point of view of someone who has to
decide where 20,000 USD goes and wants to know, honestly, whether anything here earns more than it costs.

Evidence tags used below: **[P]** primary paper or official page seen in search results; **[S]** secondary source (blog,
summary, broker page) to be verified before relying on it; **[J]** my judgment, not a finding. Links are at the end.

---

## 0. The three facts that shape everything

1. **Base rates are hostile.** Published anomalies lose roughly a third of their return after publication [P: McLean-Pontiff,
   97 predictors, about 35%]. Of 447 replicated anomalies, 64% fail at the 5% level once microcaps are handled (value-weighted,
   NYSE breakpoints) and 85% fail at t >= 3 [P: Hou-Xue-Zhang]. A new factor should clear t > 3 [P: Harvey-Liu-Zhu]. Over 80% of
   day traders lose money after costs, with a small persistent minority [S: Barber-Lee-Liu-Odean via summaries]. Every source we run
   is a textbook anomaly on large caps, the most efficient part of the market. Prior that any one of them nets more than its
   cost, forward, at our size: low (I would say 5% or less per source; [J]).
2. **Our instrument cannot see small edges.** Forward tests need t > 2.8 on daily means. With an illustrative daily-mean standard
   deviation of 1.2% (a guess until we have 20 signal days), 120 signal days detect only an edge of about 0.31% per 5-day trade
   (2.8 x 1.2 / sqrt(120)). An edge of 0.10% needs about 1,100 signal days: four and a half years. So a null result will mean "no
   LARGE edge", not "no edge". Two levers only: **lower the noise** (market/sector neutral book, fewer macro-dominated days) and
   **raise the breadth** (more independent bets), or **get prior information from history** (section 3, workstream C).
3. **At 20,000 USD the commission floor is the strategy, and the pricing tier decides where it sits.** Fixed tier: 0.005 USD/share,
   1 USD minimum per order [S: IBKR]. **Tiered tier: 0.0035 USD/share, 0.35 USD minimum, plus pass-through clearing, regulatory
   and exchange fees [S: IBKR pages; the Canadian comparison page lists them separately]** (review feedback, 2026-11-12). At a 2,000 USD
   position Fixed costs about 10 bps round trip; Tiered about 0.8 to 1.0 USD, or 4 to 5 bps (my estimate from the listed fees,
   [J]). The commission floor, the position size below which commission exceeds about 11 bps, drops from about 1,800 USD (Fixed)
   to about 800 USD (Tiered). Grinold's law (IR ~ IC x sqrt(breadth)) [S] says many small bets win, but only if independent and
   cheap; under Tiered the live book can plausibly hold 15 to 20 positions instead of 8 to 10. A **selection layer** (rank
   signals, take the top K) is still needed and does not exist yet. Which tier the live account uses is a choice to make at
   account opening; the paper account does not enforce either.

---

## 1. The questions I asked, and what came back

| # | Question | Answer (confidence) | Consequence for Tempo |
|---|---|---|---|
| 1 | Does post-earnings drift still pay? | Weakened over decades, concentrated in small, low-coverage, high-friction stocks [P: Johnson-Schwartz, Ng-Rusticus-Verdi]; a 2021 working paper argues large-cap drift is gone within 5 days [S: Martineau, WP]. No recent net-of-cost estimate by size found. | Keep the large-cap `earnings_reaction_v1` as a **negative control** and `earnings_reaction_small_v1` as the real test. If both drift, suspect the method. |
| 2 | Do analyst rating changes pay after costs? | Gross returns exist only with daily rebalancing; **net returns were not reliably above zero** [P: Barber-Lehavy-McNichols-Trueman 2001]. Prices anticipate revisions up to 3 days before [S, unidentified thesis]. | `analyst_actions_v1` has the weakest prior. Keep it for the data it generates (execution, news), not as an expected earner. |
| 3 | Is daily short volume informative? | Heavily shorted stocks trailed by 1.16% over 20 days; **institutional non-program shorts** carry it [P: Boehmer-Jones-Zhang 2008]. Stronger for low-liquidity, high-borrow-fee stocks [P: Boehmer-Huszar-Zhang]. | Our feed (FINRA daily total) mixes market-maker flow with informed shorts, and the effect lives where borrow is expensive. Log shortability and fee (see A3) or the short leg is graded on trades we could not make. |
| 3b | How expensive is borrow in our universe? | **Measured 2026-11-12 on IBKR's own short-stock file:** S&P 500 median fee 0.41% a year, maximum 1.42%, only 2 of 501 names above 1%. Small names are the opposite: ASPE 38% a year (negative rebate), LYCA 24.5%; 5,666 of 19,725 listed symbols exceed 5%. | Borrow is irrelevant for the large-cap sources and decisive for the small-cap earnings and insider sources. Daily snapshots now built (`tempo.snapshots`, `ibkr_shortstock/`). |
| 4 | Is the IV-spread/skew signal real? | Predicts weekly returns [P: Cremers-Weinbaum, Xing-Zhang-Zhao], but **at least two thirds of it disappears when high-borrow-fee stocks are excluded** [P: Pearson-Pollet, JFE 2025]. | Same confound as Q3. Do not build an options signal before borrow-fee logging exists. |
| 5 | Do insider purchases pay? | Opportunistic insiders: 82 bps/month value-weighted; routine insiders about zero [P: Cohen-Malloy-Pomorski 2012, sample to 2007]. Nothing found on decay since. | `insider_opportunistic_v1` has the best-supported prior. Hygiene rule needed: exclude IPO/SPAC allocations (our own data: the +3.9% was four such names). |
| 6 | Do headline news change what to expect? | Bad public news drifts, extreme moves **without** news reverse; mainly small, illiquid stocks [P: Chan 2003 abstract]. | A testable large-cap hypothesis with a free feed: see B4 `news_split_v1`. |
| 7 | Do short-term reversals pay, and when? | Reversal profit is liquidity provision, strongly predicted by the VIX [P: Nagel 2012]. | `weekly_reversal_v1` should be conditioned on VIX and on the no-news filter, not run unconditionally. |
| 8 | Are LLM-read-news signals trustworthy? | Look-ahead and entity-memory contamination are real [P: Glasserman-Lin]; a chronologically clean model showed modest bias [P: He et al.]; out-of-sample horizon is short [P: Gao et al.]. | Forward ledger only (what we do). Not spending API money is the right call for now. |
| 9 | Do event-premium trades (pre-FOMC drift) still work? | Drift essentially vanished after 2015 in one extension [P: Kurov-Wolfe-Gilbert]; mixed elsewhere. | Do not add. Calendar anomalies decay fast and have 8 events a year. |
| 10 | Is a variance-risk-premium sleeve worth it? | Positive but modest net of cost; cash-secured puts show deeper drawdowns; reported Sharpe ranges 0.06 to 0.77 depending on source quality [S]. | A risk premium, not alpha. Park it until the core engine is trustworthy. |
| 11 | How should the multiple-testing problem be handled? | Deflated Sharpe and minimum track record length [P: Bailey-Lopez de Prado]; always-valid sequential p-values allow peeking without inflating error [P: Johari et al., mSPRT]. | Replace "wait for n=120 then read t" with sequential monitoring plus a deflated-Sharpe report across all live sources (A2). |
| 12 | How aggressively to size a tiny, uncertain edge? | Estimation error dominates below about 50 trades; overbetting is penalised far more than underbetting; practitioners use a half to a quarter of Kelly [S]. | No Kelly until a source has at least 50 scored trades; then a quarter of Kelly on the **lower confidence bound** of its edge. Until then, equal risk. |
| 13 | Does the daily spread curve matter for 09:40 entries? | Spreads are U-shaped, widest at the open and close [P: Chan-Chung-Johnson 1995]. Nothing found for the first 15 minutes of S&P 500 stocks specifically. | Measure it ourselves (A3, D1). Do not assume 09:40 is optimal or terrible. |
| 14 | Can paper results be trusted for cost? | Paper fills are idealised; liquidity and slippage are not modelled; borrow-fee treatment unconfirmed [S]. | Paper measures plumbing only (already our stance). Real cost needs a small live period. |
| 15 | What changes for a 20,000 USD margin account? | The SEC approved FINRA's Rule 4210 change on 2026-04-14: the 25,000 USD pattern-day-trader minimum is gone; the 2,000 USD margin minimum stays; broker rollout through Oct 2027 [S: several brokers; verify FINRA Reg Notice 26-10 and IBKR's own policy]. | One-day-hold sources become feasible at our size, if IBKR confirms. |
| 16 | Canada, FX and tax? | IBKR FX conversion is far cheaper than bank brokerages [S, broker marketing]; frequent trading can be business income (T2125) rather than capital gains, treatment must stay consistent year to year [S]. | Gate item, not research: ask a tax professional **before** real money; the employer's personal-trading policy is the harder gate (already in `plan-argent-reel.md` 1.1). |

**What I could not confirm** (open, not assumed): net-of-cost PEAD by size in the 2020s; first-15-minute spreads for S&P 500
stocks; whether large-cap earnings gaps fade or continue intraday (the Gao-Han-Li-Zhou intraday-momentum paper did not surface);
IBKR's API route for shortable shares and borrow fee (the search did not confirm a specific tick; check the API docs);
post-2001 evidence on analyst-revision drift net of costs; how IBKR paper treats borrow fees.

---

## 2. What the first day showed (own data, 2026-11-12)

* Ledger and account disagreed per trade by -250 to +577 bps (mean +9, median -11); NVDA's short scored -10.1% in the ledger, -4.1%
  on the account. Fixed by exec_v2 scoring (09:40 entry, 15:45 exit, beta-adjusted).
* One downgrade (Baird, Neutral, target 200 vs price 173.7) produced a short; eight more downgrades followed the CEO-exit news the
  next morning. Direction-only rules read a "downgrade to Hold with a target above the price" as bearish.
* The only positive 5-day insider number (+3.94%, 14 signals, 1 day) came from four IPO/SPAC names with under 40 days of history;
  under exec_v2 it is +0.38% on 10 signals.
* 57% of paper gross sat in the contaminated insider source; the book was net long 25k of 47k gross.

---

## 3. The plan

Order is by information gained per hour, not by excitement. Every new rule is pre-registered in `evidence/` **before** its first
signal; v1 rules are never edited. Kill criteria are written now so we cannot move them later.

### Phase 0: this week (finish the instrument)

| # | Task | Done when | Kill / stop rule |
|---|---|---|---|
| 0.1 | Deploy exec_v2 scoring, analyst feature capture, insider entry stop, SEC-holiday skip (code done locally, 844 tests, mutation checks) | pushed, VPS pulled, first evening job writes exec_v2 scores with no timeout | If the evening `ledger_score` step exceeds 10 min, cache intraday bars to disk |
| 0.2 | Investigate the one flaky mutation survivor in `orders_properties` ("cap uses reference price only"): caught on some runs, not others | either a deterministic test that kills it, or a documented seed/deadline fix | Do not push money-path changes while it is unexplained |
| 0.3 | Verify the PDT change on FINRA Reg Notice 26-10 and IBKR's own page | one paragraph in `docs/runbook.md` with the two links | none |
| 0.4 | Borrow data. **Done 2026-11-12:** IBKR's public file `usa.txt` on `ftp2.interactivebrokers.com` (user `shortstock`, empty password; columns symbol, rebate, fee, shares available) is saved once a day by the late job. The API route also exists: generic tick 236 gives tick type 46 "shortable" [P: IBKR docs]; the threshold meaning (above 2.5 = more than 1,000 shares) is only partly confirmed | snapshot saved daily on the VPS; join fee and availability to every short signal at analysis time | if the file goes stale or unreachable the late job reports it (it does not stop the other sources) |

### Workstream A: the measurement engine (the scarce resource)

| # | Task | Why (from section 1) | Done when |
|---|---|---|---|
| A1 | **[DONE 2026-11-13, `tempo/slippage.py`, in the daily email]** **Reconciliation report**: per trade, account fill vs ledger entry price, vs 09:40 bar, tracking error by source | Q14; the NVDA day | printed in the daily report; alarm if mean absolute gap > 60 bps over 20 trades |
| A2 | **[DONE 2026-11-13 as v1, `python -m tempo.sequential`: entry-day cohorts, Newey-West lag = horizon - 1, approximate mSPRT with HAC variance, MDE, days needed for +1%, deflated Sharpe; true daily mark-to-market version still to do because scores carry only entry and exit prices]** **Sequential reporting**: per source, confidence interval, always-valid p-value, minimum detectable effect at current n, and a **deflated Sharpe** across all live sources. **Method (review feedback, accepted):** run mSPRT on the book's *daily mark-to-market incremental excess return* (one observation per day, uncorrelated under zero alpha), never on overlapping 5- or 21-day trade returns, whose adjacent observations share 80 to 95% of positions and break the i.i.d. assumption. Trade-level means use Newey-West (HAC) standard errors with lag = holding period - 1 | Q11, fact 2 | `tempo.ledger` prints these; the old fixed-n line stays as a reference |
| A3 | **Cost truth**: log, for every signal, shortable flag and borrow fee (from the daily file, 0.4), and implementation shortfall after the fact (fill vs the 09:40 bar). **Spread at order time cannot be measured with the delayed feed** (review feedback, accepted: a 15-minute-delayed quote at 09:40 is a pre-open quote). Real-time quotes cost money: see the decision box in section 4 | Q3, Q4, Q13, fact 3 | shorts without borrow are marked untradeable and excluded from the short leg's score |
| A4 | **Robust beta**: winsorise the 60 return days (earnings gaps inflate it; a shrunk beta of 3.7 appeared for TTMI); compare to a sector-ETF hedge on the same signals | review of exec_v2 | decision logged only after 60 more signal days, never tuned on a result |
| A5 | **Portfolio view**: daily return of an equal-risk blend of all live sources, correlation matrix between sources, effective number of independent bets | Grinold [S]; fact 2 | the blend's cumulative net excess is the headline number, sources are the breakdown |

### Workstream B: signal quality (challengers, registered first, v1 untouched)

| # | Task | Hypothesis and evidence | Kill rule |
|---|---|---|---|
| B1 | **Hygiene filters as a v2**, not an edit: drop signals on names listed under 90 days or with a whole-dollar insider VWAP | IPO/SPAC contamination found in our own data | n/a (hygiene) |
| B0 | **Autopsy discovery bar** (review feedback, accepted with a limit): replace Bonferroni in `tempo.autopsy` with Benjamini-Hochberg at 10% FDR over the cells examined. Reason: 6 features x terciles x 5 sources is about 90 cells, Bonferroni then needs t > 3.45, which no genuine edge reaches in 120 days, and the features (VIX, volatility) are correlated. **Limit:** a cell only *nominates* a challenger; evidence comes from the pre-registered forward test and, where history exists, a Workstream C kill filter first | all sources share one multiplicity family | change lands with tests; the forward test keeps its own bar |
| B2 | **`analyst_actions_v2`**: rating level (to Sell/Underperform vs Hold), target below price, at least 3 firms in the same window, no move of more than 5% in the prior 2 days | features already being stored; Barber et al. says direction alone is not enough | registered only after `tempo.autopsy` flags a cell above the Bonferroni bar, per the champion framework |
| B3 | **Earnings-window guard** for all non-earnings sources: skip a stock that reports earnings inside the holding window | earnings volatility swamps any weak signal; cheap noise reduction (lowers daily-mean standard deviation) | measured effect on the blend's variance after 30 days; keep only if variance falls |
| B4 | **Two separate registered tests, not one with a double condition** (review feedback, accepted): **`news_drift_v1`** (a 5% or larger move with a headline in the window: follow it) and **`no_news_fade_v1`** (a 5% or larger move with no headline **and** a residual of at least 4% against the stock's sector ETF: fade it). The sector residual removes sympathy moves (AMD falls because NVDA guided down: no AMD headline, yet fundamental, not liquidity). Chan 2003 [P] covers small caps; the large-cap test is the new part. Each leg counts in the multiplicity family; together they replace `weekly_reversal_v1`, with the Nagel VIX condition logged as a feature | each leg needs its own pre-registered pass; a dead leg does not kill the other. With 40 to 80 events in 120 days the legs are small samples: report the confidence interval, not only the verdict |
| B5 | **Selection layer**: a single daily score across sources, trade only the top K (K <= 10 at live size) | fact 3 forces it; tests whether ranking adds information | paper-trade top K vs all signals for 60 days; keep only if top K beats the rest net of commission |
| B6 | Log conditioning features on every signal (free): VIX level, market cap, 20-day volatility, headline count, days to next earnings, shortable flag | lets autopsy find cells instead of us guessing | analysed through `tempo.autopsy` with the Bonferroni bar only |

### Workstream C: cheap kill filters from history (days, not months)

The forward ledger cannot answer in under six months. A survivorship-biased history can still **kill** ideas quickly, because the
bias is known: it flatters long legs and understates short legs. A leg that fails on a flattering sample is dead; a leg that
passes proves nothing and still goes to the forward test.

| # | Test | Data (free) | Kill rule (written now) |
|---|---|---|---|
| C1 | `short_volume_v1` ranked z-score, 5-day hold, 2010 to 2025. **Legs evaluated separately** (review feedback, accepted): on a current-constituents sample the long leg is flattered and the short leg understated (bankrupt stocks are missing), so the spread's bias has no known sign | FINRA daily short-volume files since 2009 + IBKR daily bars; point-in-time membership from a public constituent list (for example fja05680/sp500 on GitHub; format not yet checked). **Caveat I add:** a membership list does not give prices for delisted names, and IBKR does not serve them, so some survivorship bias remains even then | drop the source only if **both** legs fail (gross below 20 bps per 5-day trade); a single failed long leg kills the long leg only |
| C2 | Earnings reaction, large and small bands, 2010 to 2025. The condition is the **price reaction** exactly as in `earnings_reaction_v1` (reaction-day move minus SPY of at least 5%, out-of-hours filing); an 8-K 2.02 gives timing, not a consensus surprise, and no surprise data is used | SEC 8-K item 2.02 history with acceptance times | gross drift at 5 days below the cost band (20 bps large, 60 bps small): drop that band |
| C3 | Analyst actions | IBKR headline history (depth limited; check how far back) | if less than two years available, skip and rely on forward data |

### Workstream D: execution and risk (the trader's craft)

| # | Task | Notes |
|---|---|---|
| D1 | Entry-time experiment: for half of one source's signals enter at 10:00 instead of 09:40 (alternate days) | tests the U-shaped spread claim on our own fills; paper cannot measure spread, so combine with A3 quote logs |
| D2 | **Equal-risk sizing, unambiguous** (review feedback, accepted; my first wording mixed dollars and percent): `notional = target daily risk (USD) / sigma20`, capped at a per-name maximum (live: 3,000 USD, 15% of 20,000). If `notional` falls **below the commission floor** (live Fixed about 1,800, Tiered about 800), **skip the trade**; never shrink it into a commission trap. Paper uses the same rule scaled by equity. Needs a dry run against the broker before it touches the order path |
| D3 | **Net exposure cap and beta hedge**: keep net dollar exposure within 10% of equity; hedge residual beta with a single SPY order | the paper P&L then reads alpha, not the market; also lowers daily-mean noise (fact 2) |
| D4 | Sector cap: no more than 15% of gross in one sector | correlated signals inflate apparent breadth |
| D5 | Event-risk log: flag held names with a halt, M&A or executive-change headline; no discretionary action, just a record | NVDA case; builds the sample for a rule later |
| D6 | Marketable-limit orders with the existing price band instead of pure market orders, once A3 shows the spread distribution | do not change before measuring |
| D7 | **Fractional Kelly only after 50 scored trades per source**, quarter-Kelly of the lower bound of the edge | Q12 |

### Workstream E: the real-money gate (unchanged intent, sharper numbers)

All of `plan-argent-reel.md` section 1 stays (employer policy first). Added:
* **Economic reality check**: at 20,000 USD a Sharpe-1 strategy at 10% volatility makes about 2,000 USD a year before costs and tax;
  commissions for 8 to 10 round trips a day (one-day holds) are about 16 to 20 USD a day, 0.1% of the account daily; with 5-day
  holds and 10 live positions it is about 4 USD a day. Any source must
  show its edge **net of the 2 USD per-position round trip at 2,000 USD**, i.e. above 10 bps, before real money.
* **Go-live conditions** (all required): the blend positive net over at least 120 signal days with the always-valid p-value
  below 0.05 after deflation; reconciliation tracking error under 60 bps; borrow handled; one tax and one employer-policy answer
  in writing; the daily loss limit and kill switch tested live; 30 days of live-data (not delayed) paper quotes.
* **Stop conditions** (any one): the blend's 120-day net excess is negative; deflated Sharpe below zero; tracking error above
  100 bps for 20 trades.

---

## 4. Timeline and decisions

| When | What | Decision it feeds |
|---|---|---|
| Next 48 hours | 0.1 to 0.4, A1; start C1 and C2 data pulls | deploy or not |
| 2026-11-18 | first closed 5-day trades; first autopsy rows; first reconciliation | does paper track the ledger within 60 bps? |
| By 2026-12-08 | A2, A3, B1, B3, B6, D2, D3 (dry run first), C1 and C2 verdicts | drop sources the history already killed |
| 2026-12-08 | 31 insider positions exit; first 21-day scores | insider verdict stays provisional |
| Mid-January 2027 | earnings season: first real sample for the small-cap band and B4 | does any event source clear t > 2.7? |
| Apr to May 2027 | 120 signal days for `short_volume_v1` | first honest verdict on the fastest source |

**Expected outcome, stated plainly [J]:** most sources will be dropped, which is a success of the instrument, not a failure.
The deliverable that survives regardless of results is a reconciled, sequentially monitored, cost-aware research engine and a
documented record of what was killed and why.

---

### Decisions that are yours, not mine

| Decision | What I found | My recommendation |
|---|---|---|
| Pay for real-time US quotes? | The review quoted 4.50 USD a month; I could **not** confirm that. The IBKR Canada page lists a "US Securities Snapshot and Futures Value Bundle" at 10 USD a month, waived at 30 USD of commissions. IBKR also offers free real-time streaming from Cboe One and IEX (not the full consolidated quote). Whether a paper account inherits a live account's subscription is unconfirmed, and you have no funded live account of your own | Do not pay yet. First check whether the free streaming works on the paper account (a read-only probe, no cost). Spread measurement (D1) waits for that answer. This breaks your "spend nothing but the VPS" rule only if you choose it |
| Fixed or Tiered commissions at account opening | Tiered cuts the round trip at 2,000 USD from about 10 to about 5 bps (section 0, fact 3) | Tiered, decided with the real fee schedule in front of you at that time |
| Canada: tax and records | Review feedback, **unverified, for a CPA**: log the USD/CAD Bank of Canada rate on every fill (CRA converts each trade to CAD; settlement date is the usual disposition date); on capital account the superficial-loss rule can deny losses on repeated trades of the same names; business-income treatment (T2125) has different rules and must stay consistent year to year | Add the USD/CAD rate to the fill record now (cheap), and put the three questions to a CPA before real money |

## 4b. Structural-events track (second external review, saved 2026-11-13). Status: UNVERIFIED, passive measurement first

**Provenance.** A second AI reviewer, asked to defend or destroy its own first answer. Almost every number is its own judgment [J].
Nothing here changes a live rule. It decides what we **measure** next, with no orders and no real money.

**Verified by me (web, 2026-11-12/13):** SEC exemptive order of 2026-04-16 (10-business-day minimum for qualifying cash tenders, incl. issuer
self-tenders under Rule 13e-4; from law-firm summaries, order text not read); FTSE Russell semi-annual reconstitution in June and December 2026
(December: rank day 2026-10-30, effective after the close of **2026-12-11**); IBKR Canada pays 0% on the first 10,000 USD of cash and
benchmark minus 0.5% above it for IBKR Pro; US 3-month T-bill about 4.16 to 4.30%.
**Claimed verified by the reviewer, not checked by me:** the interest scales with NAV below 100k (about 0.34% blended on 20k; partly matches
the IBKR page wording); SGOV 30-day SEC yield 3.84%; voluntary corporate-action election fee 0 USD and IBKR internal cutoff 12:00 ET the business
day before expiry; Section 302(b)(3) certification decides withholding on tender proceeds.
**Flags I raise on his answers.**
1. His two answers **contradict each other on SPAC yield** (5.5 to 8% first, 4.5 to 5.5% gross second, citing sources I did not see). Treat SPAC
   economics as unknown until measured.
2. He assumes **15% US withholding on SGOV** distributions. T-bill funds usually pay "interest-related dividends", which are exempt from US
   non-resident withholding under IRC 871(k) when the fund designates them (my recollection, [J]). If true, SGOV's after-tax yield is higher
   than his table. Ask IBKR or check the fund's annual 871(k) designation before relying on either number.
3. **His EDGAR script is unusable as pasted**: the paste is corrupted (truncated lines) and the endpoint written as `https://sec.gov` is not the
   full-text-search API (EDGAR full-text search lives under `efts.sec.gov`; verify before use). We write our own collector in the style of
   `tempo/edgar.py` (throttled, compliant User-Agent). Do not run his code.
4. Several keep/drop thresholds (for example "bounce under 60 bps", "win rate over 65%") are invented, not derived. Replace with pre-registered
   rules once event counts exist.

**Conclusions he reached (all [J], to be tested):**
* Hold SGOV (not cash) for anything idle: at 20k, IBKR cash earns about 0 to 0.7%. Baseline about 768 USD/yr pre-tax at 3.84%.
* After switching friction, tax and hours, **no structural strategy reliably beats SGOV by more than 500 USD/yr in the base case**; effective pay is
  about 2 to 13 USD/hour. SPAC trust-floor arbitrage falls to about +190 USD/yr; activist closed-end-fund (CEF) tenders about +680 (high variance);
  issuer odd-lot tenders about +610; spin-offs about +550; Plan v2 core about +250 (low -1,400, high +1,900).
* Operations: IBKR voluntary corporate actions are manual (Client Portal), **no TWS API route to elect, paper accounts cannot exercise them**, shares are
  locked after election, a missed cutoff is the main operational loss. Smallest real-money plumbing test: under 1,000 USD, only after employer
  clearance; observe time to appear in the portal, contra-ticker booking, settlement delay, and whether any tax is withheld.
* Tax (CPA to confirm): selling in the market avoids the Section 301/302 question entirely (no US withholding on capital gains for a Canadian
  resident, treaty Art. XIII). Edge that survives if I only sell in the market: SPAC 50 to 70%, CEF tender 60 to 80%, odd-lot 20 to 40%.
* Statistics for bounded carry trades: with 0 failures in N events the 95% upper bound on failure probability is about 3/N, so evidence needs
  N > 3L/G (L = tail loss, G = expected gain per event). Example: L = 12%, G = 1.8% needs about 20 events; L = 25%, G = 1.5% needs about 50.
* Five weak spots he lists in his own answer: SGOV switching cost (twice the assumed cost removes most of the SPAC edge); CEF deal count (half the
  assumed count fails the 500 USD bar); one 15% gross withholding on a 3,000 USD tender wipes out 75% of a year's profit; deadline risk during lectures
  and exams; unhedged market exposure on CEF tenders.

**My adoption decisions**
| Idea | Decision | Reason |
|---|---|---|
| SPAC trust-floor arbitrage, odd-lot tenders, CEF tenders | **Measure only** (no orders, no code beyond a read-only scanner) | Election-based; cannot run on paper; economics unproven; two of three need a tax answer first |
| Small-cap earnings drift with a borrow-fee veto (`earnings_reaction_small_v1` + `usa.txt` fee <= 3%) | **Keep; add fee, shortable and availability as logged features** on every small-cap signal (no rule edit) | Already running, passive, automated; the veto is a testable autopsy cell and a long-side filter that costs nothing |
| Trend/vol rotation SPY/TLT/GLD (his new idea 1) | **Reject on prior** | Our own pre-registered tactical-allocation test failed 4 of 8; no new evidence offered |
| CEF distribution-cut rebound (his new idea 3) | **Candidate, passive only** | Automated (no election) but unsourced; needs an event count first |
| Russell reconstitution close (2026-12-11) | **Measure passively with 5-minute bars** | Real dated event inside 30 days; no orders |

**Passive measurement calendar (2026-11-13 to 2027-02-11), zero orders.** Dates marked V are verified; others come from his answer and must be
confirmed from the publisher before use.
| Date | Event | Record | Keep/drop rule (to be pre-registered, not his numbers) |
|---|---|---|---|
| Nov 13 to Dec 4 | Russell preliminary add/delete lists (V: reconstitution dates; the list dates are unverified) | list, price, ADV, borrow fee | decide after counts |
| **2026-12-11 close** (V) | Russell reconstitution effective | 15:55 vs close vs next open, per addition and deletion | decide after one sample; no verdict from one event |
| 2026-12-18 close | S&P quarterly rebalance (unverified date) | same | same |
| Continuous | EDGAR SC TO-I (issuer tenders, CEF tenders), SPAC proxy filings (DEF 14A / DEFM14A), Form 10 spin-offs | filing date, offer or trust price, expiry, odd-lot clause, proration, and the **daily market price vs the payout** | event counts per year and the pre-expiry market spread; pre-register after the counts |
| Jan 15 to Feb 11, 2027 | Q4 earnings season | small-cap earnings sleeve with the fee veto | existing ledger rules |

**His decision memo (adopted as a draft, to be tightened).** Next 8 weeks: zero real dollars, no subscriptions; keep Tempo's paper pipeline running;
get exact event counts first. Interim gate on 2027-01-07 (my note: 30 events cannot reach a significance bar; use it as a go/no-go for the next
measurement step only). If anything is ever funded: 5,000 USD active, 15,000 in SGOV, at most 1,000 USD per position, hard stop at -400 USD or
implementation shortfall above 60 bps over 20 live trades. Abandon active trading if: employer policy forces long holds or delays; a CPA says
T2125 business income at a high marginal rate; or the reconciled paper blend fails to clear SGOV plus 150 bps by May 2027. His probabilities:
30% that the automated equity sleeves beat SGOV net of tax over 12 months, rising to 55% if the small-cap earnings sleeve holds above 1% net
through February; over 80% that the project helps a quant or software career [J, his].

**Next actions, in order** (none started):
1. **DONE 2026-11-13: `tempo/events_scan.py`** (read-only, 9 tests; `python -m tempo.events_scan`). The full-text-search host `efts.sec.gov` answers
   HTTP 403 to our client, so the scanner reads EDGAR's quarterly form index instead (every filing by form type, cached per completed quarter).
   **Measured counts of original filings, 2019 to 2026 (2026 is partial):**

   | Form | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
   |---|---|---|---|---|---|---|---|---|
   | SC TO-I (issuer tender) | 464 | 396 | 374 | 384 | 461 | 579 | 577 | 523 |
   | of which name looks like a fund/trust | 357 | 310 | 297 | 276 | 347 | 455 | 476 | 426 |
   | SC TO-I, name not fund-like | 107 | 86 | 77 | 108 | 114 | 124 | 101 | 97 |
   | N-23C3A (interval-fund repurchase notice) | 240 | 265 | 272 | 326 | 358 | 412 | 523 | 555 |
   | 10-12B (Form 10, spin-off or new registrant) | 36 | 16 | 20 | 20 | 19 | 17 | 8 | 19 |
   | DEFM14A (definitive merger proxy) | 221 | 179 | 311 | 246 | 215 | 257 | 235 | 234 |
   | SC 13E3 (going-private) | 25 | 49 | 36 | 43 | 48 | 49 | 35 | 28 |

   **What this already says (my reading, [J]):** the raw counts overstate the opportunity. Most "fund-like" tenders and all N-23C3A notices are
   **non-traded interval or private-credit funds** (no exchange price to trade), and even the "not fund-like" rows include private BDCs
   (2026 sample: Audax Credit BDC, TCW Direct Lending, Apollo Debt Solutions) next to real listed names (Yext, Palo Alto, Wix, iQIYI). The tradable set (listed
   issuer tenders, listed CEF tenders, listed SPAC proxies) is a fraction of these numbers and is **not yet measured**; the reviewer's
   "about 20 to 50 events a year" assumption cannot be confirmed or rejected from form counts alone. Spin-offs: 8 to 36 Form 10 filings a year in total,
   so a spin-off sample is small by construction. **Next step to size it properly:** join each CIK to its SIC code and exchange listing from
   `data.sec.gov/submissions` (about 0.25 s per CIK) and count only listed names. Event data lives in `data/events/events.csv` (not committed).

   **Listed-names measurement (2026-11-13, `python -m tempo.events_scan enrich`, 2,777 filers joined to current SIC and exchange).** The exchange
   field describes the filer **today**, so counts are a lower bound for mergers (an acquired target no longer lists) and for liquidated SPACs.

   | Filed by a filer listed on a US exchange today | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
   |---|---|---|---|---|---|---|---|---|
   | SC TO-I (all) | 79 | 72 | 67 | 59 | 77 | 117 | 61 | 47 |
   | of which operating companies (entity type) | 51 | 44 | 39 | 37 | 39 | 45 | 25 | 21 |
   | DEFM14A (lower bound) | 22 | 27 | 47 | 42 | 23 | 42 | 39 | 97 |
   | 10-12B | 9 | 8 | 15 | 17 | 11 | 12 | 7 | 13 |
   | SC 13E3 | 3 | 2 | 9 | 3 | 4 | 6 | 2 | 13 |

   **Reading ([J]):** listing cuts SC TO-I from about 460 to about 60 a year. 301 of the 579 listed tenders are operating companies (207 distinct
   issuers; 21 to 51 a year), 275 are funds with blank SIC (about 35 a year, the closed-end-fund candidates). Both groups are **below the
   40 to 50 events a year the reviewer's economics needed**, and an SC TO-I includes tenders that are not odd-lot or not priced
   to be attractive (option exchanges, large buybacks). Spin-offs: 7 to 17 listed Form 10 filers a year. Conclusion for the decision memo:
   structural events cannot be a **frequent** source of paid trades at this scale; they stay a passive watch list (capture each listed tender with
   its terms and price) and do not displace the automated sleeves. A filing-level classification (odd-lot clause, price vs market) is the next
   cheap step and needs the document text, not the index.
2. Log `usa.txt` fee, shortable and availability on every small-cap signal; add USD/CAD rate to each fill record.
3. Three questions to IBKR by Web Ticket: Section 302(b)(3) withholding on a Canadian W-8BEN tender; withholding on SGOV (871(k)); whether paper accounts
   can exercise corporate actions.
4. CPA questions (merge with section 4): tender and redemption vs market sale; capital vs T2125; superficial loss; USD/CAD per fill.
5. Employer personal-trading policy in writing (gate in `plan-argent-reel.md`).
6. **DONE 2026-11-13: `tempo/russell_watch.py`** (5 tests; passive, no orders). Verified from the LSEG pages: preliminary additions/deletions published after the US close
   on 2026-11-13, updates 11-20, 11-27 and 12-04, lockdown from 11-30, effective after the close of 2026-12-11. **The pages do not say where the lists are or in
   what format**, so one manual step remains: copy the final list into `data/events/russell/lists.csv` (`symbol,action` with add or delete), then run
   `python -m tempo.russell_watch` after 2026-12-14 and before about 2027-02-01 (IBKR's 5-minute history is two months). It measures runup, day, last5 and
   reverse windows against IWM. One event is one sample: no verdict from it.

## 5. Sources

* SEC order shortening tender periods (law-firm summary): https://www.skadden.com/insights/publications/2026/04/sec-allows-shortened-tender-offer-periods
* FTSE Russell December 2026 reconstitution schedule: https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2026/ftse-russell-announces-december-2026-russell-us-indexes-reconstitution-schedule
* IBKR Canada interest rates: https://interactivebrokers.ca/en/index.php?f=46385
* McLean and Pontiff, "Does Academic Research Destroy Stock Return Predictability?" (JF 2016): https://ivey.uwo.ca/media/3775549/pontiff.pdf
* Hou, Xue, Zhang, "Replicating Anomalies" (RFS 2020): https://www.nber.org/papers/w23394.pdf
* Harvey, Liu, Zhu, "... and the Cross-Section of Expected Returns" (RFS 2016): https://nber.org/papers/w20592
* Bailey and Lopez de Prado, Deflated Sharpe Ratio: https://papers.ssrn.com/abstract=2460551
* Johari et al., always-valid inference (mSPRT): https://arxiv.org/abs/1512.04922
* Boehmer, Jones, Zhang, "Which Shorts Are Informed?" (JF 2008): https://ideas.repec.org/a/bla/jfinan/v63y2008i2p491-527.html
* Cohen, Malloy, Pomorski, "Decoding Inside Information" (JF 2012): https://www.nber.org/papers/w16454
* Chan, "Stock price reaction to news and no-news" (JFE 2003): https://econpapers.repec.org/RePEc:eee:jfinec:v:70:y:2003:i:2:p:223-260
* Nagel, "Evaporating Liquidity" (RFS 2012): https://nber.org/papers/w17653
* Barber, Lehavy, McNichols, Trueman, "Can Investors Profit from the Prophets?" (JF 2001): https://econpapers.repec.org/RePEc:bla:jfinan:v:56:y:2001:i:2:p:531-563
* Pearson and Pollet, borrow fees and IV-spread predictability (JFE 2025): https://ideas.repec.org/a/eee/jfinec/v172y2025ics0304405x25001618.html
* Glasserman and Lin, look-ahead bias in GPT sentiment: https://arxiv.org/pdf/2309.17322
* Kurov, Wolfe, Gilbert, "The Disappearing Pre-FOMC Announcement Drift": https://www.skidmore.edu/economics/documents/KurovWolfeGilbert-TheDisappearingPre-FOMC-Announce-Drift-200914.pdf
* PDT rule change summary (secondary; verify FINRA Reg Notice 26-10): https://www.cmelitegroup.com/knowledge-hub/pdt-rule-2026/
* IBKR securities financing and short availability: https://www.interactivebrokers.ca/en/trading/short-securities-availability.php
* IBKR US stock costs for Canadian residents: https://interactivebrokers.ca/en/trading/us-stock-trading-costs-for-canadian-resi.php
* Barber, Lee, Liu, Odean day-trader studies (author's page): https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf
* IBKR stock-loan file (public FTP): ftp://ftp2.interactivebrokers.com (user shortstock); knowledge base: https://ibkb.interactivebrokers.com/article/2024
* IBKR TWS API tick types (generic tick 236, Shortable): https://interactivebrokers.github.io/tws-api/tick_types.html
* IBKR Canada commissions: https://www.interactivebrokers.ca/en/pricing/commissions-stocks.php
* IBKR Canada market data pricing: https://www.interactivebrokers.ca/en/pricing/research-news-marketdata.php
* Spread intraday pattern (Chan, Chung, Johnson 1995): https://ideas.repec.org/a/cup/jfinqa/v30y1995i03p329-346_00.html
