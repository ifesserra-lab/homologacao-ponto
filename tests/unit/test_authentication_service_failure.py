from homologacao_ponto.infrastructure.sigrh_browser import SigrhLoginResult
from homologacao_ponto.models import BrowserSessionState, Credential
from homologacao_ponto.services.authentication_service import AuthenticationService


class FakeBrowser:
    def login(self, credential):
        return SigrhLoginResult(False, BrowserSessionState.FAILED, "Credenciais invalidas.")


def test_authentication_service_maps_failure() -> None:
    result = AuthenticationService(FakeBrowser()).login(Credential("paulo", "bad"))

    assert not result.success
    assert result.state == BrowserSessionState.FAILED
    assert "invalid" in result.message.lower()

