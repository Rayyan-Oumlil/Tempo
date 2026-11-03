from tempo.rotation_report import Metrics, verdict

GOOD = dict(sharpe=0.9, max_dd=-0.2, half1=0.8, half2=0.7)


def metrics(**over):
    return Metrics(**{**GOOD, **over})


def run(primary=None, spy=None, ew=None, beat=97.0, variants=(0.8, 0.8, 0.8, 0.8)):
    return verdict(primary or metrics(), spy or metrics(sharpe=0.5, max_dd=-0.55), ew or metrics(sharpe=0.6),
                   beat, list(variants))


def test_passes_when_every_criterion_holds():
    assert all(ok for _, ok in run())


def test_fails_if_it_does_not_beat_equal_weight():
    assert not all(ok for _, ok in run(ew=metrics(sharpe=1.0)))


def test_fails_if_it_does_not_beat_spy():
    assert not all(ok for _, ok in run(spy=metrics(sharpe=1.2, max_dd=-0.55)))


def test_fails_if_drawdown_is_not_shallower_than_spy():
    assert not all(ok for _, ok in run(primary=metrics(max_dd=-0.6)))


def test_fails_if_a_half_is_negative():
    assert not all(ok for _, ok in run(primary=metrics(half2=-0.1)))


def test_fails_below_95_percent_of_shuffles():
    assert not all(ok for _, ok in run(beat=94.0))


def test_fails_if_variants_are_fragile():
    assert not all(ok for _, ok in run(variants=(0.8, 0.8, 0.3, 0.3)))  # only 3 of 5 incl. primary beat equal weight
