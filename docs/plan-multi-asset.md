# Plan v3: from a stock bot to a multi-asset research and trading system

Owner decision, 2026-11-23: "let's test other things like crypto and commodities ... a whole restructuration of the whole plan". This replaces plan v2 as the **top-level direction**; plan v2 stays as the record of the stock work and its frozen protocols (F, G, H, M, N, X). Nothing in v2 is edited or deleted.

## 1. Where we are, honestly

| Fact | Evidence |
|---|---|
| The stock work is finished as research: every history-testable stock rule was KILLED under frozen protocols (insider, weekly reversal, earnings bands, short volume, news, ML ranking). | `docs/research/log.md`, README "Run the strategy" |
| Slow multi-ETF trend (G) and a cash-yield version (H5) do not beat plain 60/40 per unit of risk. Put-write (H6) does not either. | log 2026-11-17 and 2026-11-23 |
| Crypto trend (X2, X3) beat buy and hold on Sharpe after costs but missed the drawdown bar (-64%, bar 75% of -83%). Gold trend (X1) did not. | log 2026-11-23 (later) |
| The code base is stock-shaped: orders, risk, data pulls, sizing, market-hours logic all assume `Stock(..., "SMART", "USD")` and US sessions. The research code (`history_trend`, `history_cash`, `history_xc`) already works on any daily close series. | grep of `tempo/` |

Said plainly: nobody has shown an edge yet, in stocks or elsewhere. What exists is a **measurement machine that kills bad ideas cheaply**. The restructure widens what it can look at; it does not lower the bar.

## 2. Principles (unchanged, now explicit)

1. **Register first.** Rules, parameters, windows, costs, pass criteria written and committed before any return is computed. Never edited after a result; add a dated entry.
2. **History can kill, never confirm.** A PASS is a candidate for a paper trade, then the 120-day real-money gate (`evidence/gate.json`).
3. **One global trial counter.** The Deflated Sharpe must see every hypothesis tried across the whole multi-asset family, not only the latest workstream. Count so far in the family (G, H, X): **N = 9** (G1-G4, G5, G6, X1-X3). Every new hypothesis raises it, and the threshold with it.
4. **Hindsight-selected assets are a bias, not a result.** BTC, ETH and today's ETFs are survivors. Say it in every protocol.
5. **Costs are assumptions until measured.** Paper fills cannot measure slippage; only tiny real-money trades could, behind the gate.
6. **Sizing is part of the rule.** A rule that makes money with a -64% drawdown is not a book. Volatility targeting and a drawdown cap are tested as hypotheses, not bolted on afterwards.

## 3. Universe (sleeves), all tested with the same engine

| Sleeve | Instruments (free daily history) | Why it is here |
|---|---|---|
| Equity indices | SPY, QQQ, IWM, EFA, EEM | already have 2006+ |
| Bonds | AGG, TIP, TLT, IEF | diversifier, the 60/40 half |
| Gold and metals | GLD (XAUUSD proxy), SLV, CPER | X1 killed plain trend; still a sleeve |
| Broad and single commodities | DBC, USO, UNG, DBA | trend works best with breadth (38+ instruments in pysystemtrade) |
| Crypto | BTC-USD, ETH-USD (SOL and others only from 2020, survivorship severe) | X2 and X3 are the only near-misses |
| FX | UUP and the CAD cross from FRED | account is CAD; currency exposure matters |
| Cash | FRED DTB3 | opportunity cost, now modelled |

## 4. Test queue (each registered before it runs; every item raises N)

| # | Hypothesis | Why this one | Data |
|---|---|---|---|
| X4 | **Volatility-targeted BTC trend** (the near-miss): same X2 signal, position sized to a fixed annual vol target, cap on gross | the failure was drawdown depth, which sizing attacks directly | have it |
| X5 | **Signal-speed robustness of X2/X3** (50, 100, 200-day neighbours reported together, one chosen rule counted as the trial, the grid disclosed) | tells whether 100-day was luck | have it |
| Y1 | **Cross-asset trend portfolio** across all sleeves, risk-parity sized, monthly | breadth is where trend Sharpe comes from; single assets mostly fail | have most; add TLT, IEF, USO, UNG, DBA, CPER |
| Y2 | **Crypto funding-rate and basis carry** (market-neutral: long spot, short perpetual) | a risk premium, not a forecast; the only crypto idea that does not need a bull market | Binance public funding history (reachability from here to be checked) |
| Y3 | **Gold vs real yields regime** (FRED DFII10): hold gold only when the 10-year real yield is falling | the one macro driver with a theory | FRED |
| Y4 | **Intraday XAUUSD and crypto** (hourly) | only if daily survives; costs dominate | IBKR or Binance klines |
| Y5 | **Cross-sectional crypto momentum** on a top-N list | survivorship makes free data nearly useless; do last or never | needs a point-in-time list |

Queue rule: stop adding hypotheses when the global N reaches 20 without a PASS. That is the signal that the family has no edge at this cost level, and the honest answer becomes "buy a diversified fund".

## 5. Engineering changes (in order, none touches the order door yet)

1. **Asset registry** `tempo/universe.py`: symbol, sleeve, annualisation (252 or 365), cost per side, data source. History modules read from it instead of hard-coding lists.
2. **One data layer**: IBKR bars when a Gateway is available, Yahoo/FRED fallback (already used in H and X) with the source recorded in each result; cached outside git.
3. **One report runner**: a registered protocol file in `evidence/` per workstream, one command prints verdict plus the global N and the DSR at that N.
4. **Execution generalisation, only after a PASS**: `Stock(...)` hard-coded in about 20 modules becomes a contract factory (stock, metals, crypto, future); market-hours and risk rules become per-sleeve (crypto is 24/7, so "regular hours only" and the daily-loss window need a sleeve-aware definition).
5. **Probe on the paper Gateway before relying on any of it** (not verified, not assumed): is spot gold (XAUUSD) tradable on this account, are crypto and futures permissions available to a CAD-resident paper account, what market-data subscriptions each needs, and what fees apply.

## 6. What happens to the stock work

- Kept as forward tests (ledger, `paper_run`) at **near-zero cost**; no new stock research is started.
- The VPS (about 12-20 USD a month) is the owner's call. Its only remaining jobs are the stock ledger forward tests and a Gateway for IBKR bars. The multi-asset research above runs on a laptop with free data. Recommendation: cancel the VPS unless the forward stock tests are wanted, and re-rent a Gateway only for step 5.
- `docs/plan-quant-v2.md` keeps every frozen protocol as the audit trail.

## 7. Decision points

| When | Decision |
|---|---|
| Now | Approve queue order: X4, X5, Y1 first (all on data already or freely available). |
| After X4, X5, Y1 | If nothing PASSes: do Y2 (carry), the structurally different idea. |
| N = 20 with no PASS | Stop searching. Record "no edge found" and shut the research line down. |
| Any PASS | Paper-trade 3 months with a probe-verified contract path, then the 120-day gate, then real money with the existing caps. |
