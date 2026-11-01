# active-trading

Day / swing / active trading on an **Interactive Brokers paper account**. Currently: connection + read-only health check.

## Setup
1. IB Gateway (stable) → log in with the **paper** username.
2. Gateway → Configure → Settings → API → Settings: enable *ActiveX and Socket Clients*, socket port `4002`, keep *Read-Only API* checked, trusted IP `127.0.0.1`.
3. ```
   python -m venv .venv && .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env
   ```

## Health check
```
python -m trader.health
```
Checks: paper account (DU*/DF*), equity, cash, buying power, clock skew vs IB server, open positions/orders. Exit code 0 = healthy.

Non-paper accounts are refused at connect time (`trader/ibkr.py`). Tests: `pytest`.
