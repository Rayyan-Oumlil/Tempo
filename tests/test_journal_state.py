import json

import pytest

from tempo.journal import Journal
from tempo.state import get_mode, set_mode


def test_journal_appends_and_reads_back(tmp_path):
    j = Journal(tmp_path / "j.jsonl", clock=lambda: 100.0)
    j.append("intent", ref="a", symbol="SPY")
    j.append("outcome", ref="a", status="Filled")
    recs = j.records()
    assert [r["kind"] for r in recs] == ["intent", "outcome"]
    assert recs[0]["ts"] == 100.0 and recs[0]["symbol"] == "SPY"


def test_unresolved_is_intent_without_outcome_or_resolution(tmp_path):
    j = Journal(tmp_path / "j.jsonl")
    j.append("intent", ref="a")
    j.append("intent", ref="b")
    j.append("intent", ref="c")
    j.append("outcome", ref="a", status="Filled")
    j.append("resolution", ref="b", status="found")
    assert [r["ref"] for r in j.unresolved()] == ["c"]


def test_corrupt_line_fails_loudly(tmp_path):
    path = tmp_path / "j.jsonl"
    path.write_text('{"kind": "intent", "ref": "a"}\nnot json\n', encoding="utf-8")
    with pytest.raises(ValueError, match="line 2"):
        Journal(path).records()


def test_missing_journal_is_empty(tmp_path):
    assert Journal(tmp_path / "none.jsonl").records() == []


def test_mode_defaults_to_normal_when_no_file(tmp_path):
    assert get_mode(tmp_path / "state.json") == "normal"


def test_set_and_get_mode_roundtrip(tmp_path):
    path = tmp_path / "state.json"
    set_mode("reduce_only", "test", path)
    assert get_mode(path) == "reduce_only"
    set_mode("normal", "back", path)
    assert get_mode(path) == "normal"


def test_unreadable_or_unknown_state_fails_closed(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("garbage", encoding="utf-8")
    assert get_mode(path) == "reduce_only"
    path.write_text(json.dumps({"mode": "yolo"}), encoding="utf-8")
    assert get_mode(path) == "reduce_only"


def test_set_mode_rejects_unknown_mode(tmp_path):
    with pytest.raises(ValueError):
        set_mode("halt", "x", tmp_path / "s.json")
