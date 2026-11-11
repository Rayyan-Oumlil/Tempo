"""The VPS kit must stay consistent with the PC scheduler and never expose the Gateway."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ps1_times():
    out = set()
    for line in (ROOT / "tools/sched/register.ps1").read_text(encoding="utf-8").splitlines():
        m = re.match(r'^Add-Job "[^"]+"\s+"(\w+)"\s+@\(([^)]*)\)(?:\s+"([^"]*)")?\s*$', line.strip())
        if m:
            for hh, mm in re.findall(r'"(\d\d):(\d\d)"', m.group(2)):
                out.add((int(hh), int(mm), f"{m.group(1)} {m.group(3) or ''}".strip()))
    return out


def _cron_times():
    out = set()
    for line in (ROOT / "deploy/crontab").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\d+) (\d+) \* \* 1-5 cd /opt/tempo && \.venv/bin/python -m tempo\.sched (.+)$", line)
        if m:
            out.add((int(m.group(2)), int(m.group(1)), m.group(3).strip()))
    return out


def test_vps_crontab_runs_the_same_jobs_at_the_same_times_as_the_pc():
    assert _cron_times() and _cron_times() == _ps1_times()


def test_every_cron_line_is_a_full_command_not_a_variable():
    lines = [ln for ln in (ROOT / "deploy/crontab").read_text(encoding="utf-8").splitlines() if ln and not ln.startswith("#")]
    assert all(re.match(r"^\d+ \d+ \* \* 1-5 cd /opt/tempo && ", ln) for ln in lines), lines


def test_gateway_image_is_pinned_and_ports_are_localhost_only():
    compose = (ROOT / "deploy/docker-compose.yml").read_text(encoding="utf-8")
    image = re.search(r"image:\s*(\S+)", compose).group(1)
    assert re.search(r":\d+\.\d+\.\d+\w*$", image), image          # an exact version, never latest/stable
    ports = re.findall(r'-\s*"([^"]+)"', compose)
    assert ports and all(p.startswith("127.0.0.1:") for p in ports)
    assert "TRADING_MODE: paper" in compose


def test_gateway_credentials_file_is_never_committed():
    assert "deploy/gateway.env" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
