from homologacao_ponto.models import BrowserSession, NavigationStatus
from homologacao_ponto.services.menu_navigation_service import MenuNavigationRequest, MenuNavigationService


class NoWaitRateLimiter:
    def wait_before_action(self) -> None:
        return None


class SnapshotBrowser:
    def __init__(self, html: str) -> None:
        self.html = html

    def click_menu_label(self, label: str, timeout_seconds: int):
        return type("Snapshot", (), {"html": self.html})()

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return "captcha" in html.lower()

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return "sessão expirada" in html.lower()


def test_session_expiration_returns_partial_without_reauth() -> None:
    result = MenuNavigationService(SnapshotBrowser("<h1>Sessão expirada</h1>"), rate_limiter=NoWaitRateLimiter()).navigate_to_espelho(
        BrowserSession().authenticated("ctx"), MenuNavigationRequest("paulo")
    )

    assert result.status == NavigationStatus.PARTIAL
    assert "expirada" in result.message


def test_anti_automation_returns_blocked() -> None:
    result = MenuNavigationService(SnapshotBrowser("<h1>captcha</h1>"), rate_limiter=NoWaitRateLimiter()).navigate_to_espelho(
        BrowserSession().authenticated("ctx"), MenuNavigationRequest("paulo")
    )

    assert result.status == NavigationStatus.BLOCKED
    assert "anti-automação" in result.message
