"""IB Gateway connection. Paper accounts only: anything else is refused at connect time."""
from __future__ import annotations

from ib_async import IB

from tempo.config import IbkrConfig

PAPER_PREFIXES = ("DU", "DF")  # IBKR paper account ids


def assert_paper(account_id: str) -> None:
    if not account_id.startswith(PAPER_PREFIXES):
        raise RuntimeError(f"{account_id} is not a paper account (expected DU*/DF*). Refusing to continue.")


def _masked(account_id: str) -> str:
    return f"...{account_id[-3:]}" if len(account_id) > 3 else "..."


def assert_expected(account_id: str, cfg: IbkrConfig) -> None:
    """With orders enabled, the account must be pinned (IBKR_ACCOUNT) and match. Any pin is enforced, also read-only."""
    if cfg.account is None:
        if not cfg.readonly:
            raise RuntimeError("Orders are enabled but IBKR_ACCOUNT is not set in .env: refusing to guess which account to trade.")
        return
    if account_id != cfg.account:
        raise RuntimeError(f"Gateway is logged into account {_masked(account_id)}, not the IBKR_ACCOUNT {_masked(cfg.account)}. "
                           "Log Gateway into the right account. Refusing to continue.")


def connect(cfg: IbkrConfig) -> IB:
    """Connect once (no retry loop) and fail loudly. Disconnects again if the account is not paper."""
    ib = IB()
    try:
        ib.connect(
            cfg.host,
            cfg.port,
            clientId=cfg.client_id,
            timeout=cfg.timeout,
            readonly=cfg.readonly,
            raiseSyncErrors=True,  # a half-synced login must not look like an empty account
        )
    except (OSError, TimeoutError) as exc:
        ib.disconnect()
        raise ConnectionError(
            f"IB Gateway not reachable at {cfg.host}:{cfg.port} ({exc!r}). "
            "Is it running, logged into the PAPER account, with the API socket enabled on this port?"
        ) from exc

    accounts = ib.managedAccounts()
    if not accounts:
        ib.disconnect()
        raise ConnectionError("Gateway connected but reports no account yet; retry in a few seconds.")
    try:
        assert_paper(accounts[0])
        assert_expected(accounts[0], cfg)
    except RuntimeError:
        ib.disconnect()
        raise
    return ib
