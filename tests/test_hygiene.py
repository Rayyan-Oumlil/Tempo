import pytest

from tempo.hygiene import SUFFIX, clean_view, contamination, spac_like

C, O = "insider_cluster_v1", "insider_opportunistic_v1"


def sig(source, symbol, **features):
    return {"signal_id": f"{source}:{symbol}:1", "source": source, "symbol": symbol, "features": features}


@pytest.mark.parametrize("symbol,expected", [("NONE", True), ("NA", True), ("ABCDU", True), ("ABCDW", True), ("ABCU", False),
                                             ("ABCDE", False), ("AAPL", False), ("ABCDUX", False)])
def test_spac_like_symbols(symbol, expected):
    assert spac_like(symbol) is expected


def test_whole_dollar_with_three_or_more_insiders_is_an_ipo_allocation():
    assert contamination(sig(C, "AAA", vwap=10.0, n_insiders=3)) == "whole-dollar price with several insiders (IPO allocation)"
    assert contamination(sig(C, "AAA", vwap=10.004, n_insiders=5)) is not None
    assert contamination(sig(C, "AAA", vwap=10.0, n_insiders=2)) is None           # two insiders at a round price is plausible
    assert contamination(sig(C, "AAA", vwap=10.02, n_insiders=3)) is None
    assert contamination(sig(O, "AAA", vwap=20.0, n_opportunistic=3)) is not None   # the opportunistic source names its count differently


def test_spac_symbol_is_contaminated_whatever_the_price():
    assert contamination(sig(C, "ABCDU", vwap=10.37, n_insiders=1)) == "placeholder or SPAC-like symbol"


def test_missing_features_and_other_sources_are_never_contaminated():
    assert contamination(sig(C, "AAA")) is None
    assert contamination({"source": C, "symbol": "AAA", "features": None}) is None
    assert contamination(sig("weekly_reversal_v1", "NONE", vwap=10.0, n_insiders=9)) is None


def test_clean_view_relabels_only_clean_insider_scores_and_keeps_originals_untouched():
    signals = [sig(C, "GOOD", vwap=12.34, n_insiders=3), sig(C, "ABCDU", vwap=10.0, n_insiders=3), sig(O, "FINE", vwap=7.5, n_opportunistic=1),
               sig("weekly_reversal_v1", "XXXX")]
    scores = [{"signal_id": s["signal_id"], "source": s["source"], "net_excess": 0.01} for s in signals]
    view = clean_view(signals, scores)
    assert [r["source"] for r in view] == [C + SUFFIX, O + SUFFIX]
    assert all(r["source"] == s["source"] for r, s in zip(scores, signals))


def test_a_score_without_a_signal_is_an_error():
    with pytest.raises(ValueError):
        clean_view([], [{"signal_id": "x", "source": C}])
