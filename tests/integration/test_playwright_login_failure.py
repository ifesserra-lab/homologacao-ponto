from homologacao_ponto.infrastructure.sigrh_browser import SigrhBrowser
from homologacao_ponto.models import BrowserSessionState
from fixtures.sigrh_pages import LOGIN_FAILURE_HTML


def test_route_mocked_login_failure_detection() -> None:
    result = SigrhBrowser().detect_login_result(
        LOGIN_FAILURE_HTML, "https://sigrh.ifes.edu.br/sigrh/login.jsf"
    )

    assert not result.success
    assert result.state == BrowserSessionState.FAILED
