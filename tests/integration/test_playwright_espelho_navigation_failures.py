import pytest

from homologacao_ponto.infrastructure.sigrh_browser import MenuNavigationError
from homologacao_ponto.models import BrowserSession, NavigationStatus, NavigationStepStatus
from homologacao_ponto.services.menu_navigation_service import MenuNavigationRequest, MenuNavigationService
from fixtures.sigrh_navigation_pages import BLOCKED_HTML, DESTINATION_MISMATCH_HTML, SESSION_EXPIRED_HTML


class NoWaitRateLimiter:
    def wait_before_action(self) -> None:
        return None


class FailureBrowser:
    def __init__(self, mode: str) -> None:
        self.mode = mode

    def click_menu_label(self, label: str, timeout_seconds: int):
        if self.mode == "missing":
            raise MenuNavigationError(label, NavigationStepStatus.MISSING, f"menu não encontrado: {label}")
        html = {
            "expired": SESSION_EXPIRED_HTML,
            "blocked": BLOCKED_HTML,
            "mismatch": DESTINATION_MISMATCH_HTML,
        }[self.mode]
        return type("Snapshot", (), {"html": html})()

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return "captcha" in html.lower()

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return "sessão expirada" in html.lower()

    @staticmethod
    def destination_visible(label: str) -> bool:
        return False


@pytest.mark.parametrize(
    ("mode", "expected_status"),
    [
        ("missing", NavigationStatus.FAILED),
        ("expired", NavigationStatus.PARTIAL),
        ("blocked", NavigationStatus.BLOCKED),
        ("mismatch", NavigationStatus.FAILED),
    ],
)
def test_route_mocked_espelho_navigation_failures(mode: str, expected_status: NavigationStatus) -> None:
    result = MenuNavigationService(FailureBrowser(mode), rate_limiter=NoWaitRateLimiter()).navigate_to_espelho(
        BrowserSession().authenticated("ctx"), MenuNavigationRequest("paulo")
    )

    assert result.status == expected_status
    assert result.message
