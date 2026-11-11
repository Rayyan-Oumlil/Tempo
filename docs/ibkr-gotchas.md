# IBKR gotchas observed in this project

Observed on the paper account `DUR239224` (IB Gateway port 4002, ib_async 2.1.0), 2026-11-01/02, unless marked "(video)".

## Message codes

| Code / message | Meaning | What we did |
|---|---|---|
| 10167 "not subscribed, displaying delayed market data" | No live subscription. The Gateway log also shows `snapshot perms=NO_TOP` | Use `reqMarketDataType(4)`; daily bars work without a subscription |
| 399 "order will not be placed at the exchange until 09:30" | Market closed; order queued as `PreSubmitted`. ib_async logs it as `ValidationError`, but it is not a failure | Treat as accepted |
| 202 "Order Canceled" | Confirmation of our own cancel | Expected |
| 201 "Order was discarded" | Order dropped, here by a Gateway precaution (see 10329) | Fix the Gateway setting |
| 10329 "will be directly routed to OVERNIGHT. Restriction is specified in Precautionary Settings" | Gateway blocks API orders to the overnight venue | Configure, Settings, API, Precautions: tick "Bypass Redirect Order warning for Stock API Orders". Worked, and video 05 confirms it |
| 10243 "Fractional-sized order cannot be placed via API" | No fractional shares through the TWS API | Whole shares only |
| 387 "Unsupported order type for this exchange" | Market orders are not allowed on the OVERNIGHT venue | Limit orders only |
| 10349 "TIF set to DAY based on order preset" | Informational | Ignore |
| 104 "cannot modify a filled order" (video) | Re-sent an order that already filled | Don't reuse order ids |

## Behaviour

- **Read-Only API** (Gateway setting) blocks orders **and what-if orders**. A what-if on a read-only connection opens a modal popup and the request hangs forever.
- **`ib.RequestTimeout` defaults to no timeout.** Set it (we use 15 seconds), or a missing subscription hangs the script.
- **`reqTickers` needs a qualified contract** (`qualifyContracts` first, so it has a `conId`).
- **`whatIfOrder` returns `[]` unless the order has an explicit `tif="DAY"`.** The harmless 10349 notice ("TIF set to DAY based on order preset") swallows it. With `tif="DAY"` it returns an `OrderState` with the commission (1.000003 USD for 1 SPY) and margin change (initMarginChange 318.36 for 1 SPY at about 1,062 CAD). Verified 2026-11-02, market open.
- **CAD-only paper account:** IBKR lists no USD `ExchangeRate`, so equity in USD needs the USD.CAD forex price (we use daily MIDPOINT bars).
- **Buying a US stock with only CAD works.** CAD `TotalCashValue` fell by exactly the converted cost (1,063.68 CAD for 760.64 USD at about 1.398). No USD ledger line appeared and we saw no margin interest.
- **Per-currency cash:** only the `TotalCashValue` tag is reported per currency (no `CashBalance`). Commissions also leave a small negative USD line in `SettledCashByDate` (about -4 USD after a few trades).
- **Commission:** 1.00 USD on a 1-share trade (probably a per-order minimum).
- **Overnight venue:** contract `exchange="OVERNIGHT"` (`primaryExchange="ARCA"` for SPY worked). ib_async 2.1.0 has no `includeOvernight` order field. A buy filled immediately (759.64 vs last close 755.72). Sell limits at 748.16, 730 and 700 sat in `Submitted` and never filled: no bid, or a paper-simulator limit. A market sell is rejected (387).
- **Outside regular hours (video 07):** market orders aren't accepted; use a limit with `outsideRth=True`.
- **Client ids (videos 06, 08):** orders are visible only to the client id that placed them. Use a fixed id (Tempo uses 21). The master client id or 0 sees all.
- **Gateway auto-logoff** defaults to 23:45; use Auto restart in Configure, Lock and Exit.
- **Paper reset** is requested in the live account's portal and landed the same evening for us (5,000 CAD to 250,000 CAD).
- **Time zones (video 06):** use explicit UTC or US/Eastern; a creator lost days to a wrong zone.
- **Scripts in a scratch file** that call `load_dotenv()` with no file path can fail with an `AssertionError` in `find_dotenv()`; run them as a module or save them as a file.

## Orders (probed 2026-11-02, market open, SPY, paper)

| Test | Result |
|---|---|
| **Always set `tif` explicitly** | Without it, every order gets the 10349 notice. ib_async turns that notice into a transient `Cancelled` status (log line "Canceled order"), so `trade.isDone()` can be `True` on an order that then fills. This also made my first latency numbers meaningless (about 50 ms was the false cancel, not the fill). All Tempo tools set `tif="DAY"` |
| Shorting | `SELL` with no shares fills and gives position -1; a `BUY` covers it. Paper allows it. `tempo.flatten` only closes longs |
| Order types accepted when far from market | `STP`, `STP LMT`, `TRAIL` (percent and amount), `LMT` GTC, `outsideRth`, Adaptive algo, `REL`, hidden. `LOC` came back `Cancelled` |
| Bad price (off tick, or negative) | 110, status `Cancelled`. Tick for SPY is 0.01, for TSX stocks 0.005 |
| Quantity 0 | 321, `ValidationError` (never reaches the exchange) |
| Quantity 10,000,000 | 201 rejected, status `Inactive` |
| `LMT` order with no price | 201 "Message must contain field # 44", `Inactive` |
| Cancel an order that is already cancelled | 10148 (or 161 "not in a cancellable state"); harmless, but `reqGlobalCancel` produces a burst of 161s |
| Modify | Re-place the same order object (same `orderId`) with the new price; it updates in place |

## Brackets, stops and kill switch

- **Parent with children:** with a far `LMT` parent, the take-profit and stop children sit `PreSubmitted` until the parent fills; cancelling the parent cancels both children.
- **Live bracket (MKT parent, TP `LMT`, `STP`, same `ocaGroup`, `ocaType=1`):** parent filled, TP `Submitted`, stop `PreSubmitted` (held by IBKR, not by our script).
- **Cancelling one leg of an OCA pair cancels the other.** Cancelling only the take-profit also cancelled the stop and left a long position with **no stop**. Never cancel a single bracket leg; to exit, flatten and cancel all.
- **`ib.reqGlobalCancel()` cancels every client's open orders**, not just this client's (client 22 cancelled a GTC order placed by client 21). Right after it, `ib.openTrades()` can still list one trade for a few seconds (stale local state, probably); confirm with `ib.reqAllOpenOrders()`.
- **Orders outlive the connection.** A GTC order stayed open after its client disconnected and after it reconnected. A stop left at IBKR still protects you if the script dies, and an unwanted order keeps working until cancelled. DAY orders were not tested.
- **Live bracket through Tempo (2026-11-02):** MKT parent filled; the GTC stop rested as `PreSubmitted` at IBKR; a separate process (`tempo.health`) saw the position and both orders. `tempo.kill` then cancelled the resting orders, closed that long and a separate QQQ short, confirmed flat, and left the mode at `reduce_only`.
- **Take-profit firing, live (2026-11-02):** a take-profit priced below the market filled right after the entry, and IBKR cancelled the stop (the OCA partner), leaving the account flat. `confirm_bracket` first read that as "stop not resting, UNPROTECTED"; it now recognises a filled take-profit (or an immediate stop-out) as a closed position.
- **Do not modify a bracket leg after it is placed.** Re-placing the take-profit from a second connection with a new price CANCELLED it. The stop stayed, so the position stayed protected, but the take-profit was lost. To change a bracket, flatten and start again.
- **`orderRef` survives across client ids** in both `reqAllOpenOrders()` and `reqExecutions()`. A fresh client (a new process) matched a working order and a filled order from a "crashed" one by their tags. Verified live 2026-11-02.
- **`reqCompletedOrders()` cannot be matched to the journal.** For orders from another session it returns `orderRef` empty, `orderId` 0 and `clientId` 0 (checked 2026-11-02); only `permId` survives, and it is not known before a crash. So cancelled orders need a manual `--accept-missing`. `reqExecutions()` only covers today.
- **A SELL stop above the market is already hit:** it triggered at once and filled (`PreSubmitted` then `Filled`); its execution carries the stop's `orderRef`. Execution commission reads 0.0 at first and is filled in later, so do not record it from the first read.
- **Other clients see your orders:** client 22 saw client 21's order with `reqAllOpenOrders()` and `openTrades()`.

- **Position feed lags fills.** Right after a fill, `ib.positions()` can briefly miss the change. A retrying flatten could then sell twice and open a short, so `tempo.flatten` sells each symbol once, waits for the feed to settle, and reports anything still open.
- **Reference price for caps:** entry checks use the newest daily bar. During regular hours that is today's bar, i.e. the latest trade (delayed about 15 minutes): SPY 754.84 against a delayed quote of 755.07 on 2026-11-02. Before the open it is the previous close. Fine for a cap and a sanity band; do not use it as a trading price.

## Fees (paper, 2026-11-02)

| Item | Measured |
|---|---|
| Currency | USD, always (it is a US stock) |
| BUY | 0.005 USD per share, minimum 1.00 (1, 10, 100 shares = 1.00; 300 shares = 1.50) |
| SELL | same, plus about 0.0157 USD per share at a price near 760 (about 20.6 USD per million sold; likely the SEC fee, inferred) |
| 300-share round trip | 7.70 USD of commission on 228k USD per side |
| CAD-to-USD | No visible markup: a round trip's CAD cash change matched the net USD at the market USD.CAD rate (1.3970 vs 1.3967) |
| Account base | The account seems to carry a small USD debit instead of converting CAD (inferred). A real account may charge interest on a USD debit held overnight; unverified |
| Preview | `whatIfOrder` with `tif="DAY"` returns the commission before you send the order |

A paper account only simulates fees. Check the real fee schedule before going live.

## Market data (no subscription)

- **Quotes:** `reqMarketDataType(4)` then `reqMktData` gives streaming bid/ask/last about 15 minutes delayed. The values arrive in `ticker.bid/ask/last` with `ticker.marketDataType == 3`; ib_async's `Ticker` has no `delayedBid` fields. Asking for live data (type 1) gives 10089.
- **Intraday history is delayed too:** at about 09:55 ET the newest 1-minute bar was 09:38. A `keepUpToDate` subscription added no bars in 70 seconds. A live intraday strategy needs a data subscription.
- **History depth and speed:** daily bars, 20 years in 3 s (5,026 bars); 5 days of 1-minute bars in 0.4 s (1,569 bars, regular hours); 1 week of 5-minute bars 0.2 s; head timestamp for SPY is 1993-01-29. `ADJUSTED_LAST`, `BID_ASK` and `OPTION_IMPLIED_VOLATILITY` work.
- **Too much history hangs:** 1 year of 1-minute bars timed out at 15 s with no error. Request in chunks.
- **1-second bars:** "1 D" and "30 D" with `1 secs` give 162 "invalid step". Not investigated further.
- **Pacing:** three identical daily-bar requests in a row did not trigger a pacing error.
- **Canada:** `Stock("RY","TSE","CAD")` and `XIU` give 162 "No market data permissions for TSE". `Stock("SHOP","SMART","CAD")` returned daily bars, so route Canadian stocks through SMART.
- **Not available:** 5-second real-time bars (420, no permission for AMEX), market depth (10092), fundamentals (10358). The news provider list loads; news content was not tested.
- **`reqPnL` first callback can be STALE.** Subscribing returned -11.21 at 0.06 s and the real daily P&L, -151.55, about a second later (later subscriptions got one correct callback at about 1 s). `ib.reqPnL` also starts as NaN. Tempo reads the figure only after a 2 s settle (`PNL_SETTLE_SECONDS`), so each new entry pays about 2 s. Verified live: three reads agreed with IBKR at 0.0602%.
- **Works:** option chain parameters (64 chains for SPY), `reqPnL`, `reqExecutions` (today's fills), `reqCompletedOrders`, 96 account summary values.
- **Scanner:** works without a subscription for `STK.US.MAJOR` (`TOP_PERC_GAIN`, `MOST_ACTIVE`, `HOT_BY_VOLUME`, 8 rows in 0.2 to 2.4 s). The gainers are micro-caps (INO, RBNE, CLRO), so add price/volume filters before trusting them. `STK.CA.TSE` gives 162 "not configured". A 162 "scanner subscription cancelled" follows every scan and is harmless.

## Windows

- An editor or terminal session that has a folder as its working directory locks it; a rename fails with "Device or resource busy".
- Windows PowerShell 5.1 `ren tempo Tempo` rejects a case-only rename; rename via a temporary name.
- Python run from WSL can't reach a Gateway on the Windows host via localhost (video 01).

## Why an order failed: where the reason actually is (verified live 2026-11-03)
| What IBKR did | Status we see | Where the error code is |
|---|---|---|
| 201 "Order rejected - reason: ..." (tested with 20,000 SPY, margin far beyond the account) | `Inactive` | **Only `ib.errorEvent`.** `trade.log` has no error code. |
| 110 (price off the tick) | `Cancelled` | `errorEvent` and `trade.log` |
| 391 (GTD with no valid date) | `Cancelled` | `errorEvent` and `trade.log` |
| 202 "Order Canceled - reason:" | `Cancelled` | `errorEvent` only, and the reason text is **blank**. It is sent for our own cancels too, so it cannot tell who cancelled. |
| 10349 "TIF set to DAY" | none (harmless) | `errorEvent` |

`tempo.orders` therefore listens to `errorEvent` per connection (idea from thetagang's order supervision) and journals `reason_code`, `reason_kind` (`rejected` for 201, otherwise `error`) and `reason_text` on any order that did not fully fill. Plain cancels, 202 and 10349 leave no reason. Limit: the error can arrive after the status, so record the outcome once the order is done (the live test waits 1.5 s).

## News (probed 2026-11-10, paper, no subscription)
- `reqNewsProviders` lists 8 free providers: BRFG, BRFUPDN (Briefing.com), DJ-N, DJ-RTA, DJ-RTE, DJ-RTG, DJ-RTPRO, DJNL (Dow Jones). Per-stock headlines come mostly from DJ-N (Dow Jones Global Equity Trader).
- `reqHistoricalNews(conId, "BRFG+...", "", "", 300)` returns up to 300 headlines, newest same-day. **With a start/end window the results are wrong** (headlines from before the start come back). Pass empty start/end and filter by `time` yourself.
- `reqNewsArticle(providerCode, articleId)` returns the text (about 4,500 characters for a Barron's piece).
