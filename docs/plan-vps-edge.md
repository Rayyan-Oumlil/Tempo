# Plan: using the VPS to find a real edge (2026-11-11)

Builds on `research/what-people-do.md` (2026-11-03) and the six failed daily-data tests. New searches done today; tags as in that file: [P] paper or summary, [B] blog or vendor, [I] my inference.

## What the new research says

| Question | Finding | Consequence |
|---|---|---|
| Do LLM agents that trade beat buy-and-hold? | StockBench: most agents struggle to beat it; in downturns none did; the best model got +1.9% vs +0.4% with a smaller drawdown [P]. A six-month study of two production agent fleets found no directional edge in either [P]. A leakage-controlled A-share study: returns mostly explained by passive market and style exposure [P]. | **Do not let Claude pick trades discretionarily.** Keep Claude as a text reader whose calls are recorded before the outcome (forward test). |
| Is post-earnings drift still there? | Largely gone for all but microcaps; prices absorb the surprise on the announcement day (Martineau); drift decline tracks falling earnings persistence (Zhao 2022) [P]. | `earnings_reaction_v1` on the S&P 500 is probably a null. Keep it (it is free) but add a size split, and look at small and mid caps. |
| Do congressional trades work? | Post-2012 senator trades show no stock-picking skill; pre-Act edge vanished [P]. One forum backtest says copying after disclosure works (Sharpe 1.05); unreliable [B]. | Low priority. Maybe a cheap collector later; do not build now. |
| Is the volatility risk premium real? | Yes as a premium; option bid-ask spreads can bias estimates, and the open question is how much survives honest execution [P][B]. | Needs option quotes. Paper quotes are delayed and fills are simulated. So: **collect the data now, trade later.** |
| What free data can a VPS gather? | SEC EDGAR (insiders, 13F, FTD), FINRA short interest (twice a month) and daily short volume (free API key), FRED, CBOE/CFTC positioning [B]. | New signal families at zero cost; all runnable as cron jobs. |

## The one structural advantage of a VPS: building your own history

Many free sources show only today's value. A job that saves it every day builds a **point-in-time dataset** that cannot be bought cheaply and cannot suffer look-ahead. In 6 to 12 months Tempo owns data that backtests of the same age could not have. This is a bigger edge than running more cron jobs.

## Plan, in order

**Track 0: protect what exists (this week, 1 to 2 days).** The journal, `state.json` and the ledger's unpushed state live only on the VPS disk and `journal/` is not in git. Add: (a) a nightly encrypted backup to somewhere off the server (private GitHub repo with `age` encryption; the main repo is public so never push raw journals there); (b) a daily "all good" email at 17:00 ET so silence means trouble; (c) restore drill: rebuild from backup on a scratch folder and prove `reconcile` agrees. Without (c) a backup is a hope.

**Track 1: collect, free, no trading (weeks 1 to 3).** Daily snapshots written to `data/snapshots/` and backed up:
1. SPY and QQQ option chains, IV and the VIX curve from IBKR (delayed data is free) for a future volatility-premium test.
2. FINRA daily short volume and twice-monthly short interest for the S&P 500 and a small-cap list.
3. SEC fails-to-deliver files and 13F filings.
4. 5-minute bars for the universe, to measure realistic entry-time costs.
Acceptance: each collector fails loudly, is idempotent, and shows up in the daily email.

**Track 2: signals, at most three new ones, each pre-registered before any result (weeks 2 to 6).** Today six forward tests run (insider cluster, insider opportunistic, Claude earnings, earnings reaction, analyst actions, weekly reversal). Candidates, chosen because the evidence survives or because we can measure it cheaply:
1. Short-volume or short-interest extremes (cross-sectional, 5 and 21 days).
2. Post-earnings drift restricted to small and mid caps, where the evidence says it survives.
3. Volatility-premium shadow test: SPY implied minus realised volatility, recorded daily; hypothetical defined-risk spread tracked, not traded, until Track 1 has 3 months of data.
Rule: no fourth signal until one of the first three is judged. Pre-register means a JSON in `evidence/` with the horizon, cost assumption, universe and kill rule, committed before the first signal.

**Track 3: judge honestly (continuous).** The ledger already prints a power line. Today insider_cluster needs about 1,586 scored signals at its current 1-day effect, roughly 42 weeks. A signal is dropped when it has 100 scored events and t is below 1, or earlier if its sign is wrong with t below -2. Stats on paper results cannot measure slippage; only tiny real trades can.

**Track 4: the real-money gate (not before the evidence exists).** From `evidence/gate.json`: two to three months of paper results positive after costs, kill switch and daily loss limit tested, and compliance checked. Add one item: you work in Capital Markets IT at National Bank, which usually means a personal-trading policy with pre-clearance and reporting. Check that with compliance before any real order, and check study-permit and tax rules. A fast, honest timeline: first real trades (tiny, to measure slippage) around February 2027 at the earliest, only if something has at least 30 scored signals with a positive net result; any scaling decision waits for 100.

## What I will not do
- No LLM discretionary trading and no "AI picks stocks" mode (evidence above).
- No parameter tuning on the forward tests (it breaks the only evidence that cannot be overfitted).
- No real money because a result looks good at 15 signals.

## Open choices for you
1. Approve Track 0 and Track 1 now (they touch no money).
2. Pick up to three Track 2 candidates; my order is short-volume, small-mid PEAD, volatility shadow.
3. Where the encrypted backup goes: private GitHub repo (my pick, free) or a Google Drive folder.
