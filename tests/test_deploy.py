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
    assert all(re.match(r"^(\d+ \d+ \* \* (1-5|\*)|\*/10 \* \* \* \*) cd /opt/tempo && ", ln) for ln in lines), lines


def test_the_watchdog_runs_every_ten_minutes_all_week():
    text = (ROOT / "deploy/crontab").read_text(encoding="utf-8")
    assert "*/10 * * * * cd /opt/tempo && .venv/bin/python -m tempo.watchdog >> logs/watchdog.log 2>&1" in text


def test_gateway_image_is_pinned_and_ports_are_localhost_only():
    compose = (ROOT / "deploy/docker-compose.yml").read_text(encoding="utf-8")
    image = re.search(r"image:\s*(\S+)", compose).group(1)
    assert re.search(r":\d+\.\d+\.\d+\w*$", image), image          # an exact version, never latest/stable
    ports = re.findall(r'-\s*"([^"]+)"', compose)
    assert ports and all(p.startswith("127.0.0.1:") for p in ports)
    assert "TRADING_MODE: paper" in compose


def test_gateway_credentials_file_is_never_committed():
    assert "deploy/gateway.env" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_files_run_on_linux_have_unix_line_endings():
    for name in ("deploy/bootstrap.sh", "deploy/crontab"):
        assert b"\r\n" not in (ROOT / name).read_bytes(), name


def test_gateway_gets_a_full_login_every_night_after_the_ibkr_reset_and_the_watchdog_maintenance_window():
    """IBC's 23:59 autorestart resumes a stored session token; the second resume in a row after one full login is refused
    ('Unrecognized Username or Password', seen 2026-11-13 and 2026-11-14). A daily container restart does a full login
    (about 5 s, no 2FA on paper) so the token chain never gets that long."""
    from tempo.watchdog import MAINTENANCE_END
    lines = [ln for ln in (ROOT / "deploy/crontab").read_text(encoding="utf-8").splitlines() if "docker compose" in ln and "restart" in ln]
    assert len(lines) == 1, lines
    m = re.match(r"^(\d+) (\d+) \* \* \* cd /opt/tempo && sudo -n docker compose -f deploy/docker-compose\.yml restart >> logs/gateway_restart\.log 2>&1$", lines[0])
    assert m, lines[0]
    minute, hour = int(m.group(1)), int(m.group(2))
    assert (hour, minute) > (MAINTENANCE_END.hour, MAINTENANCE_END.minute + 20)   # IBKR's reset ends about 00:45 ET
    assert hour < 3                                                               # still a night, far from the 06:30 morning job
