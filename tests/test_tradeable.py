import pytest

from tempo.tradeable import tradeable_scores, untradeable_reason


def sig(sid, direction, **features):
    return {"signal_id": sid, "source": sid.split(":")[0], "direction": direction, "features": features}


def test_only_a_short_with_known_zero_availability_is_untradeable():
    assert untradeable_reason(sig("a:X:1", -1, borrow_known=True, borrow_available=0)) == "no shares available to borrow"
    assert untradeable_reason(sig("a:X:1", 1, borrow_known=True, borrow_available=0)) is None          # a long needs no borrow
    assert untradeable_reason(sig("a:X:1", -1, borrow_known=True, borrow_available=100)) is None
    assert untradeable_reason(sig("a:X:1", -1, borrow_known=True, borrow_available=None)) is None      # NA is unknown, not zero
    assert untradeable_reason(sig("a:X:1", -1, borrow_known=False)) is None
    assert untradeable_reason(sig("a:X:1", -1)) is None                                                # old signal, no borrow terms
    assert untradeable_reason({"direction": -1, "features": None}) is None


def test_scores_of_untradeable_signals_are_left_out_and_counted_per_source():
    signals = [sig("a:X:1", -1, borrow_known=True, borrow_available=0), sig("a:Y:1", -1, borrow_known=True, borrow_available=5),
               sig("b:Z:1", -1, borrow_known=True, borrow_available=0)]
    scores = [{"signal_id": s["signal_id"], "source": s["source"]} for s in signals]
    kept, excluded = tradeable_scores(signals, scores)
    assert [r["signal_id"] for r in kept] == ["a:Y:1"] and excluded == {"a": 1, "b": 1}


def test_a_score_without_a_signal_is_an_error_not_a_silent_keep():
    with pytest.raises(ValueError):
        tradeable_scores([], [{"signal_id": "a:X:1", "source": "a"}])
