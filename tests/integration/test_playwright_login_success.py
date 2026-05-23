from homologacao_ponto.infrastructure.sigrh_browser import SigrhBrowser
from homologacao_ponto.models import BrowserSessionState
from fixtures.sigrh_pages import LOGIN_SUCCESS_HTML


def test_route_mocked_login_success_detection() -> None:
    result = SigrhBrowser().detect_login_result(
        LOGIN_SUCCESS_HTML, "https://sigrh.ifes.edu.br/sigrh/home.jsf"
    )

    assert result.success
    assert result.state == BrowserSessionState.AUTHENTICATED
