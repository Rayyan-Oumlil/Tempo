"""Connection settings, read from the environment (.env is loaded by the entrypoint)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class IbkrConfig:
    host: str
    port: int
    client_id: int
    readonly: bool
    timeout: float


def load_config(env: Mapping[str, str] | None = None) -> IbkrConfig:
    env = os.environ if env is None else env
    try:
        return IbkrConfig(
            host=env.get("IBKR_HOST", "127.0.0.1"),
            port=int(env.get("IBKR_PORT", "4002")),  # IB Gateway paper; TWS paper is 7497
            client_id=int(env.get("IBKR_CLIENT_ID", "21")),
            readonly=env.get("IBKR_READONLY", "1") == "1",
            timeout=float(env.get("IBKR_TIMEOUT", "20")),
        )
    except ValueError as exc:
        raise ValueError(f"Invalid IBKR_* setting in environment: {exc}") from exc
