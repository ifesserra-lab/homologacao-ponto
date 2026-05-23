from homologacao_ponto.app import HomologacaoPontoApp
from homologacao_ponto.infrastructure.sigrh_browser import SigrhLoginResult
from homologacao_ponto.models import BrowserSession, BrowserSessionState, Credential, CrawlResult


class Provider:
    def load(self):
        return Credential("paulo", "secret")


class Browser:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class Auth:
    def login(self, credential):
        return SigrhLoginResult(
            True,
            BrowserSessionState.AUTHENTICATED,
            "ok",
            browser_session=BrowserSession().authenticated("ctx"),
        )


class Crawler:
    def crawl(self, session, request):
        return CrawlResult("paulo", 1, message="nenhum registro encontrado")


class Writer:
    def write(self, result):
        return result.with_output_path(__import__("pathlib").Path("out.json"))


def test_context_closes_after_success() -> None:
    browser = Browser()
    app = HomologacaoPontoApp(Provider(), browser, Auth(), Crawler(), Writer())

    result = app.run()

    assert result.exit_code == 0
    assert browser.closed

