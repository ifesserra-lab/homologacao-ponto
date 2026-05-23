import pytest

from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import BrowserSession, SelectionStatus, ServidorResultado
from homologacao_ponto.services.server_selection_service import ServerSelectionRequest, ServerSelectionService


class NoWaitRateLimiter:
    def wait_before_action(self) -> None:
        return None


class FailureSelectionBrowser:
    def __init__(self, results, visible: bool = False) -> None:
        self.results = results
        self.visible = visible
        self.clicked = False

    def search_server_results(self, server_name: str, timeout_seconds: int = 15, **kwargs):
        return SigrhPageSnapshot("url", "Espelho", "<html></html>", "2026-05-20T12:00:00+00:00")

    def find_server_results(self, server_name: str):
        return self.results

    def select_server_result(self, result: ServidorResultado, timeout_seconds: int = 15):
        self.clicked = True
        return SigrhPageSnapshot("url", "Ponto", "<h1>Outro servidor</h1>", "2026-05-20T12:00:00+00:00")

    def selected_server_visible(self, server_name: str, identifier: str | None = None) -> bool:
        return self.visible

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return False

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return False


@pytest.mark.parametrize(
    ("results", "message_fragment"),
    [
        ([], "servidor não encontrado"),
        (
            [
                ServidorResultado("CELIO PROLICIANO MAIOLI", "1534589", "1534589 CELIO PROLICIANO MAIOLI", True),
                ServidorResultado("CELIO PROLICIANO SILVA", "9999999", "9999999 CELIO PROLICIANO SILVA", True),
            ],
            "resultado ambíguo",
        ),
        ([ServidorResultado("CELIO PROLICIANO MAIOLI", "1534589", "1534589 CELIO PROLICIANO MAIOLI", False)], "seleção não disponível"),
    ],
)
def test_server_selection_service_reports_pre_click_failures(results, message_fragment: str) -> None:
    browser = FailureSelectionBrowser(results)

    result = ServerSelectionService(browser, rate_limiter=NoWaitRateLimiter()).select_server(
        BrowserSession().authenticated("ctx"),
        ServerSelectionRequest(username_ref="paulo", requested_server="Celio Proliciano"),
    )

    assert result.status == SelectionStatus.FAILED
    assert message_fragment in (result.message or "")
    assert browser.clicked is False


def test_server_selection_service_reports_destination_mismatch() -> None:
    browser = FailureSelectionBrowser(
        [ServidorResultado("CELIO PROLICIANO MAIOLI", "1534589", "1534589 CELIO PROLICIANO MAIOLI", True)]
    )

    result = ServerSelectionService(browser, rate_limiter=NoWaitRateLimiter()).select_server(
        BrowserSession().authenticated("ctx"),
        ServerSelectionRequest(username_ref="paulo", requested_server="Celio Proliciano Maioli"),
    )

    assert result.status == SelectionStatus.FAILED
    assert "confirmação visível" in (result.message or "")
