"""Nightly backup of everything the VPS holds that git does not: journals, state, ledger, evidence, collected data.

Usage: python -m tempo.backup            (cron, nightly)   -> backups/tempo-YYYYMMDD-HHMM.tar.gz + .sha256
       python -m tempo.backup --restore-check ARCHIVE     -> extracts to a scratch folder and reads every journal back

A backup that was never restored is a hope, so every archive is verified right after it is written (whole archive read,
checksum written, journals parsed from the extracted copy). Secrets (.env, gateway.env) are deliberately NOT included.
"""
from __future__ import annotations

import hashlib
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "backups"
INCLUDE = ("journal", "state.json", "ledger", "evidence", "data", "logs")
EXCLUDE_SUFFIXES = (".lock",)
EXCLUDE_DIRS = ("data/insider_sets",)   # 116 MB of SEC zips that a rebuild downloads again
KEEP = 14


class BackupError(RuntimeError):
    pass


def _skip(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
    return None if info.name.endswith(EXCLUDE_SUFFIXES) or info.name.startswith(EXCLUDE_DIRS) else info


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def create(root: Path, dest_dir: Path, now: datetime) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    final = dest_dir / f"tempo-{now:%Y%m%d-%H%M}.tar.gz"
    partial = final.with_suffix(".gz.partial")
    with tarfile.open(partial, "w:gz") as tar:
        for name in INCLUDE:
            if (root / name).exists():
                tar.add(root / name, arcname=name, filter=_skip)
    partial.replace(final)
    Path(f"{final}.sha256").write_text(f"{sha256(final)}  {final.name}\n", encoding="utf-8")
    return final


def restore(archive: Path, target: Path) -> None:
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():   # never trust archive paths
            if Path(member.name).is_absolute() or ".." in Path(member.name).parts or member.issym() or member.islnk():
                raise BackupError(f"unsafe path in archive: {member.name}")
        tar.extractall(target, filter="data")


def verify(archive: Path, root: Path) -> list[str]:
    """Checks the checksum, restores into a scratch folder and reads every journal back. Returns what was checked."""
    from tempo.journal import Journal
    sidecar = Path(f"{archive}.sha256")
    if not sidecar.exists() or sidecar.read_text(encoding="utf-8").split()[0] != sha256(archive):
        raise BackupError(f"checksum mismatch or missing for {archive.name}")
    checked = ["checksum"]
    with tempfile.TemporaryDirectory() as scratch:
        restore(archive, Path(scratch))
        for name in INCLUDE:
            if (root / name).exists() and not (Path(scratch) / name).exists():
                raise BackupError(f"{name} exists on disk but is missing from the archive")
        for journal in sorted((Path(scratch) / "journal").glob("*.jsonl")) if (Path(scratch) / "journal").exists() else []:
            n = len(Journal(journal).records())   # raises on corruption
            checked.append(f"{journal.name}: {n} records")
        if (root / "ledger" / "ledger.jsonl").exists():
            n = len(Journal(Path(scratch) / "ledger" / "ledger.jsonl").records())
            checked.append(f"ledger.jsonl: {n} records")
    return checked


def prune(dest_dir: Path, keep: int = KEEP) -> list[Path]:
    archives = sorted(dest_dir.glob("tempo-*.tar.gz"))
    removed = archives[:-keep] if keep else archives
    for a in removed:
        a.unlink()
        Path(f"{a}.sha256").unlink(missing_ok=True)
    return removed


def latest(dest_dir: Path) -> Path | None:
    archives = sorted(dest_dir.glob("tempo-*.tar.gz"))
    return archives[-1] if archives else None


def main(argv: list[str]) -> int:  # pragma: no cover - entry point
    if argv[:1] == ["--restore-check"]:
        print("\n".join(verify(Path(argv[1]), ROOT)))
        return 0
    from zoneinfo import ZoneInfo
    archive = create(ROOT, BACKUP_DIR, datetime.now(ZoneInfo("America/New_York")))
    checked = verify(archive, ROOT)
    removed = prune(BACKUP_DIR)
    print(f"backup {archive.name} ({archive.stat().st_size / 1e6:.1f} MB) verified: {'; '.join(checked)}; pruned {len(removed)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as err:  # noqa: BLE001 - alert, then fail non-zero so cron mail/logs show it
        from tempo.notify import notify
        notify("Tempo BACKUP FAILED", f"{type(err).__name__}: {err}")
        print(f"[FAIL] {type(err).__name__}: {err}", file=sys.stderr)
        raise SystemExit(1)
