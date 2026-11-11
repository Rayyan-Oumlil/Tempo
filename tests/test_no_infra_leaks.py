"""The repo is public: nothing that identifies the server or holds a secret may ever be committed."""
import ipaddress
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = {".py", ".md", ".sh", ".json", ".yml", ".yaml", ".txt", ".ps1", ".toml", ".ini", ".example", ".cfg", ".env"}
SKIP = ("ledger/ledger.jsonl", "evidence/universe_", "goldens/", "tests/test_no_infra_leaks.py")
IPV4 = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{1,3}){3})(?![\w.])")
SECRET_LINE = re.compile(r"^\s*(TWS_PASSWORD|VNC_SERVER_PASSWORD|TEMPO_SMTP_PASSWORD|SEC_USER_AGENT)\s*=[ \t]*[^\s#]+", re.M)


def is_public(ip) -> bool:
    return ip.is_global


def tracked_text_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    for rel in out:
        p = ROOT / rel
        if p.suffix in TEXT and not rel.startswith(SKIP) and p.is_file() and p.stat().st_size < 2_000_000:
            yield rel, p.read_text(encoding="utf-8", errors="replace")


def test_no_public_ip_address_is_committed():
    leaks = []
    for rel, text in tracked_text_files():
        for m in IPV4.finditer(text):
            try:
                ip = ipaddress.ip_address(m.group(1))
            except ValueError:
                continue
            if is_public(ip):
                leaks.append(f"{rel}: {m.group(1)}")
    assert not leaks, f"public IP address(es) in a tracked file: {leaks}"


def test_no_secret_or_private_key_is_committed():
    leaks = []
    for rel, text in tracked_text_files():
        if "PRIVATE KEY-----" in text:
            leaks.append(f"{rel}: private key block")
        if not rel.endswith((".md", ".py", ".example")) and SECRET_LINE.search(text):
            leaks.append(f"{rel}: secret with a value")
    assert not leaks, leaks


def test_real_secret_files_are_git_ignored():
    for name in (".env", "deploy/gateway.env"):
        r = subprocess.run(["git", "check-ignore", "-q", name], cwd=ROOT)
        assert r.returncode == 0, f"{name} must be in .gitignore"


def test_the_detectors_do_catch_a_leak():
    """The guard must not be a green rubber stamp: feed it known-bad text."""
    assert IPV4.search("ssh ubuntu@8.8.8.8") and is_public(ipaddress.ip_address("8.8.8.8"))
    assert not is_public(ipaddress.ip_address("127.0.0.1")) and not is_public(ipaddress.ip_address("192.168.1.5"))
    assert SECRET_LINE.search("TWS_PASSWORD=hunter2\n")
    assert not SECRET_LINE.search("TWS_PASSWORD=\nVNC_SERVER_PASSWORD=\n")  # empty placeholders are fine
