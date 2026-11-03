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


from tempo.data import Bars, load_ohlc, ohlc_path, save_ohlc

ROWS = [("2026-01-02", 100.0, 101.0, 99.0, 100.5), ("2026-01-05", 100.6, 102.0, 100.0, 101.9)]


def test_ohlc_roundtrip(tmp_path):
    path = tmp_path / "SPY_ohlc.csv"
    save_ohlc(path, ROWS)
    bars = load_ohlc(path)
    assert bars == Bars(dates=["2026-01-02", "2026-01-05"], open=[100.0, 100.6], high=[101.0, 102.0],
                        low=[99.0, 100.0], close=[100.5, 101.9])


def test_ohlc_path_is_separate_from_the_close_only_file():
    assert ohlc_path("SPY").name == "SPY_ohlc.csv"


def test_ohlc_rejects_unsorted_dates(tmp_path):
    path = tmp_path / "x.csv"
    save_ohlc(path, list(reversed(ROWS)))
    with pytest.raises(ValueError, match="sorted"):
        load_ohlc(path)


def test_ohlc_rejects_non_positive_prices(tmp_path):
    path = tmp_path / "x.csv"
    save_ohlc(path, [("2026-01-02", 0.0, 101.0, 99.0, 100.5)])
    with pytest.raises(ValueError, match="positive"):
        load_ohlc(path)


@pytest.mark.parametrize("row", [("2026-01-02", 100.0, 99.0, 98.0, 98.5),    # high below the open
                                 ("2026-01-02", 100.0, 101.0, 100.5, 100.2),  # low above the close
                                 ("2026-01-02", 100.0, 99.0, 101.0, 100.0)])  # high below low
def test_ohlc_rejects_impossible_bars(tmp_path, row):
    path = tmp_path / "x.csv"
    save_ohlc(path, [row])
    with pytest.raises(ValueError, match="impossible"):
        load_ohlc(path)


def test_ohlc_allows_tiny_rounding_in_adjusted_prices(tmp_path):
    path = tmp_path / "x.csv"
    save_ohlc(path, [("2026-01-02", 100.0, 100.0, 99.0, 100.00001)])  # close a hair above the high
    assert load_ohlc(path).close == [100.00001]
