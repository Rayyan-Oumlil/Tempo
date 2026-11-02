# Resources for building Claude + IBKR trading automation

Compiled 2026-11-02 from web searches and `gh repo view` (stars and activity are as of that date).
Confidence labels: **[checked]** = I saw the repo or page data directly; **[search]** = from search-result text only; **[memory]** = from my own knowledge, not verified.
Most pages on IBKR's own site block automated fetches (403), so IBKR claims come from search snippets.

## 1. Official documentation (read first)

| Resource | What it is |
|---|---|
| [ib_async docs](https://ib-api-reloaded.github.io/ib_async) | The library Tempo uses. Successor to ib_insync, maintained. [checked: 1,779 stars, pushed 2026-10-29] |
| IBKR Campus: Python TWS API course | Free 11-lesson course: orders, bracket orders, scanners, concurrency. Aimed at experienced Python programmers. [search] |
| IBKR Campus: Traders' Academy webinars (ibkrwebinars.com) | Free webinars. [search] |
| IBKR TWS API docs: "Trading the overnight session" | Contract `exchange="OVERNIGHT"`, order flag `includeOvernight`. [search] |
| IBKR Campus article "From back-test to paper trading" | IBKR's own list of what paper trading does not simulate. [search] |

## 2. Libraries and infrastructure

| Project | Why it matters | Status |
|---|---|---|
| [ib_async](https://github.com/ib-api-reloaded/ib_async) | Our IBKR wrapper | [checked] active |
| [gnzsnz/ib-gateway-docker](https://github.com/gnzsnz/ib-gateway-docker) | Runs IB Gateway unattended in Docker with IBC. Settings: `AUTO_RESTART_TIME`, `TWOFA_TIMEOUT_ACTION`. The way to keep a bot running without you logging in daily. | [checked] 1,291 stars, pushed 2026-10-30 |
| [IbcAlpha/IBC](https://github.com/IbcAlpha/IBC) | Automates Gateway/TWS login. | [checked] **archived 2026-09-01**. gnzsnz bundles it; check how long that stays viable |
| [pst-group/pysystemtrade](https://github.com/pst-group/pysystemtrade) | Rob Carver's production system, uses IBKR. Best open-source study of risk and position sizing. | [checked] 3,575 stars, active. Per [search], it still uses `ib_insync`, so don't mix with ib_async without checking |

## 3. Backtesting and research engines

| Engine | Notes |
|---|---|
| [nautilus_trader](https://github.com/nautechsystems/nautilus_trader) | 31,151 stars, pushed 2026-11-02, event-driven, same code for backtest and live. IBKR adapter: [memory], verify before relying on it |
| [QuantConnect Lean](https://github.com/QuantConnect/Lean) | 22,341 stars, active. Cloud or self-hosted; supports live brokerages [search]. Heavy setup |
| [vectorbt](https://github.com/polakowo/vectorbt) | 9,633 stars, active. Fast parameter sweeps. Research only, not a live engine [search] |
| [backtrader](https://github.com/mementum/backtrader) | 23,634 stars but **last push 2024-08-19**: looks unmaintained. Sources conflict on its IBKR live support |

Sensible path: write our own small backtester first (we need to understand fills and costs), then decide whether to adopt one of these.

## 4. Reference projects to read, not install

These are small projects. Read how they're structured; don't run code that places orders without reading it.

| Repo | What to look at |
|---|---|
| [9600dev/mmr](https://github.com/9600dev/mmr) | IBKR platform on ib_async. ZeroMQ messaging, DuckDB storage, a propose-review-approve flow for LLM-driven trades. 132 stars [checked] |
| [pedrobraiti/agentic-trading-mcp](https://github.com/pedrobraiti/agentic-trading-mcp) | "Valet": MCP servers so Claude Code can trade IBKR. Paper-first, fail-closed safety guards on every order, hexagonal architecture. Uses the Client Portal API. README says it supports **fractional buys by the dollar**, which our TWS API route blocks (error 10243). Lead worth checking. 14 stars [checked] |
| [omarpatel/ibkr-algo-trader](https://github.com/omarpatel/ibkr-algo-trader) | Paper trading with walk-forward backtesting and risk limits. 0 stars, new [checked] |
| [ArjunDivecha/ibkr-mcp-server](https://github.com/ArjunDivecha/ibkr-mcp-server) | IBKR MCP server for Claude. **Archived 2026-04-11** [checked] |
| [zw008/quant-trader](https://github.com/zw008/quant-trader) | 39-tool MCP server for Claude Code with IBKR execution. 3 stars [checked] |
| [rekurt/awesome-open-source-trading](https://github.com/rekurt/awesome-open-source-trading) | Index of 450+ open-source trading projects. Brand new, 0 stars, so treat the list as unvetted |

Security note: any MCP server or bot that can place orders runs with your broker session. Read the code first and keep paper-only until you trust it.

## 5. Videos and courses

| Resource | Notes |
|---|---|
| Part Time Larry: "Interactive Brokers API with Python and ib_async" (YouTube) | Free, about 24 min, async historical data. [search] |
| Class Central "Interactive Brokers API Tutorial" playlist | ib_insync videos: connecting, orders, option chains. Concepts still apply to ib_async. [search] |
| Ryan O'Connell, "Build a Python Trading Bot ... Using AI" (about 38 min) | Live data, strategy, paper trades on IBKR. Described as sponsored by IBKR. [search] |
| The video you sent: "Claude + IBKR API: Complete AI Trading Bot Guide" | See [notes-claude-ibkr-trading-bot-video.md](notes-claude-ibkr-trading-bot-video.md) |
| Udemy: "Algorithmic Trading using Interactive Broker's Python API" | Paid. Not reviewed. [search] |
| GitHub: [oheesyed/ib_async_tutorial](https://github.com/oheesyed/ib_async_tutorial), [AlgoTrading101 ib_insync course](https://github.com/AlgoTrading101/AlgoTrading101-Interactive-Brokers-Course-ib_insync-) | Free starter code. The AlgoTrading101 one is old (2021, ib_insync) |

I could not verify QuantInsti/Quantra or QuantConnect course offerings; no search returned them.

## 6. Books

| Book | Why |
|---|---|
| Robert Carver, *Systematic Trading* | Designing a system and sizing positions. Companion code is pysystemtrade. Appears repeatedly in recommendations [search] |
| Ernest Chan, *Quantitative Trading* and *Algorithmic Trading: Winning Strategies and Their Rationale* | Beginner and intermediate foundations. [search] |
| Yves Hilpisch, *Python for Algorithmic Trading* | Python-focused workflow. [search] |
| Kevin Davey, *Building Algorithmic Trading Systems* | Practical system building. [search] |
| Andreas Clenow, *Stocks on the Move* / *Trading Evolved* | The search returned nothing useful. Mentioned from memory only; check before buying |
| Marcos López de Prado, *Advances in Financial Machine Learning* | Not verified by the search; see the papers below for the overfitting ideas |

## 7. Reality checks (read before risking real money)

- **Backtest overfitting:** Bailey, Borwein, López de Prado and Zhu, [Statistical Overfitting and Backtest Performance](https://papers.ssrn.com/abstract=2507040). Trying many strategy variants on one dataset finds "winners" that are noise.
- **Deflated Sharpe Ratio:** [Bailey and López de Prado](https://papers.ssrn.com/abstract=2460551). Discounts a Sharpe ratio for how many things you tried.
- **Day trader outcomes:** Chague, De-Losso and Giovannetti (Brazil, 2020) report that the large majority of persistent day traders lost money; figures vary between versions ([arXiv 1912.04274](https://arxiv.org/pdf/1912.04274)). Barber and Odean's "Trading Is Hazardous to Your Wealth" found very active households trailed the market. Blog statistics (97%, etc.) vary, so cite the papers.
- **Paper vs live:** IBKR paper fills come from top of book, with no market impact, slippage, or price improvement simulated [search]. Paper results will look better than live.

## 8. Suggested learning order

1. IBKR Campus Python TWS API course, then the ib_async docs (understand orders, contracts, errors).
2. Part Time Larry video, then our own `tempo/` code (already built).
3. Rob Carver's *Systematic Trading* (risk and sizing) alongside pysystemtrade's IB code.
4. Read mmr and Valet for architecture and safety guards.
5. Write our backtester; read the two Bailey/López de Prado papers before trusting any result.
6. gnzsnz/ib-gateway-docker when we want the bot to run unattended.
