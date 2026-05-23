from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import BrowserSession, NavigationStatus
from homologacao_ponto.services.menu_navigation_service import MenuNavigationRequest, MenuNavigationService
from fixtures.sigrh_navigation_pages import ESPELHO_DESTINATION_HTML


class NoWaitRateLimiter:
    def wait_before_action(self) -> None:
        return None


class RouteMockedBrowser:
    def __init__(self) -> None:
        self.clicked: list[str] = []
        self.html = ESPELHO_DESTINATION_HTML

    def click_menu_label(self, label: str, timeout_seconds: int):
        self.clicked.append(label)
        return SigrhPageSnapshot("https://sigrh.ifes.edu.br/sigrh/ponto/espelho", "Espelho do Ponto", self.html, "2026-05-20T12:00:00+00:00")

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return False

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return False

    def destination_visible(self, label: str) -> bool:
        return label in self.html


def test_route_mocked_espelho_navigation_success() -> None:
    browser = RouteMockedBrowser()

    result = MenuNavigationService(browser, rate_limiter=NoWaitRateLimiter()).navigate_to_espelho(
        BrowserSession().authenticated("ctx"), MenuNavigationRequest("paulo")
    )

    assert result.status == NavigationStatus.COMPLETED
    assert browser.clicked[-1] == "Espelho do Ponto"
