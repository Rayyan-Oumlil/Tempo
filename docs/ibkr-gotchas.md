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
- **`whatIfOrder` returned an empty list** on the closed market; we haven't gotten a usable result.
- **CAD-only paper account:** IBKR lists no USD `ExchangeRate`, so equity in USD needs the USD.CAD forex price (we use daily MIDPOINT bars).
- **Buying a US stock with only CAD works.** CAD `TotalCashValue` fell by exactly the converted cost (1,063.68 CAD for 760.64 USD at about 1.398). No USD ledger line appeared and we saw no margin interest.
- **Commission:** 1.00 USD on a 1-share trade (probably a per-order minimum).
- **Overnight venue:** contract `exchange="OVERNIGHT"` (`primaryExchange="ARCA"` for SPY worked). ib_async 2.1.0 has no `includeOvernight` order field. A buy filled immediately (759.64 vs last close 755.72). Sell limits at 748.16, 730 and 700 sat in `Submitted` and never filled: no bid, or a paper-simulator limit. A market sell is rejected (387).
- **Outside regular hours (video 07):** market orders aren't accepted; use a limit with `outsideRth=True`.
- **Client ids (videos 06, 08):** orders are visible only to the client id that placed them. Use a fixed id (Tempo uses 21). The master client id or 0 sees all.
- **Gateway auto-logoff** defaults to 23:45; use Auto restart in Configure, Lock and Exit.
- **Paper reset** is requested in the live account's portal and landed the same evening for us (5,000 CAD to 250,000 CAD).
- **Time zones (video 06):** use explicit UTC or US/Eastern; a creator lost days to a wrong zone.
- **Scripts in a scratch file** that call `load_dotenv()` with no file path can fail with an `AssertionError` in `find_dotenv()`; run them as a module or save them as a file.

## Windows

- A Claude Code session that has a folder as its working directory locks it; a rename fails with "Device or resource busy".
- Windows PowerShell 5.1 `ren tempo Tempo` rejects a case-only rename; rename via a temporary name.
- Python run from WSL can't reach a Gateway on the Windows host via localhost (video 01).
