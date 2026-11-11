import pytest

from tempo.config import load_config
from tempo.ibkr import assert_paper


def test_defaults_target_gateway_paper_readonly():
    cfg = load_config({})
    assert (cfg.host, cfg.port, cfg.readonly) == ("127.0.0.1", 4002, True)


def test_overrides():
    cfg = load_config({"IBKR_PORT": "7497", "IBKR_READONLY": "0", "IBKR_CLIENT_ID": "5"})
    assert (cfg.port, cfg.readonly, cfg.client_id) == (7497, False, 5)


def test_bad_port_fails_loudly():
    with pytest.raises(ValueError, match="IBKR_"):
        load_config({"IBKR_PORT": "abc"})


@pytest.mark.parametrize("account", ["DU1234567", "DF7654321"])
def test_paper_accounts_pass(account):
    assert_paper(account)


@pytest.mark.parametrize("account", ["U1234567", "", "I9999999"])
def test_live_accounts_refused(account):
    with pytest.raises(RuntimeError, match="not a paper account"):
        assert_paper(account)


def test_account_pin_is_read_and_blank_means_unset():
    assert load_config({"IBKR_ACCOUNT": " DU1234567 "}).account == "DU1234567"
    assert load_config({"IBKR_ACCOUNT": ""}).account is None
    assert load_config({}).account is None
