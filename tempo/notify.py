"""Alerts that reach you away from the PC: email (free, Gmail SMTP with an app password) plus a popup on Windows.

Set in .env (never committed):
    TEMPO_SMTP_USER=you@gmail.com
    TEMPO_SMTP_PASSWORD=<16-character Gmail app password, not your normal password>
    TEMPO_ALERT_TO=you@gmail.com          (optional; defaults to TEMPO_SMTP_USER)
Neither path ever raises: an alert that cannot be delivered is written to the log instead.
"""
from __future__ import annotations

import os
import smtplib
import ssl
import subprocess
from email.message import EmailMessage
from pathlib import Path
from typing import Callable, Mapping

ROOT = Path(__file__).resolve().parent.parent
POPUP_SECONDS = 7200


def send_email(title: str, text: str, env: Mapping[str, str] | None = None, smtp=smtplib.SMTP_SSL) -> bool:
    if env is None:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
        env = os.environ
    user, password = env.get("TEMPO_SMTP_USER"), env.get("TEMPO_SMTP_PASSWORD")
    if not (user and password):
        return False
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = user, env.get("TEMPO_ALERT_TO") or user, title
    msg.set_content(text)
    try:
        with smtp(env.get("TEMPO_SMTP_HOST", "smtp.gmail.com"), int(env.get("TEMPO_SMTP_PORT", "465")), timeout=30,
                  context=ssl.create_default_context()) as server:   # verify the server certificate (not the default on 3.11)
            server.login(user, password)
            server.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException):
        return False


def popup(title: str, text: str) -> None:
    if os.name != "nt":
        return
    try:
        subprocess.run(["msg", os.environ.get("USERNAME", "*"), f"/TIME:{POPUP_SECONDS}", f"{title}\n\n{text}"[:900]],
                       capture_output=True, timeout=30, check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        pass


def notify(title: str, text: str, email: Callable[[str, str], bool] = send_email, popup: Callable[[str, str], None] = popup,
           log: Callable[[str], None] = print) -> None:
    if not email(title, text):
        log(f"alert email not sent (TEMPO_SMTP_* missing in .env, or the mail server refused): {title}")
    popup(title, text)
