import pytest

from tempo.reporting import by_year, daily_returns


def test_daily_returns_of_a_series():
    assert daily_returns([100.0, 110.0, 99.0]) == [pytest.approx(0.10), pytest.approx(-0.10)]
    assert daily_returns([5.0]) == []


def test_by_year_chains_from_the_last_value_of_the_previous_year():
    dates = ["2020-12-30", "2020-12-31", "2021-01-04", "2021-01-05", "2022-01-03"]
    equity = [100.0, 110.0, 121.0, 99.0, 198.0]
    result = by_year(dates, equity)
    assert [y for y, _ in result] == ["2020", "2021", "2022"]
    assert result[0][1] == pytest.approx(110.0 / 100.0 - 1)           # first year: relative to its own first value
    assert result[1][1] == pytest.approx(99.0 / 110.0 - 1)            # 2021 starts from the end of 2020
    assert result[2][1] == pytest.approx(198.0 / 99.0 - 1)


def test_by_year_of_a_single_year():
    assert by_year(["2020-01-02", "2020-01-03"], [100.0, 105.0]) == [("2020", pytest.approx(0.05))]
