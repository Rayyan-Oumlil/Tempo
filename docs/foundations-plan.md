# Foundations plan

Goal: small, solid, boring. About 600 lines of new code across five phases, each with tests and one clear "done" check. Every idea comes from [the reference audit](research/reference-audit.md). Nothing here is a strategy: a strategy plugs into these foundations later.

Paper account only. Work in order; each phase stands on the one before.

## Phase 1: one door for orders

**Build:** `tempo/orders.py` and `tempo/journal.py`.
- `place(ib, contract, order, *, reason)` is the only function that calls `ib.placeOrder`. It sets `tif` explicitly, tags the order with a unique `orderRef`, and refuses a non-paper account, an order above `max_position_pct`, a duplicate of an order sent in the last N seconds, and entries when the market is closed.
- The journal is an append-only JSONL file in `journal/` (gitignored). It writes the **intent before** sending and the **outcome after**, and the same file answers "what did Tempo do today?".
- Existing tools (`lifecycle`, `flatten`, `roundtrip`) switch to `place`.

**Done when:** a test proves a script cannot place an order without a journal line, and a fake crash between intent and outcome leaves the intent on disk.

## Phase 2: stop button

**Build:** `tempo/state.py` and `tempo/kill.py`.
- State file with three values from pysystemtrade's idea: `normal`, `reduce_only` (no new entries, exits allowed), `halt` (cancel everything). `place` checks it.
- `python -m tempo.kill`: set `halt`, `reqGlobalCancel`, flatten **longs and shorts** with retry passes, confirm with `reqAllOpenOrders` and positions (not the local trade list, which can be stale), and report.
- **Exit rule from mmr:** an order that reduces the live position is never refused by any limit. Entries fail closed if equity or the price cannot be read.

**Done when:** tests show an entry is refused in `reduce_only`, an exit is allowed in every state, and a live paper run flattens one long and one short and ends clean.

## Phase 3: know the truth at startup

**Build:** `tempo/reconcile.py`, plus lines in `health`.
- Read unresolved journal intents, compare with `reqAllOpenOrders` and `reqExecutions` by `orderRef`. A partial fill counts as filled. Unknown orders block trading until cleared.
- `health` also shows state, today's journal count, and unresolved intents.

**Done when:** a test with a fake broker resolves a found order, keeps a missing one blocked, and `health` prints both.

## Phase 4: brackets that cannot hurt you

**Build:** `tempo/bracket.py` on top of `place`.
- Parent plus stop plus take-profit in one OCA group, GTC stop so it rests at IBKR.
- Built-in rule from our probe: **never cancel one leg**; the only exits are "flatten" and "cancel all".
- Entry size comes from `risk.py`; the stop price is required, not optional.

**Done when:** live paper run shows parent filled, stop resting, then `kill` clears everything, and a test proves no code path cancels a single leg.

## Phase 5: the evidence harness

**Build:** `evidence/gate.yaml`, a tiny backtester, and `docs/research/log.md`.
- **Pre-register the gate before any backtest:** minimum round trips, net positive after the measured costs, share of trades tainted by bot errors, a stated number of variants tried, and "no live-money talk on delayed data". Adapted from `gate_criteria.yaml`; never edited between gates.
- **Backtester on free daily bars** (20 years), with the measured costs: 0.005 USD per share, 1.00 USD minimum, sell-side fee about 20.6 USD per million, slippage assumed. Signals use only data available at the time.
- **Negative control:** run the same pipeline on shuffled or random data. A "good" result on noise means the pipeline is wrong.
- **Research log:** append-only, dated; corrections go underneath, never over the original (mmr).

**Done when:** a do-nothing and a buy-and-hold baseline run through the harness and match hand calculations, and the control returns roughly nothing.

## Deliberately not in this plan

- Any strategy, scanner use, or intraday work (needs a data subscription; quotes are about 15 minutes delayed).
- Docker and unattended running (`AUTO_RESTART_TIME`, `TWOFA_TIMEOUT_ACTION`); do it once Phases 1 to 4 exist, since an unattended bot without them is dangerous.
- MCP server or letting Claude place orders. Phase 1 is the prerequisite.
- ZeroMQ, databases, event frameworks, mutation testing, switching to Client Portal API, adopting Lean or nautilus.
- Leverage, bigger sizes, more trades. The reference that went that way (ibkr-algo-trader's "WAY_BETTER") is the cautionary example.

## Later, cheap additions (after Phase 4)

Dead-man's ping that alerts on silence; order-rate ceiling that trips `halt`; a price plausibility check; an exchange calendar with early closes; no API jobs 23:30 to 01:00 ET; a daily loss limit that blocks new entries only.

## Risks to watch

- Phase 1 changes every existing tool: keep each tool's tests green as it moves over.
- A guard only protects what goes through it. Anything that calls `ib.placeOrder` directly bypasses it, so grep for that at the end of each phase.
- Paper fills are optimistic in thin books and ignore queue position; treat paper results as an upper bound.
