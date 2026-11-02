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
| `python -m tempo.gate metrics.json` | Check results against the pre-registered criteria in `evidence/gate.json` | no |
| `IBKR_READONLY=0 python -m tempo.roundtrip [SYMBOL]` | Places a far-below-market limit buy, watches it, cancels it | yes (cannot fill) |
| `IBKR_READONLY=0 python -m tempo.lifecycle [SYMBOL] [QTY]` | Market buy, confirm, market sell, report P&L and cash (regular hours) | yes (fills) |
| `IBKR_READONLY=0 python -m tempo.bracket SYMBOL STOP [TP] [QTY]` | Market buy with a stop (and optional take-profit) resting at IBKR | yes (fills) |
| `IBKR_READONLY=0 python -m tempo.flatten [SYMBOL]` | Cancel that symbol's resting orders, then close longs and shorts | yes (fills) |
| `IBKR_READONLY=0 python -m tempo.kill` | Switch to `reduce_only`, cancel every order, flatten everything, confirm flat | yes (fills) |

On Windows PowerShell set the variable first: `$env:IBKR_READONLY=0`. Tests: `pytest`.

## How orders are kept safe
Every order goes through `tempo/orders.py` (`place`); nothing else calls `ib.placeOrder`. It refuses non-paper accounts and duplicates, sets `tif`, tags the order with a unique `orderRef`, and writes the intent to `journal/journal.jsonl` **before** sending. New entries also need: mode `normal`, regular hours, a known equity and price, size under the position cap, and no stale unresolved journal entries. Orders that reduce a live position are never refused by those limits.

## Rules
`rules.json` holds the risk rules (percent of equity): `risk_per_trade_pct` is the most you lose if the stop hits, `max_position_pct` caps one position's value (and every entry). Sizing takes the smaller result.

## Docs
See [docs/](docs/README.md): IBKR gotchas, market hours, the foundations plan, roadmap, research log, and research notes.
