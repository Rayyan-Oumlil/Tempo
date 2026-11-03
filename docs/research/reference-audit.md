# Reference projects audit

2026-11-02. The repos live in `Trading/reference/`. They are untrusted code: we read them, we do not run them.

**Method and limits.** I read the design documents and the safety-critical files of the five projects closest to Tempo (agentic-trading-mcp, mmr, ibkr-algo-trader, pysystemtrade, ib-gateway-docker). I did not run any code, and I did not check any performance claim a repo makes. Lean, nautilus_trader and vectorbt are large frameworks (41k, 130k and 106k lines of Python in the clone) that I only skimmed for size; revisit them if we outgrow our own backtester.

## Verdicts

| Repo | Size (Python lines) | What it is | Take | Skip |
|---|---|---|---|---|
| **agentic-trading-mcp** | 8.9k | MCP server that lets Claude trade IBKR, with a hard safety layer and an ADR log | `GuardedBroker`: one choke point every order passes through. Append-only JSONL journal that records the **intent before the order is sent**. Reconcile unresolved intents against the broker's open orders by client order id. Decision log (ADRs) | Client Portal API (needs a browser login, ~24h sessions; they chose it only for fractional shares). The MCP layer, for now |
| **mmr** | 145k | Mature IBKR platform on ib_async, self-audited | Principles from `SAFETY_ROADMAP.md` (below). `STRATEGY_EVALUATION.md`: how to judge a backtest. Append-only research log with corrections written underneath | ZeroMQ, DuckDB, mutation testing, a verification "gauntlet": far too much for us |
| **ibkr-algo-trader** | 12k | Paper bot with risk limits and a kill switch | `KILL_SWITCH` file blocks new entries. `flatten_now.py`: global cancel, then flatten with retry passes and a flat check, without stacking duplicate covers. `gate_criteria.yaml`: success criteria written before the data exists. The gap list in `ECOSYSTEM_REVIEW.md` | `AGGRESSIVE_MODE`, `ULTRA_AGGRESSIVE`, `WAY_BETTER`: 4x leverage, a 50% daily loss limit and 500 trades a day. The opposite of what we want. Its own review admits the daily-loss breaker is switched off |
| **pysystemtrade** | 96k | Rob Carver's production futures system | The *idea* of override states (normal, reduce only, no trade) plus trade limits and position limits per period | Mongo, order stack, futures-specific code. Per earlier notes it uses `ib_insync`, not `ib_async` |
| **ib-gateway-docker** | n/a | Gateway in Docker | Later, for unattended running: `AUTO_RESTART_TIME`, `TWOFA_TIMEOUT_ACTION`, `EXISTING_SESSION_DETECTED_ACTION`, `TRADING_MODE=paper` as default | IBC is archived upstream (per `resources.md`); check how long the bundle stays viable |
| ib_async, ib_async_tutorial | 11k, 0.3k | The library we use, plus a tutorial | Nothing new: our probes already covered the API | |
| ibkr-mcp-server, quant-trader | 1.1k, 4.5k | MCP servers for Claude | Nothing now | ibkr-mcp-server is archived |

## The ideas worth taking (and where they come from)

1. **One choke point for every order** (agentic-trading-mcp). Its rules: live only with an explicit flag; a cap on order value; a cap on daily spend; reject an identical order inside a short window; market must be open; dry run by default. Rules in code that every order passes through cannot be skipped by a new script.
2. **Journal the intent before sending** (agentic-trading-mcp). If the script dies between "sent" and "result", the intent is already on disk, so nothing is lost or double-sent.
3. **Reconcile at startup** (agentic-trading-mcp, ibkr-algo-trader). Compare unresolved intents with the broker's open orders and today's executions, and refuse to trade until they agree. A found order that partly filled counts as filled.
4. **Exits are never refused; entries fail closed** (mmr). Every limit applies only to orders that *increase* exposure. If a needed input cannot be read, new exposure is refused with a reason, but closing is always allowed. The classifier must check the live position, not trust the caller.
5. **Turn conventions into invariants** (mmr). A rule that lives in a habit or a comment gets skipped eventually. Put it where a script cannot bypass it.
6. **Kill switch plus flatten** (ibkr-algo-trader). A file that blocks new entries, `reqGlobalCancel`, then flatten with a verify step. Our probe confirmed `reqGlobalCancel` cancels other clients' orders too.
7. **Pre-register the success criteria** (ibkr-algo-trader `gate_criteria.yaml`): minimum round trips, net positive after costs, a share of trades tainted by bot errors, and "no live-money talk on delayed data". Written before the results exist, never edited between gates.
8. **Judge a backtest honestly** (mmr `STRATEGY_EVALUATION.md`). Three questions: what does the same pipeline report on pure noise, how much of the result came from searching many variants, and what does the rule earn without knowing the future. In their case every armed strategy failed all three; the flagship's out-of-sample return was +0.097% against a backtest Sharpe of 3.46. Their one durable result was pre-registered 12-1 momentum at Sharpe 0.26, after costs, on a survivorship-free universe. They also note that the probabilistic Sharpe ratio blessed sweeps that were pure overfit, so it is not a gate.
9. **Cheap hard backstops** (ibkr-algo-trader review): a dead-man's ping that alerts on silence, an order-rate ceiling that trips the kill switch, a price plausibility check that rejects limits far from the last close, early-close days in the calendar, and no API jobs around the 23:30 to 01:00 ET reset.

## Tempo today against these

| Idea | Tempo |
|---|---|
| Paper-only guard | Yes (`ibkr.connect`) |
| Read-only by default | Yes (`IBKR_READONLY=1`) |
| Sizing from risk rules | Yes (`risk.py`, `size.py`) |
| Fixed client id | Yes (21) |
| Order tag (`orderRef`) | Partly: each tool sets its own |
| Explicit `tif` | Yes in all tools, but nothing enforces it |
| Single choke point, journal, reconcile | **No** |
| Kill switch | **Partly**: `flatten` handles longs only; no global cancel, no entry block |
| Daily loss limit, exit-class rule | **No** |
| Pre-registered gate, honest backtest | **No** (the roadmap gate is a paragraph) |

## 2026-11-02 evening: second audit, five more references

Cloned shallow into `Trading/reference/`: **freqtrade** (68k Python lines, 82k test lines), **thetagang** (21k, 22k test), **vnpy** (16k, 2.7k test), **qlib** (70k), **icli** (24k, no tests). Read, not run. I read the order-handling code of thetagang, the protections and bias-analysis code of freqtrade, and grepped icli and vnpy for specific questions; I did not read them whole.

| Repo | What it is | Take | Skip |
|---|---|---|---|
| **thetagang** | Production IBKR bot on `ib_async`, closest to Tempo | Order supervision in `order_execution.py`: a rejection can arrive as `Inactive` or as `Cancelled` plus error 201; an external cancel is 202; unknown codes fail closed. The reason can arrive after the status, so wait up to 2 s for it. Re-send only the unfilled remainder. | Options strategies, roll logic, config models |
| **freqtrade** | Largest open-source bot (crypto) | `plugins/protections/`: MaxDrawdown lock over a window, StoplossGuard (N stop-outs in a window pauses trading), CooldownPeriod. Lookahead and recursive-bias analysis tools. | Crypto, hyperopt, FreqAI, Telegram |
| **vnpy** | Chinese and crypto framework | Nothing: the engine is an event bus, there is no risk layer to copy | All of it |
| **qlib** | Microsoft ML research platform | Nothing now; relevant only for large factor research | All of it |
| **icli** | IBKR command line on `ib_async`, no tests | Runs `whatIfOrder` on every leg of a bracket before sending | The rest |

## Tempo against them: gaps found

Facts checked in Tempo's code are marked (checked).

1. **Broker rejection reasons are not recorded** (checked: no code in `tempo/` reads error codes or `whyHeld` after sending; `record_outcome` stores status, fills and commission only). A rejected or externally cancelled order therefore stays "unresolved" and needs `--accept-missing`. thetagang shows the reason is available from `ib_async` shortly after the status. Whether `trade.log` carries the error code in our installed version is **not yet checked**.
2. **Only a one-day loss limit.** freqtrade's protections suggest two more locks: a drawdown over several days, and "N stop-outs in a row pauses entries". Neither exists in Tempo. They matter once a strategy trades unattended, not before.
3. **`whatIfOrder` is not in the order path** (checked: its only use is the read-only smoke test, `tempo/smoke.py:86`). icli previews every bracket leg. A margin and commission preview inside the order door would refuse an entry the account cannot afford before it reaches the broker.
4. **Limit prices are not rounded to the tick.** An off-tick price comes back as error 110 and `Cancelled` (documented in `ibkr-gotchas.md`), so it fails safe, but noisily. thetagang rounds to 2 decimals; a real fix reads `minTick` per contract.
5. **Not a gap:** look-ahead bias in the backtester. A strategy only receives closes up to day t and fills at t+1 (`backtest.py`, tested), so the failure freqtrade's lookahead tool detects cannot occur by construction.

Nothing here was built. Ranking by risk reduced per line of code: 1, then 3, then 2 (only when unattended running is chosen), then 4.
