from tempo.notify import notify, send_email

ENV = {"TEMPO_SMTP_USER": "me@example.com", "TEMPO_SMTP_PASSWORD": "app-pass", "TEMPO_ALERT_TO": "alerts@example.com"}


class FakeSMTP:
    sent = []

    def __init__(self, host, port, timeout):
        self.host, self.port = host, port

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def login(self, user, password):
        self.user = user

    def send_message(self, msg):
        FakeSMTP.sent.append((self.host, self.port, self.user, msg["To"], msg["Subject"], msg.get_content()))


def test_an_email_goes_out_through_the_configured_account():
    FakeSMTP.sent = []
    assert send_email("Tempo entries FAILED", "P&L unreadable", env=ENV, smtp=FakeSMTP) is True
    (host, port, user, to, subject, body) = FakeSMTP.sent[0]
    assert (host, port, user, to, subject) == ("smtp.gmail.com", 465, "me@example.com", "alerts@example.com", "Tempo entries FAILED")
    assert "P&L unreadable" in body


def test_without_credentials_nothing_is_sent_and_it_says_so():
    assert send_email("t", "x", env={}, smtp=FakeSMTP) is False


def test_a_broken_mail_server_never_raises():
    class Boom(FakeSMTP):
        def login(self, user, password):
            raise OSError("refused")

    assert send_email("t", "x", env=ENV, smtp=Boom) is False


def test_notify_tries_email_and_popup_and_logs_what_failed():
    logs, popups = [], []
    notify("T", "body", email=lambda t, x: False, popup=lambda t, x: popups.append(t), log=logs.append)
    assert popups == ["T"] and any("email not sent" in line for line in logs)
    logs.clear()
    notify("T", "body", email=lambda t, x: True, popup=lambda t, x: None, log=logs.append)
    assert logs == []
