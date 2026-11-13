import json
import random
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from tempo.champion import Pair, RegistryError, daily_means, load_pair, load_registry, report, require_registered, verdict
from tempo.ledger import Ledger
from tempo.short_volume import VARIANTS, Variant, select

ET = ZoneInfo("America/New_York")


def pair(**kw):
    base = dict(challenger="short_volume_v2", champion="short_volume_v1", registered=date(2026, 11, 12), change="skip weak z",
                reason="autopsy pattern", min_days=30, margin=0.001, t_min=2.0)
    return Pair(**{**base, **kw})


def series(n, f):
    return {f"2026-12-{i + 1:02d}" if i < 31 else f"2027-01-{i - 30:02d}": f(i) for i in range(n)}


def test_too_early_until_enough_common_days():
    v, why = verdict(pair(), series(29, lambda i: 0.0), series(29, lambda i: 0.01), "2026-12-01")
    assert v == "TOO EARLY" and "29 of 30" in why


def test_a_clear_and_stable_improvement_is_a_promote_candidate_but_only_a_candidate():
    rng = random.Random(1)
    champ = series(60, lambda i: rng.gauss(0.000, 0.004))
    chall = {d: v + 0.004 + rng.gauss(0, 0.001) for d, v in champ.items()}
    v, why = verdict(pair(), champ, chall, "2026-12-01")
    assert v == "PROMOTE CANDIDATE" and "FAIL" not in why


def test_each_promotion_condition_blocks_promotion_on_its_own():
    rng = random.Random(2)
    champ = series(60, lambda i: rng.gauss(0, 0.004))
    better = {d: v + 0.004 + rng.gauss(0, 0.001) for d, v in champ.items()}
    assert verdict(pair(margin=0.01), champ, better, "2026-12-01")[0] == "KEEP CHAMPION"            # gain below the margin
    assert verdict(pair(), champ, {d: v + 0.004 + rng.gauss(0, 0.05) for d, v in champ.items()}, "2026-12-01")[0] == "KEEP CHAMPION"   # noisy: t too low
    first_half_only = {d: v + (0.01 if i < 30 else -0.0005) for i, (d, v) in enumerate(champ.items())}
    assert verdict(pair(), champ, first_half_only, "2026-12-01")[0] == "KEEP CHAMPION"             # one lucky half
    weak_champ = {d: -0.05 for d in champ}
    still_negative = {d: -0.04 + rng.gauss(0, 0.0005) for d in champ}
    assert verdict(pair(), weak_champ, still_negative, "2026-12-01")[0] == "KEEP CHAMPION"         # better than a loser, still a loser


def test_a_challenger_registered_on_or_after_its_first_signal_is_void():
    s = series(60, lambda i: 0.0)
    assert verdict(pair(registered=date(2026, 12, 1)), s, s, "2026-12-01")[0] == "INVALID"
    assert verdict(pair(registered=date(2026, 12, 2)), s, s, "2026-12-01")[0] == "INVALID"
    assert verdict(pair(registered=date(2026, 11, 30)), s, s, "2026-12-01")[0] != "INVALID"


def write(folder, name="short_volume_v2", **over):
    body = {"challenger": name, "champion": "short_volume_v1", "registered": "2026-11-12", "change": "skip weak z",
            "reason": "autopsy pattern", "promotion_rule": {"min_days": 60, "margin": 0.001, "t_min": 2.0}, **over}
    folder.mkdir(exist_ok=True)
    (folder / f"{name}.json").write_text(json.dumps(body), encoding="utf-8")
    return folder / f"{name}.json"


def test_registry_files_are_validated_strictly(tmp_path):
    assert load_pair(write(tmp_path)).min_days == 60
    for bad in ({"champion": "short_volume_v2"}, {"promotion_rule": {"min_days": 10, "margin": 0, "t_min": 2}},
                {"promotion_rule": {"min_days": 60, "margin": 0}}, {"promotion_rule": {"min_days": 60, "margin": 0, "t_min": 0.5}},
                {"change": " "}, {"registered": "soon"}):
        with pytest.raises(RegistryError):
            load_pair(write(tmp_path, **bad))
    path = write(tmp_path)
    path.rename(tmp_path / "other_name.json")
    with pytest.raises(RegistryError):
        load_pair(tmp_path / "other_name.json")                    # file name must equal the challenger
    assert load_registry(tmp_path / "missing") == []


def test_collectors_may_record_only_after_the_day_of_registration(tmp_path):
    write(tmp_path)
    with pytest.raises(RegistryError):
        require_registered("short_volume_v9", date(2026, 11, 20), tmp_path)           # unknown
    with pytest.raises(RegistryError):
        require_registered("short_volume_v2", date(2026, 11, 12), tmp_path)           # same day
    assert require_registered("short_volume_v2", date(2026, 11, 13), tmp_path).challenger == "short_volume_v2"


def test_every_variant_other_than_the_champion_has_a_registry_file():
    from pathlib import Path
    registry = Path(__file__).resolve().parents[1] / "evidence" / "challengers"
    for name in VARIANTS:
        if name != "short_volume_v1":
            assert (registry / f"{name}.json").exists(), f"{name} has no registry file: it would record unregistered signals"
    for p in load_registry(registry):
        assert p.champion in VARIANTS or p.champion.endswith("_v1")


def test_variant_filters_apply_after_the_champions_ordering():
    z = {f"S{i:03d}": (i - 60) / 20 for i in range(121)}                                       # z from -3 to +3
    base_l, base_s = select(z, Variant("c"))
    strict_l, strict_s = select(z, Variant("x", min_abs_z=2.8))
    assert len(base_l) == len(base_s) == 30 and all(abs(z[s]) >= 2.8 for s in strict_l + strict_s) and 0 < len(strict_l) < 30
    assert select(z, Variant("x", sides=("short",)))[0] == [] and select(z, Variant("x", sides=("long",)))[1] == []


def test_end_to_end_with_a_real_ledger(tmp_path):
    clock = {"t": 0.0}
    ledger = Ledger(tmp_path / "l.jsonl", clock=lambda: clock["t"])
    for i in range(35):
        day = datetime(2026, 12, 1, 20, 0, tzinfo=ET).timestamp() + i * 86400
        clock["t"] = day
        for source, ne in (("short_volume_v1", 0.001), ("short_volume_v2", 0.006)):
            sig = ledger.record_signal(source=source, symbol="AAA", direction=1, event_id=f"e{i}")
            ledger.record_scores([{"method": "exec_v2", "signal_id": sig["signal_id"], "source": source, "symbol": "AAA", "horizon": 5, "entry_date": "x",
                                   "exit_date": "y", "ret": ne, "bench_ret": 0.0, "excess": ne, "net_excess": ne + (i % 3) * 1e-4,
                                   "round_trip_cost": 0.002}])
    assert len(daily_means(ledger, "short_volume_v1", 5)) == 35
    folder = tmp_path / "reg"
    write(folder, registered="2026-11-30", promotion_rule={"min_days": 30, "margin": 0.001, "t_min": 2.0})
    text = report(ledger, folder)
    assert "short_volume_v2 vs short_volume_v1: PROMOTE CANDIDATE" in text and "35 days" in text
    assert "none registered" in report(ledger, tmp_path / "empty")


def test_a_noisy_gain_that_passes_every_other_condition_is_still_not_promoted_because_t_is_low():
    champ = series(60, lambda i: 0.01)
    chall = {d: 0.01 + (0.023 if i % 2 == 0 else -0.017) for i, d in enumerate(champ)}         # mean +0.3%, both halves +0.3%, sd 2%
    v, why = verdict(pair(margin=0.001, t_min=2.0), champ, chall, "2026-12-01")
    assert v == "KEEP CHAMPION" and "FAIL: t " in why and why.count("FAIL") == 1


def test_only_days_where_both_have_signals_are_compared():
    champ = series(60, lambda i: 0.0)
    chall = {d: 0.01 + (i % 5) * 1e-4 for i, d in enumerate(list(champ)[:40])}                  # the challenger skipped 20 days
    v, why = verdict(pair(), champ, chall, "2026-12-01")
    assert why.startswith("40 days") and v == "PROMOTE CANDIDATE"
    extra = {**chall, "2027-03-01": 9.9}                                                       # a day the champion does not have
    assert verdict(pair(), champ, extra, "2026-12-01")[1].startswith("40 days")
