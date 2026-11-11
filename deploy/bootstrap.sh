#!/usr/bin/env bash
# One-time setup of a fresh Ubuntu 24.04 VPS for Tempo. Run as root:  bash bootstrap.sh git@github.com:OWNER/Tempo.git
# Idempotent: safe to run again. It does NOT copy secrets or state; docs/vps.md says what to copy and how.
set -euo pipefail
REPO="${1:?usage: bash bootstrap.sh <git clone URL>}"
DIR=/opt/tempo

timedatectl set-timezone America/New_York                    # cron times in deploy/crontab are ET
apt-get update -y
apt-get install -y git python3 python3-venv docker.io docker-compose-v2 ufw
systemctl enable --now docker

ufw allow OpenSSH
ufw --force enable                                          # only SSH is reachable; the Gateway API binds to localhost

if [ ! -d "$DIR/.git" ]; then
  git clone "$REPO" "$DIR"
fi
cd "$DIR"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

git config user.name  "tempo-vps"
git config user.email "tempo-vps@localhost"

echo
echo "Next (docs/vps.md): copy .env, deploy/gateway.env, journal/, state.json and data/ from the PC,"
echo "then: docker compose -f deploy/docker-compose.yml up -d ; crontab deploy/crontab"
