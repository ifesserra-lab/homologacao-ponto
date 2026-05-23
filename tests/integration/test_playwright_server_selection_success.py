from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import BrowserSession, SelectionStatus, ServidorResultado
from homologacao_ponto.services.server_selection_service import ServerSelectionRequest, ServerSelectionService
from fixtures.sigrh_server_selection_pages import SELECTED_SERVER_PAGE_HTML


class NoWaitRateLimiter:
    def wait_before_action(self) -> None:
        return None


class RouteMockedSelectionBrowser:
    def __init__(self) -> None:
        self.selected = False

    def search_server_results(self, server_name: str, timeout_seconds: int = 15, **kwargs):
        return SigrhPageSnapshot("url", "Espelho", "<html></html>", "2026-05-20T12:00:00+00:00")

    def find_server_results(self, server_name: str):
        return [ServidorResultado("CELIO PROLICIANO MAIOLI", "1534589", "1534589 CELIO PROLICIANO MAIOLI", True)]

    def select_server_result(self, result: ServidorResultado, timeout_seconds: int = 15):
        self.selected = True
        return SigrhPageSnapshot("url", "Ponto", SELECTED_SERVER_PAGE_HTML, "2026-05-20T12:00:00+00:00")

    @staticmethod
    def selected_server_visible(server_name: str, identifier: str | None = None) -> bool:
        return True

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return False

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return False


def test_route_mocked_server_selection_success() -> None:
    browser = RouteMockedSelectionBrowser()

    result = ServerSelectionService(browser, rate_limiter=NoWaitRateLimiter()).select_server(
        BrowserSession().authenticated("ctx"),
        ServerSelectionRequest("paulo", "Celio Proliciano Maioli"),
    )

    assert result.status == SelectionStatus.COMPLETED
    assert browser.selected is True
