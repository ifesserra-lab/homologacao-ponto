import pytest

from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import BrowserSession, SelectionStatus, ServidorResultado
from homologacao_ponto.services.server_selection_service import ServerSelectionRequest, ServerSelectionService
from fixtures.sigrh_server_selection_pages import SELECTION_BLOCKED_HTML, SELECTION_DESTINATION_MISMATCH_HTML, SELECTION_SESSION_EXPIRED_HTML


class NoWaitRateLimiter:
    def wait_before_action(self) -> None:
        return None


class FailureBrowser:
    def __init__(self, mode: str) -> None:
        self.mode = mode

    def search_server_results(self, server_name: str, timeout_seconds: int = 15, **kwargs):
        return SigrhPageSnapshot("url", "Espelho", "<html></html>", "2026-05-20T12:00:00+00:00")

    def find_server_results(self, server_name: str):
        if self.mode == "missing":
            return []
        if self.mode == "ambiguous":
            return [
                ServidorResultado("CELIO PROLICIANO MAIOLI", "1534589", "1534589 CELIO PROLICIANO MAIOLI", True),
                ServidorResultado("CELIO PROLICIANO SILVA", "9999999", "9999999 CELIO PROLICIANO SILVA", True),
            ]
        if self.mode == "missing-control":
            return [ServidorResultado("CELIO PROLICIANO MAIOLI", "1534589", "1534589 CELIO PROLICIANO MAIOLI", False)]
        return [ServidorResultado("CELIO PROLICIANO MAIOLI", "1534589", "1534589 CELIO PROLICIANO MAIOLI", True)]

    def select_server_result(self, result: ServidorResultado, timeout_seconds: int = 15):
        html = {
            "expired": SELECTION_SESSION_EXPIRED_HTML,
            "blocked": SELECTION_BLOCKED_HTML,
            "mismatch": SELECTION_DESTINATION_MISMATCH_HTML,
        }.get(self.mode, "<html></html>")
        return SigrhPageSnapshot("url", "Ponto", html, "2026-05-20T12:00:00+00:00")

    @staticmethod
    def selected_server_visible(server_name: str, identifier: str | None = None) -> bool:
        return False

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return "captcha" in html.lower()

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return "sessão expirada" in html.lower()


@pytest.mark.parametrize(
    ("mode", "expected_status"),
    [
        ("missing", SelectionStatus.FAILED),
        ("ambiguous", SelectionStatus.FAILED),
        ("missing-control", SelectionStatus.FAILED),
        ("expired", SelectionStatus.PARTIAL),
        ("blocked", SelectionStatus.BLOCKED),
        ("mismatch", SelectionStatus.FAILED),
    ],
)
def test_route_mocked_server_selection_failures(mode: str, expected_status: SelectionStatus) -> None:
    result = ServerSelectionService(FailureBrowser(mode), rate_limiter=NoWaitRateLimiter()).select_server(
        BrowserSession().authenticated("ctx"),
        ServerSelectionRequest("paulo", "Celio Proliciano"),
    )

    assert result.status == expected_status
    assert result.message
