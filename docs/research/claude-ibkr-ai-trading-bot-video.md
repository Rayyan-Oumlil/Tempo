# Video notes: "Claude + IBKR API: Complete AI Trading Bot Guide"

- Source: https://www.youtube.com/watch?v=UgWQtQ3MEVE (transcript via tactiq.io; the video itself was not watched)
- Creator: a discretionary momentum day trader, self-described as having no coding background
- Disclosure: sponsored by BetaPro (leveraged ETFs), mentioned mid-video
- Notes written: 2026-11-01

## One-paragraph summary

She connects Claude (Claude Code / desktop) to an Interactive Brokers **paper** account through Python, then has Claude generate a full intraday bot: a rules file for her "Trend Join Long" strategy, an S&P 500 gapper scanner, a 30-minute decision loop, order management (stop, partial, break-even, trail, forced close), Telegram alerts and an R-multiple dashboard. The most useful part is her closing admission: the strategy that backtested very well on TradingView performed "meh" once automated through the IBKR API, and she still trades it better by hand.

## Her setup

| Step | What she did |
|---|---|
| Broker | IBKR paper account, Trader Workstation (TWS), API socket on **7497** (live would be 7496) |
| API settings | Enable ActiveX and Socket Clients, trusted IP 127.0.0.1, **Read-Only API unticked** so it can trade |
| Environment | Python 3.12+, Claude on a paid plan, a fresh Claude project |
| Permissions | Claude **auto mode** (no permission prompts), because prompts every 10 seconds annoyed her |
| Connection test | Asked Claude for open positions and buying power, then had it place a 1-share NVDA limit buy at $100 (far below market, so it can't fill), then cancelled it |
| Paper balance | Started with CAD/USD 1,000,000; she advises resetting to about 10,000 |

Gateway showed a "simulated trading, enable API orders" confirmation popup on the first API order.

## The strategy ("Trend Join Long", long-only, 5-minute chart)

- Daily filters: stock above the previous day's high; previous close above the 200-day average.
- Initial stop: 1% below the low of day.
- Take a partial at **0.75R**; move stop to break-even at **1R**; then trail under 5-minute swing lows.
- Risk: **1% of account per trade**, maximum **10% of account** per position.
- Universe in the demo: S&P 500 (she normally trades everything above $1B market cap and $3 per share).
- Scanner: top 20 stocks gapping up more than 3% on the day; 503 tickers screened in about 14 seconds.

## The pipeline Claude built

1. `rules.json`: the strategy rules as data.
2. Settings file: IBKR port, position limits, account info, Telegram token.
3. Universe list (`SP500_tickers`) and a morning pre-filter (gappers).
4. Watchlist file refreshed every 30 minutes.
5. Decision loop every 30 minutes during market hours (Eastern time): scan, decide, place entries, manage exits, force-close before the close.
6. Telegram alerts: scan lists, entries, exits, partials, trailing stops, end-of-day summary.
7. Dashboard tracking R-multiples per trade.

## Her own numbers

| Claim | Where it comes from |
|---|---|
| 64% win rate, profit factor 2.48, max drawdown 7%, total P&L 12% | TradingView backtest in her previous video, S&P 500 stocks only, limited timeframe |
| Live automated results "very meh" | Her own statement at the end |
| Her manual trading of the same setup beats the bot | Her own statement |

## Why backtest and live diverged (her reasons, plus mine)

Her reasons:
- The backtest used a limited timeframe.
- She hasn't managed to turn her manual execution judgment into precise code.

Mine (inference, not from the video):
- A 30-minute decision loop on a 5-minute-bar strategy misses entries and exits that the backtest assumed were instant.
- Backtests assume fills at the bar price; real market and stop orders slip.
- Ending a 5-minute strategy's decisions on a 30-minute clock means trailing stops under 5-minute swing lows are only recalculated every 30 minutes unless the stop is a resting order at IBKR.

## Red flags and cautions

- **Sponsored video** promoting 3x leveraged ETFs. She does note they reset daily and aren't for holding.
- **No verified track record.** Backtest numbers are from a prior video and she says live results are worse. No live P&L is shown.
- **Auto mode with a trading API.** Fine on paper; risky near real money. Tempo stays read-only by default.
- **Vague on the "brain".** The decision logic is whatever Claude generated from a prompt; she says she doesn't read the code. Nothing in the video shows tests or review.
- **Scanner speed claim.** 503 tickers in 14 seconds is faster than IBKR historical data pacing allows (see below), so the data likely came from another source. The video doesn't say.

## What applies to Tempo

| Her step | Tempo today |
|---|---|
| Connection | Same idea; Tempo uses IB Gateway (port 4002) instead of TWS (7497), via `ib_async` |
| Read-only unticked | Tempo keeps **Read-Only API on** until we build order placement behind an explicit flag |
| Test order: 1 share, far limit, cancel | This is exactly the order round trip we planned next |
| Paper balance reset to about 10k | Yours is already about 5,000 CAD, which is realistic |
| Gapper scanner on 500 tickers | Needs data. Tempo has no live market data on paper (IB error 10167, snapshot perms NO_TOP). A pre-market gap scan needs live or at least reliable delayed snapshots |
| Pacing | IBKR limits: 50 open historical requests; 60 requests per 10 minutes can trigger a pacing violation; 6 identical requests in 2 seconds also trips it. Scanning 500 tickers through IBKR history needs batching or another data source |
| Risk rules | 1% risk per trade of 6,559 CAD is about 65 CAD; 10% max position is about 656 CAD. Small, so share counts will be tiny for expensive stocks |
| Alerts | Telegram alerts are a good later step |

## Ideas worth borrowing, in order

1. Order round trip on paper (place 1 share, watch status, cancel), mirroring her test.
2. Store the strategy as data (a rules file) so rules are separate from code and testable.
3. Compute **R-multiples** per trade from day one; it's the right unit for judging a strategy.
4. Log every decision with the inputs that produced it, so paper results can be audited.
5. Backtest on more than daily S&P 500 data before trusting any rule, and compare backtest vs paper fills explicitly. Her main lesson is that these differ.

## Open questions

- What data source did her scanner use for the gap calculation?
- Are her stops resting orders at IBKR or recalculated by the bot each cycle?
- How many live paper trades are behind her "meh" verdict?
