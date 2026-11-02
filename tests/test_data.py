import pytest

from tempo.data import load_closes, save_bars


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "SPY_1d.csv"
    save_bars(path, [("2026-01-02", 100.5), ("2026-01-05", 101.25)])
    dates, closes = load_closes(path)
    assert dates == ["2026-01-02", "2026-01-05"] and closes == [100.5, 101.25]


def test_load_rejects_unsorted_dates(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text("date,close\n2026-01-05,1\n2026-01-02,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sorted"):
        load_closes(path)


def test_load_rejects_non_positive_or_missing_prices(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text("date,close\n2026-01-02,0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="positive"):
        load_closes(path)
    with pytest.raises(FileNotFoundError):
        load_closes(tmp_path / "nope.csv")
