# Tempo

Day / swing / active trading on an **Interactive Brokers paper account**. Python, `ib_async`, IB Gateway. Paper only: non-paper accounts are refused at connect time (`tempo/ibkr.py`).

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
| `python -m tempo.health` | Account health: paper check, equity, cash, buying power, clock skew, positions, open orders | no |
| `python -m tempo.smoke [SYMBOL]` | Read-only API tests: qualify, contract details, snapshot, history start, daily bars | no |
| `python -m tempo.size SYMBOL STOP` | Shares allowed by `rules.json` for a long trade, using your equity in USD | no |
| `IBKR_READONLY=0 python -m tempo.roundtrip [SYMBOL]` | Places a far-below-market limit buy, watches it, cancels it | yes (cannot fill) |

On Windows PowerShell set the variable first: `$env:IBKR_READONLY=0`. Tests: `pytest`.

## Rules
`rules.json` holds the risk rules (percent of equity): `risk_per_trade_pct` is the most you lose if the stop hits, `max_position_pct` caps one position's value. Sizing takes the smaller result.

## Docs
See [docs/](docs/README.md): IBKR gotchas, market hours, roadmap, and research notes.
