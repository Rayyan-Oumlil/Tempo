"""The SEC client's network-facing code, tested without a network: urllib and the module's own fetch are replaced."""
import io
import json
import urllib.error

import pytest

import tempo.edgar as edgar
from tempo.edgar import EdgarError, earnings_release, fetch


class NoWait:
    def wait(self):
        pass


@pytest.fixture(autouse=True)
def no_dotenv_no_throttle_no_cache(monkeypatch):
    monkeypatch.setattr(edgar, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr(edgar, "_THROTTLE", NoWait())
    edgar._ticker_map.cache_clear()
    yield
    edgar._ticker_map.cache_clear()


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_fetch_sends_the_declared_user_agent_and_returns_the_text(monkeypatch):
    seen = {}

    def fake_urlopen(req, timeout):
        seen["ua"] = req.get_header("User-agent")
        seen["url"] = req.full_url
        seen["timeout"] = timeout
        return Response("héllo".encode("utf-8"))

    monkeypatch.setenv("SEC_USER_AGENT", "Tempo test contact@example.com")
    monkeypatch.setattr(edgar.urllib.request, "urlopen", fake_urlopen)
    assert fetch("https://www.sec.gov/x") == "héllo"
    assert seen == {"ua": "Tempo test contact@example.com", "url": "https://www.sec.gov/x", "timeout": edgar.TIMEOUT}


def test_fetch_refuses_to_run_without_a_contact_string(monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    monkeypatch.setattr(edgar.urllib.request, "urlopen", lambda *a, **k: pytest.fail("must not touch the network without a User-Agent"))
    with pytest.raises(EdgarError, match="SEC_USER_AGENT"):
        fetch("https://www.sec.gov/x")


@pytest.mark.parametrize("error,expected", [
    (urllib.error.HTTPError("u", 403, "Forbidden", {}, None), "HTTP 403"),
    (urllib.error.URLError("no route"), "no route"),
    (TimeoutError("slow"), "slow"),
])
def test_fetch_turns_every_network_failure_into_an_edgar_error_carrying_the_url(monkeypatch, error, expected):
    def boom(req, timeout):
        raise error

    monkeypatch.setenv("SEC_USER_AGENT", "Tempo test contact@example.com")
    monkeypatch.setattr(edgar.urllib.request, "urlopen", boom)
    with pytest.raises(EdgarError) as info:
        fetch("https://www.sec.gov/y")
    assert "https://www.sec.gov/y" in str(info.value) and expected in str(info.value)


TICKERS = json.dumps({"0": {"cik_str": 2488, "ticker": "AMD", "title": "AMD"}})
SUBMISSIONS = json.dumps({"filings": {"recent": {
    "accessionNumber": ["0000002488-26-000099"], "filingDate": ["2026-11-03"], "acceptanceDateTime": ["2026-11-03T21:05:00.000Z"],
    "form": ["8-K"], "items": ["2.02,9.01"], "primaryDocument": ["amd-8k.htm"]}}})
INDEX = """<table><tr><th>Seq</th><th>Description</th><th>Document</th><th>Type</th><th>Size</th></tr>
<tr><td>1</td><td>8-K</td><td><a href="/Archives/edgar/data/2488/000000248826000099/amd-8k.htm">amd-8k.htm</a></td><td>8-K</td><td>1</td></tr>
<tr><td>2</td><td>PRESS</td><td><a href="/Archives/edgar/data/2488/000000248826000099/release.htm">release.htm</a></td><td>EX-99.1</td><td>2</td></tr></table>"""
RELEASE = "<html><body><h1>AMD Reports Third Quarter</h1><p>Revenue $13.4 billion</p></body></html>"


def fake_sec(routes):
    calls = []

    def fetch_fake(url):
        calls.append(url)
        for fragment, body in routes.items():
            if fragment in url:
                return body
        raise EdgarError(url, "HTTP 404")

    return fetch_fake, calls


ROUTES = {"company_tickers.json": TICKERS, "submissions/CIK0000002488.json": SUBMISSIONS,
          "0000002488-26-000099-index.htm": INDEX, "release.htm": RELEASE}


def test_earnings_release_follows_ticker_to_filing_to_exhibit_and_returns_clean_text(monkeypatch):
    fake, calls = fake_sec(ROUTES)
    monkeypatch.setattr(edgar, "fetch", fake)
    rel = earnings_release("amd", "2026-11-03")
    assert rel["url"] == "https://www.sec.gov/Archives/edgar/data/2488/000000248826000099/release.htm"
    assert rel["accepted"] == "2026-11-03T21:05:00.000Z" and "AMD Reports Third Quarter" in rel["text"] and "<" not in rel["text"]
    assert calls[0].endswith("company_tickers.json") and calls[-1].endswith("release.htm")


def test_the_ticker_map_is_downloaded_only_once(monkeypatch):
    fake, calls = fake_sec(ROUTES)
    monkeypatch.setattr(edgar, "fetch", fake)
    earnings_release("AMD", "2026-11-03")
    earnings_release("AMD", "2026-11-03")
    assert sum(c.endswith("company_tickers.json") for c in calls) == 1


def test_no_earnings_filing_on_that_date_gives_none(monkeypatch):
    fake, _ = fake_sec(ROUTES)
    monkeypatch.setattr(edgar, "fetch", fake)
    assert earnings_release("AMD", "2026-11-04") is None


def test_an_unknown_ticker_is_an_error_not_a_silent_none(monkeypatch):
    fake, _ = fake_sec(ROUTES)
    monkeypatch.setattr(edgar, "fetch", fake)
    with pytest.raises(EdgarError, match="not found"):
        earnings_release("NOPE", "2026-11-03")


def test_a_filing_without_a_press_release_exhibit_falls_back_to_the_main_document(monkeypatch):
    routes = {**ROUTES, "0000002488-26-000099-index.htm": "<table><tr><td>1</td><td>8-K</td><td><a href=\"/x/amd-8k.htm\">amd-8k.htm</a></td><td>8-K</td><td>1</td></tr></table>",
              "amd-8k.htm": "<p>cover page only</p>"}
    fake, calls = fake_sec(routes)
    monkeypatch.setattr(edgar, "fetch", fake)
    rel = earnings_release("AMD", "2026-11-03")
    assert rel["url"].endswith("/000000248826000099/amd-8k.htm") and rel["text"] == "cover page only"
