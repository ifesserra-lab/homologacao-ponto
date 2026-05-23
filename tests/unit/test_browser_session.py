import pytest

from homologacao_ponto.models import BrowserSession, BrowserSessionState


def test_browser_session_authenticates_and_requires_authenticated_state() -> None:
    session = BrowserSession().authenticated("ctx-1", "https://sigrh.ifes.edu.br/home")

    assert session.state == BrowserSessionState.AUTHENTICATED
    assert session.context_id == "ctx-1"
    session.require_authenticated()


def test_browser_session_terminal_states() -> None:
    failed = BrowserSession().failed("invalid credentials")
    blocked = BrowserSession().blocked("captcha")
    expired = BrowserSession().authenticated("ctx-1").expired("session expired")

    assert failed.is_terminal
    assert blocked.is_terminal
    assert expired.is_terminal


def test_crawl_requires_authenticated_session() -> None:
    with pytest.raises(ValueError):
        BrowserSession().require_authenticated()

