from homologacao_ponto.app import HomologacaoPontoApp
from homologacao_ponto.infrastructure.sigrh_browser import SigrhLoginResult
from homologacao_ponto.models import BrowserSessionState, Credential


class Provider:
    def load(self):
        return Credential("paulo", "bad")


class Browser:
    closed = False

    def close(self):
        self.closed = True


class Auth:
    def login(self, credential):
        return SigrhLoginResult(False, BrowserSessionState.FAILED, "Credenciais invalidas.")


class Crawler:
    def crawl(self, *args, **kwargs):
        raise AssertionError("crawler must not run")


class Writer:
    def write(self, result):
        raise AssertionError("writer must not run")


def test_app_stops_before_crawl_after_failed_authentication() -> None:
    browser = Browser()
    app = HomologacaoPontoApp(Provider(), browser, Auth(), Crawler(), Writer())

    result = app.run()

    assert result.exit_code == 2
    assert browser.closed

