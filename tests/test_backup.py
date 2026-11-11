import json
from datetime import datetime, timezone

import pytest

from tempo import backup


def _tree(root):
    (root / "journal").mkdir()
    (root / "journal" / "journal.jsonl").write_text(json.dumps({"kind": "intent"}) + "\n", encoding="utf-8")
    (root / "journal" / "journal.lock").write_text("x")
    (root / "ledger").mkdir()
    (root / "ledger" / "ledger.jsonl").write_text(json.dumps({"kind": "signal"}) + "\n", encoding="utf-8")
    (root / "state.json").write_text("{}")
    (root / ".env").write_text("SECRET=1")


def test_backup_round_trips_and_leaves_secrets_and_locks_out(tmp_path):
    root, dest = tmp_path / "root", tmp_path / "bk"
    root.mkdir(); _tree(root)
    archive = backup.create(root, dest, datetime(2026, 11, 11, 21, 0, tzinfo=timezone.utc))
    checked = backup.verify(archive, root)
    assert "journal.jsonl: 1 records" in checked and "ledger.jsonl: 1 records" in checked
    names = __import__("tarfile").open(archive).getnames()
    assert ".env" not in names and not any(n.endswith(".lock") for n in names)


def test_a_corrupted_archive_fails_verification(tmp_path):
    root, dest = tmp_path / "root", tmp_path / "bk"
    root.mkdir(); _tree(root)
    archive = backup.create(root, dest, datetime(2026, 11, 11, 21, 0, tzinfo=timezone.utc))
    archive.write_bytes(archive.read_bytes()[:-20] + b"x" * 20)
    with pytest.raises(backup.BackupError):
        backup.verify(archive, root)


def test_a_journal_corrupted_in_the_middle_fails_the_restore_check(tmp_path):
    root, dest = tmp_path / "root", tmp_path / "bk"
    root.mkdir(); _tree(root)
    (root / "journal" / "journal.jsonl").write_text('{"a":1}\nnot json\n{"b":2}\n', encoding="utf-8")
    archive = backup.create(root, dest, datetime(2026, 11, 11, 21, 0, tzinfo=timezone.utc))
    with pytest.raises(ValueError):
        backup.verify(archive, root)


def test_prune_keeps_only_the_newest(tmp_path):
    for d in range(1, 6):
        (tmp_path / f"tempo-2026111{d}-2100.tar.gz").write_bytes(b"x")
    removed = backup.prune(tmp_path, keep=2)
    assert len(removed) == 3 and backup.latest(tmp_path).name == "tempo-20261115-2100.tar.gz"


def test_unsafe_archive_paths_are_refused(tmp_path):
    import io, tarfile
    bad = tmp_path / "bad.tar.gz"
    with tarfile.open(bad, "w:gz") as t:
        info = tarfile.TarInfo("../evil"); info.size = 1
        t.addfile(info, io.BytesIO(b"x"))
    with pytest.raises(backup.BackupError):
        backup.restore(bad, tmp_path / "out")
