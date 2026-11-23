import numpy as np
import pandas as pd
import pytest

from tempo import history_y as y
from tempo import x4_signal as s


def closes(vals):
    return pd.Series(vals, index=pd.date_range("2022-01-01", periods=len(vals)), dtype="float64")


def test_signal_matches_the_frozen_backtest_weight():
    rng = np.random.default_rng(3)
    c = closes(100 * np.cumprod(1 + rng.normal(0.002, 0.03, 400)))
    sig = s.compute_signal(c)
    assert sig.target_weight == pytest.approx(y.x4_weights(c.rename("BTC-USD")).iloc[-1, 0])
    assert sig.signal_on == (c.iloc[-1] > c.rolling(100).mean().iloc[-1])


def test_off_signal_means_zero_weight():
    c = closes(np.r_[np.linspace(100, 200, 200), np.linspace(200, 80, 100)])
    sig = s.compute_signal(c)
    assert not sig.signal_on and sig.target_weight == 0.0


def test_too_little_history_fails_loudly():
    with pytest.raises(ValueError):
        s.compute_signal(closes(np.full(50, 100.0)))


def test_describe_prints_notional_and_states_no_order():
    rng = np.random.default_rng(4)
    sig = s.compute_signal(closes(100 * np.cumprod(1 + rng.normal(0.003, 0.02, 300))))
    text = s.describe(sig, 10_000)
    assert "PRINT ONLY" in text and "BTC" in text
