import math

from tempo import evidence
from tempo.data import save_bars


def test_report_runs_on_saved_data_and_lists_every_strategy(tmp_path, monkeypatch):
    path = tmp_path / "TEST_1d.csv"
    rows = [(f"2020-{1 + i // 28:02d}-{1 + i % 28:02d}", 100 + 10 * math.sin(i / 20) + i * 0.05) for i in range(300)]
    save_bars(path, rows)
    monkeypatch.setattr(evidence, "csv_path", lambda symbol: path)
    text = evidence.report("TEST", window=20, n_shuffles=10)
    for needle in ("flat", "buy and hold", "SMA 20 trend", "negative control (10 shuffled", "variants tried: 1"):
        assert needle in text
