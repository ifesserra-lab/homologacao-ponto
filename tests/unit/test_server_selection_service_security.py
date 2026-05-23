from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import BrowserSession, SelectionStatus, ServidorResultado
from homologacao_ponto.services.server_selection_service import ServerSelectionRequest, ServerSelectionService


class NoWaitRateLimiter:
    def wait_before_action(self) -> None:
        return None


class SecuritySelectionBrowser:
    def __init__(self, html: str) -> None:
        self.html = html

    def search_server_results(self, server_name: str, timeout_seconds: int = 15, **kwargs):
        return SigrhPageSnapshot("url", "Espelho", "<html></html>", "2026-05-20T12:00:00+00:00")

    def find_server_results(self, server_name: str):
        return [ServidorResultado("CELIO PROLICIANO MAIOLI", "1534589", "1534589 CELIO PROLICIANO MAIOLI", True)]

    def select_server_result(self, result: ServidorResultado, timeout_seconds: int = 15):
        return SigrhPageSnapshot("url", "Ponto", self.html, "2026-05-20T12:00:00+00:00")

    @staticmethod
    def selected_server_visible(server_name: str, identifier: str | None = None) -> bool:
        return False

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return "captcha" in html.lower()

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return "sessão expirada" in html.lower()


def test_server_selection_service_reports_blocked_selection() -> None:
    result = ServerSelectionService(SecuritySelectionBrowser("CAPTCHA obrigatório"), rate_limiter=NoWaitRateLimiter()).select_server(
        BrowserSession().authenticated("ctx"),
        ServerSelectionRequest(username_ref="paulo", requested_server="Celio Proliciano Maioli"),
    )

    assert result.status == SelectionStatus.BLOCKED


def test_server_selection_service_reports_expired_selection() -> None:
    result = ServerSelectionService(SecuritySelectionBrowser("Sessão expirada"), rate_limiter=NoWaitRateLimiter()).select_server(
        BrowserSession().authenticated("ctx"),
        ServerSelectionRequest(username_ref="paulo", requested_server="Celio Proliciano Maioli"),
    )

    assert result.status == SelectionStatus.PARTIAL
