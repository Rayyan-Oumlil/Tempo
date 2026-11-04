# Tempo

Day / swing / active trading on an **Interactive Brokers paper account**. Python, `ib_async`, IB Gateway. Paper only: non-paper accounts are refused at connect time (`tempo/ibkr.py`) and again on every order (`tempo/orders.py`).

## Setup
1. IB Gateway (stable) → choose **IB API** and **Paper Trading**, log in with the paper login.
2. Gateway → Configure → Settings → API → Settings: enable *ActiveX and Socket Clients*, socket port `4002`, trusted IP `127.0.0.1`. Keep *Read-Only API* ticked unless you are running the order tools.
3. ```
   python -m venv .venv && .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   ```

## Commands

| Command | What it does | Places orders? |
|---|---|---|
| `python -m tempo.health` | Account health, plus trading mode and unresolved journal entries | no |
| `python -m tempo.smoke [SYMBOL]` | Read-only API tests: qualify, contract details, snapshot, history start, daily bars | no |
| `python -m tempo.size SYMBOL STOP` | Shares allowed by `rules.json` for a long trade | no |
| `python -m tempo.reconcile [--accept-missing]` | Match journal entries with the broker's orders and fills; clears or reports unresolved ones | no |
| `python -m tempo.state [normal\|reduce_only] [why]` | Show or set the trading mode | no |
| `python -m tempo.data SYMBOL [YEARS]` | Download daily bars to `data/` | no |
| `python -m tempo.evidence SYMBOL [SMA_WINDOW]` | Backtest baselines and a trend rule on saved bars, with a shuffled-data control | no |
| `IBKR_READONLY=0 python -m tempo.roundtrip [SYMBOL]` | Places a far-below-market limit buy, watches it, cancels it | yes (cannot fill) |
| `IBKR_READONLY=0 python -m tempo.lifecycle [SYMBOL] [QTY]` | Market buy, confirm, market sell, report P&L and cash (regular hours) | yes (fills) |
| `IBKR_READONLY=0 python -m tempo.bracket SYMBOL STOP [TP] [QTY]` | Market buy with a stop (and optional take-profit) resting at IBKR | yes (fills) |
| `IBKR_READONLY=0 python -m tempo.flatten [SYMBOL]` | Cancel that symbol's resting orders, then close longs and shorts | yes (fills) |
| `IBKR_READONLY=0 python -m tempo.kill` | Switch to `reduce_only`, cancel every order, flatten everything, confirm flat | yes (fills) |

On Windows PowerShell set the variable first: `$env:IBKR_READONLY=0`.

### Research and forward-test commands (no orders unless noted)

| Command | What it does |
|---|---|
| `python -m tempo.rotation_report`, `pairs_report`, `overnight_report`, `meanrev_report`, `tactical_report` | Run one pre-registered strategy test (rules in `evidence/*.json`) on saved data and print the verdict. Results so far: all FAIL, see `docs/research/log.md` |
| `python -m tempo.data SYMBOL [YEARS] [--ohlc]` | Download daily bars (closes, or open/high/low/close) to `data/` |
| `python -m tempo.edgar TICKER [DATE] [brief]` | Print a company's earnings press release (SEC 8-K item 2.02). Needs `SEC_USER_AGENT` in `.env` (a contact string; the SEC requires one) |
| `python -m tempo.insider DATE [DATE ...]` | Collect SEC Form 4 insider purchases for those days, in order, and record clusters as ledger signals |
| `python -m tempo.ledger` | Show the signal ledger: counts and statistics per source and horizon (no verdict before 30 scored signals) |
| `python -m tempo.ledger add SOURCE SYMBOL long\|short EVENT_ID --confidence 1-5 ...` | Record one forward call |
| `python -m tempo.ledger_score` | Score the ledger's signals against what happened (needs the Gateway for prices) |
| `python -m tempo.forward` | Forward test of the frozen mean-reversion rules (prints NOT ENOUGH TRIPS until 60 round trips exist) |
| `IBKR_READONLY=0 python -m tempo.paper_run plan\|entries\|exits\|status` | Trade the ledger's signals on the paper account through the order door (see `evidence/paper_run.json`) |
| `python tools/golden.py snapshot\|record\|check` | Prove a refactor of the report runners changes none of their numbers |

**Tests:** `pytest` runs the fast offline suite (GitHub Actions runs it, plus `ruff check .`, on every push; dev tools: `pip install -r requirements-dev.txt`). `TEMPO_LIVE=1 pytest tests/live` (PowerShell: `$env:TEMPO_LIVE=1; pytest tests/live`) runs five checks against the paper account during regular hours: lifecycle, bracket plus kill, take-profit exit, kill on a long and a short, and crash recovery. It places real paper orders and leaves the account flat. Tests that need the regular session skip themselves outside it.

## How orders are kept safe
Every order goes through `tempo/orders.py` (`place`); nothing else calls `ib.placeOrder`. It refuses non-paper accounts and duplicates, sets `tif`, tags the order with a unique `orderRef`, and writes the intent to `journal/journal.jsonl` **before** sending. New entries also need: mode `normal`, regular hours, a known equity and price, size under the position cap, the account not down more than `max_daily_loss_pct` today, and no stale unresolved journal entries. Orders that reduce a live position are never refused by those limits.

## Rules
`rules.json` holds the risk rules (percent of equity): `risk_per_trade_pct` is the most you lose if the stop hits, `max_position_pct` caps one position's value (and every entry), `max_daily_loss_pct` stops new entries once the account is that far down today (exits are never blocked; if IBKR's daily P&L cannot be read, entries are refused). Sizing takes the smaller of the first two.

## Docs
See [docs/](docs/README.md): IBKR gotchas, market hours, the foundations plan, roadmap, research log, and research notes.
