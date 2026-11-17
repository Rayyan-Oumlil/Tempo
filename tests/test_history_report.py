from collections import Counter

from tempo.history_core import Trade, judge
from tempo.history_report import load_spy, load_universe, make_bar_lookup, missing_symbols, render


def test_bar_lookup_prefers_the_first_directory_and_skips_files_without_an_open_column(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "X.csv").write_text("date,open,close,volume\n2024-01-02,1,2,3\n", encoding="utf-8")
    (b / "X.csv").write_text("date,open,close,volume\n2024-01-02,9,9,9\n", encoding="utf-8")
    (a / "Y.csv").write_text("date,close,volume\n2024-01-02,2,3\n", encoding="utf-8")      # no open: unusable
    (b / "Y.csv").write_text("date,open,close,volume\n2024-01-02,7,8,9\n", encoding="utf-8")
    get = make_bar_lookup(a, b)
    assert get("X").open == [1.0] and get("Y").open == [7.0] and get("Z") is None


def test_missing_symbols_lists_each_once_sorted():
    sigs = {"s1": [("2024-01-03", "B"), ("2024-01-04", "A")], "s2": [("2024-01-05", "B"), ("2024-01-05", "C")]}
    assert missing_symbols(sigs, lambda s: object() if s == "C" else None) == ["A", "B"]


def test_load_spy_and_universe(tmp_path):
    (tmp_path / "SPY_ohlc.csv").write_text("date,open,high,low,close\n2024-01-02,100,101,99,100.5\n", encoding="utf-8")
    spy = load_spy(tmp_path / "SPY_ohlc.csv")
    assert spy.open == [100.0] and spy.close == [100.5] and spy.pos == {"2024-01-02": 0}
    bars = tmp_path / "bars"
    bars.mkdir()
    (bars / "AAA.csv").write_text("date,open,close,volume\n2024-01-02,1,2,3\n", encoding="utf-8")
    (bars / "SPY.csv").write_text("date,open,close,volume\n2024-01-02,1,2,3\n", encoding="utf-8")
    assert list(load_universe(bars)) == ["AAA"]


def test_render_states_the_decision_the_numbers_and_the_limits():
    trades = [Trade(f"{y}-{1 + i // 28:02d}-{1 + i % 28:02d}", "S", 0.03 + (0.004 if i % 2 else -0.004))
              for y in ("2023", "2024", "2025") for i in range(60) for _ in range(2)]
    text = render({"demo_v1": (judge(trades, 0.002, 5), Counter(scored=360), 0.002)})
    assert "demo_v1" in text and "=> FORWARD" in text and "survivorship" in text and "never real money" in text
