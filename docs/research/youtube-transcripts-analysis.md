# YouTube transcripts: what's useful for Tempo

Source: the 14 transcripts in [transcripts/](transcripts/) (tactiq.io auto-transcripts, so names and terms are sometimes garbled). Read 2026-11-02.
Reading depth: #00, #01, #02, #05 read in full; #03, #04 and #06-#13 scanned with keyword search, not read end to end.
Several creators sell memberships or are sponsored; treat money claims as marketing.

## The videos

| File | Title | Type | Worth it? |
|---|---|---|---|
| [00](transcripts/00-how-i-built-an-ibkr-trading-bot-with-claude-ai.md) | How I Built an IBKR Trading Bot with Claude AI | Demo of a Claude Code built futures app (gold, micro BTC/ETH). Dated 2026-05-20 | Some practical warnings; the author sells memberships |
| [01](transcripts/01-ai-trading-bot-on-windows-streamlit-ibkr.md) | AI Trading Bot on Windows: Streamlit + IBKR | Dashboard demo, 2025-07-11 | One real gotcha (WSL); mostly promo |
| [02](transcripts/02-how-to-actually-build-an-ai-trading-bot.md) | how to actually build an ai trading bot (full guide) | General bot design, uses Alpaca, not IBKR | Good ideas on bot memory and risk, claims unverified |
| [03](transcripts/03-build-a-python-trading-bot-using-ai.md) | Build a Python Trading Bot for Algorithmic Trading Using AI | Paper bot in a cloud notebook (sponsor: Datalore), TWS port 7497 | Basic; confirms free daily data and costly live data |
| [04](transcripts/04-backtesting-a-strategy-with-ai-generated-code.md) | Backtesting a Trading Strategy in Python With AI Generated Code | Mean-reversion backtest, no IBKR | Useful as a warning (see flaws below) |
| [05](transcripts/05-24-hour-overnight-trading-ibkr-python-api.md) | 24 Hour Overnight Stock Trading with IBKR Python API | ib_async, overnight venue | **Most relevant to what we just did** |
| [06](transcripts/06-ultimate-ibkr-api-tutorial-part-1.md) | The ultimate IBKR API Tutorial Part 1 | Long ib_insync/ib_async fundamentals | Good fundamentals |
| [07](transcripts/07-placing-orders-ib-insync-part-1.md) | Placing Orders (Part 1) | Orders, extended hours, data subscriptions | Useful |
| [08](transcripts/08-async-orders-ib-insync-part-2.md) | Async Into Orders (Part 2) | Client ids, async orders | Useful |
| [09](transcripts/09-real-time-bar-data-part-3.md) | Real-Time Bar Data (Part 3) | Real-time bars; no-subscription errors | Medium |
| [10](transcripts/10-basic-orders-ibkr-python-part-5.md) | Basic Orders (Part 5) | Market/limit orders, error 104 | Medium |
| [11](transcripts/11-trailing-stop-orders-ibkr-python.md) | Trailing Stop Orders | Trailing stops, bracket orders | Needed for our order-management step |
| [12](transcripts/12-conditional-orders-ib-insync.md) | Conditional Orders | Orders conditioned on price, time, volume | Later |
| [13](transcripts/13-scanners-ib-insync-ib-async.md) | Scanners | IBKR scanner subscriptions | Needed for a gap scanner |

## Confirmed by our own testing

- **Overnight (#05):** contract `exchange="OVERNIGHT"`; Gateway **Configure, Settings, API, Precautions: tick "Bypass Redirect Order warning for Stock API Orders"**. This is exactly what fixed error 10329 for us. He also warns of "way less liquidity", which matches our sell never filling.
- **Overnight data (#05):** live ticks, 5-second real-time bars (`useRTH=False`) and historical bars (`useRTH=False`, `keepUpToDate`) all work overnight on an account with market data. We have no live subscription, so we can't see the bid and don't know where a sell would fill.
- **Extended hours (#07):** market orders are not allowed outside regular hours. Use a limit order with `tif="GTC"` and `outsideRth=True`. Same family as our error 387 on the overnight venue.
- **Free data (#03):** daily SPY bars from IBKR are free. Live data costs money. Matches what we saw.
- **Regulatory snapshots cost money (#11, #13):** keep `regulatorySnapshot=False`. Tempo's default already does.

## New, useful things to adopt

1. **Fixed client id (#06, #08).** Orders are only visible to the client id that placed them. A random id breaks order tracking. Tempo uses a fixed 21. A "master client id" or id 0 can see all clients' orders.
2. **Time zone bug (#06).** One creator lost days to a wrong time zone. Store all times as UTC or explicit US/Eastern.
3. **Scanner (#13).** IBKR has a built-in scanner: `ScannerSubscription` with `locationCode="STK.US.MAJOR"` and a scan code such as `TOP_PERC_GAIN`; max 50 rows. This is the proper route to a "gappers" list instead of downloading 500 tickers (which would hit IBKR's historical-data pacing limits). I haven't tested whether it needs a data subscription.
4. **Bracket and trailing orders (#11).** `ib.bracketOrder(...)` builds parent, take-profit and stop-loss orders together, so stops rest at IBKR and survive a crash. Our order-management step should use it.
5. **Kill switch (#00).** A command that cancels all orders and flattens all positions. Add before any unattended run.
6. **Bot memory (#02).** Keep a ledger of every trade (what, when, why, result) and a short "learnings" file written when a trade closes. Our journal and R-multiple plan covers the ledger; the hard rules must stay in code, not in the LLM's judgment.
7. **Order id reuse (#10).** Re-running the same order can raise error 104 "cannot modify a filled order". Let ib_async assign new ids.
8. **Paper limits (#06).** Some order types, such as combos, can stay `PendingSubmit` on paper accounts.
9. **Quantity types (#00).** An order quantity as an int vs float caused errors for one creator.
10. **Run on Windows, not WSL (#01).** A script in WSL can't reach TWS/Gateway on the Windows host via localhost.

## Claims to treat carefully

- **"Paper doesn't work without a market data subscription" (#00).** Overstated for our case: connect, account data, daily bars, order placement and cancel, and delayed snapshots all worked with no subscription.
- **Subscription bundles (#07):** he recommends the US Securities Snapshot and Futures Value Bundle, the US equity and options streaming add-on, and a CBOE One add-on, and says the account needs funding of at least about 2,000 USD. Unverified.
- **Futures (#00):** needs a margin account and roughly 2,500 USD plus futures permissions, per the author.
- **Profit claims (#02: "over $8,000 a week"):** no evidence shown.
- **#04's backtest (100,000 turned into about 360,000, Sharpe about 0.8):** it assumes no transaction costs or taxes, and it pulls the *current* S&P 500 constituents from Wikipedia, which creates survivorship bias (companies that dropped out are missing). My reading, not the author's. Don't trust a backtest like that.
- **Cost of building (#00):** the author says a Claude Code app cost "a couple hundred bucks" and about a week of work.

## What this changes in our roadmap

- Add a **kill switch** command before the unattended-bot step.
- Order management should use **bracket orders**, with a **trailing stop** as an option.
- Gap scanning should use the **IBKR scanner**, not per-ticker downloads. Test it on paper first.
- Overnight selling needs a **live bid** to price a limit, which needs a market data subscription (about 4.50 USD/month for the US exchange bundle, unverified). Or just trade regular hours.
- Journal: keep **ledger + learnings**, with R-multiples.
