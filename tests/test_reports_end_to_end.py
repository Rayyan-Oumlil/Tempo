"""Every strategy runner, end to end, on synthetic data that contains NO edge.

mmr's first rule of strategy evaluation: ask what the pipeline reports on nothing. These tests feed the real runners
(real data loading, real alignment, real engines, real verdicts) random-walk prices and require that they run to the end
and do not say PASS. A runner that passes noise has a wiring bug.
"""
import csv
import json
import random
from datetime import date, timedelta

import pytest

import tempo.data
from tempo import (evidence, forward, meanrev_report, overnight_report, pairs_report, rotation_report,
                   tactical_report)

DAYS = 4000   # the pairs runner insists on at least 15 years (3780 days) of history per leg


def weekdays(n: int, start: date = date(2005, 1, 3)) -> list[str]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def symbols_needed() -> set[str]:
    root = tempo.data.Path(tempo.data.__file__).resolve().parents[1] / "evidence"
    rotation = json.loads((root / "momentum_rotation.json").read_text(encoding="utf-8"))["universe"]
    pairs = json.loads((root / "pairs_trading.json").read_text(encoding="utf-8"))["candidate_pairs"]
    tactical = json.loads((root / "tactical_allocation.json").read_text(encoding="utf-8"))["universe"].values()
    return set(rotation) | {s for pair in pairs for s in pair} | set(tactical) | {"SPY", "QQQ"}


@pytest.fixture(scope="module")
def noise_data(tmp_path_factory):
    folder = tmp_path_factory.mktemp("noise")
    dates = weekdays(DAYS)
    for i, symbol in enumerate(sorted(symbols_needed())):
        rng, price = random.Random(1000 + i), 100.0
        closes, opens, highs, lows = [], [], [], []
        for _ in dates:
            open_ = price * (1 + rng.gauss(0.0001, 0.004))
            close = open_ * (1 + rng.gauss(0.0001, 0.010))
            opens.append(open_), closes.append(close)
            highs.append(max(open_, close) * (1 + abs(rng.gauss(0, 0.003)))), lows.append(min(open_, close) * (1 - abs(rng.gauss(0, 0.003))))
            price = close
        with (folder / f"{symbol}_1d.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date", "close"])
            w.writerows(zip(dates, closes))
        if symbol in ("SPY", "QQQ"):
            with (folder / f"{symbol}_ohlc.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["date", "open", "high", "low", "close"])
                w.writerows(zip(dates, opens, highs, lows, closes))
    return folder


@pytest.fixture
def on_noise(noise_data, monkeypatch):
    monkeypatch.setattr(tempo.data, "DATA_DIR", noise_data)
    for module in (rotation_report, pairs_report, meanrev_report, tactical_report):
        monkeypatch.setattr(module, "N_SHUFFLES", 4)
    return noise_data


def test_rotation_runner_does_not_pass_noise(on_noise):
    text, passed = rotation_report.report()
    assert "VERDICT" in text and passed is False
    assert "equal weight all (bench)" in text and "SPY buy and hold (bench)" in text


def test_pairs_runner_does_not_pass_noise(on_noise):
    text, passed = pairs_report.report()
    assert "VERDICT" in text and passed is False
    assert "pairs kept 10" in text and "W=60 E=2.0 (primary)" in text   # the synthetic data gives every symbol full history


def test_overnight_runner_does_not_pass_noise(on_noise):
    text, passed = overnight_report.report()
    assert "VERDICT" in text and passed is False
    assert "break-even slippage" in text and "SPY by year" in text


def test_mean_reversion_runner_does_not_pass_noise(on_noise):
    text, passed = meanrev_report.report()
    assert "VERDICT" in text and passed is False
    assert "REFERENCE ONLY" in text and "RSI(2) on SPY (primary)" in text


def test_tactical_runner_does_not_pass_noise(on_noise):
    text, passed = tactical_report.report()
    assert "VERDICT" in text and passed is False
    assert "identical for every row" in text and "60/40 SPY/AGG" in text


def test_forward_runner_refuses_a_verdict_when_no_trips_exist(on_noise):
    text = forward.report(today=date(2026, 11, 4))
    assert "NOT ENOUGH TRIPS" in text and "VERDICT" not in text


def test_the_original_evidence_runner_runs_on_noise(on_noise):
    text = evidence.report("SPY", 200, n_shuffles=5)
    assert "buy and hold" in text and "variants tried: 1" in text


def test_pairs_runner_drops_a_pair_with_short_history_and_says_why(on_noise, tmp_path, monkeypatch):
    import shutil
    folder = tmp_path / "short"
    shutil.copytree(on_noise, folder)
    rows = (folder / "PEP_1d.csv").read_text(encoding="utf-8").splitlines()
    kept = rows[:1] + rows[-2000:]   # the header and the last 2000 days: about 8 years only
    (folder / "PEP_1d.csv").write_text("\n".join(kept) + "\n", encoding="utf-8")
    monkeypatch.setattr(tempo.data, "DATA_DIR", folder)
    text, passed = pairs_report.report()
    assert "pairs kept 9" in text and "pair dropped KO/PEP: PEP has 2000 days, under the 3780 needed" in text and passed is False
