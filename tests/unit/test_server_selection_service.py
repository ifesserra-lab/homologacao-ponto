from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import BrowserSession, SelectionStatus, ServidorResultado
from homologacao_ponto.services.server_selection_service import ServerSelectionRequest, ServerSelectionService


class NoWaitRateLimiter:
    def __init__(self) -> None:
        self.calls = 0

    def wait_before_action(self) -> None:
        self.calls += 1


class SuccessfulSelectionBrowser:
    def __init__(self) -> None:
        self.selected: ServidorResultado | None = None
        self.reference_month: int | None = None
        self.reference_year: int | None = None

    def search_server_results(
        self,
        server_name: str,
        timeout_seconds: int = 15,
        reference_month: int | None = None,
        reference_year: int | None = None,
        **kwargs,
    ):
        self.reference_month = reference_month
        self.reference_year = reference_year
        return SigrhPageSnapshot("url", "Espelho", "<html></html>", "2026-05-20T12:00:00+00:00")

    def find_server_results(self, server_name: str):
        return [ServidorResultado("CELIO PROLICIANO MAIOLI", "1534589", "1534589 CELIO PROLICIANO MAIOLI", True)]

    def select_server_result(self, result: ServidorResultado, timeout_seconds: int = 15):
        self.selected = result
        return SigrhPageSnapshot("url", "Ponto", "<h1>PONTO DIÁRIO DO SERVIDOR: CELIO PROLICIANO MAIOLI</h1>", "2026-05-20T12:00:00+00:00")

    @staticmethod
    def selected_server_visible(server_name: str, identifier: str | None = None) -> bool:
        return True

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return False

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return False


def test_server_selection_service_selects_unique_result_and_completes() -> None:
    browser = SuccessfulSelectionBrowser()
    limiter = NoWaitRateLimiter()

    result = ServerSelectionService(browser, rate_limiter=limiter).select_server(
        BrowserSession().authenticated("ctx"),
        ServerSelectionRequest(username_ref="paulo", requested_server="Celio Proliciano Maioli"),
    )

    assert result.status == SelectionStatus.COMPLETED
    assert result.selected_server == "CELIO PROLICIANO MAIOLI"
    assert browser.selected is not None
    assert limiter.calls == 2


def test_server_selection_service_passes_reference_period_to_browser() -> None:
    browser = SuccessfulSelectionBrowser()

    result = ServerSelectionService(browser, rate_limiter=NoWaitRateLimiter()).select_server(
        BrowserSession().authenticated("ctx"),
        ServerSelectionRequest(
            username_ref="paulo",
            requested_server="Celio Proliciano Maioli",
            reference_month=12,
            reference_year=2025,
        ),
    )

    assert result.status == SelectionStatus.COMPLETED
    assert browser.reference_month == 12
    assert browser.reference_year == 2025
