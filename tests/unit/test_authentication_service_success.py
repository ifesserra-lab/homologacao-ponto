from homologacao_ponto.infrastructure.sigrh_browser import SigrhLoginResult
from homologacao_ponto.models import BrowserSession, BrowserSessionState, Credential
from homologacao_ponto.services.authentication_service import AuthenticationService


class FakeBrowser:
    def login(self, credential):
        session = BrowserSession().authenticated("ctx-1", "https://sigrh.ifes.edu.br/home")
        return SigrhLoginResult(True, BrowserSessionState.AUTHENTICATED, "ok", browser_session=session)


def test_authentication_service_maps_success() -> None:
    result = AuthenticationService(FakeBrowser()).login(Credential("paulo", "secret"))

    assert result.success
    assert result.state == BrowserSessionState.AUTHENTICATED

