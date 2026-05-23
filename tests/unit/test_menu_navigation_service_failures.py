from homologacao_ponto.infrastructure.sigrh_browser import MenuNavigationError
from homologacao_ponto.models import BrowserSession, NavigationStatus, NavigationStepStatus
from homologacao_ponto.services.menu_navigation_service import MenuNavigationRequest, MenuNavigationService


class NoWaitRateLimiter:
    def wait_before_action(self) -> None:
        return None


class MissingBrowser:
    def __init__(self, missing_label: str) -> None:
        self.missing_label = missing_label

    def click_menu_label(self, label: str, timeout_seconds: int):
        if label == self.missing_label:
            raise MenuNavigationError(label, NavigationStepStatus.MISSING, f"menu não encontrado: {label}")
        return type("Snapshot", (), {"html": "<html></html>"})()

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return False

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return False

    @staticmethod
    def destination_visible(label: str) -> bool:
        return True


def test_missing_chefe_menu_reports_failed_stage() -> None:
    result = MenuNavigationService(MissingBrowser("Chefia de Unidade"), rate_limiter=NoWaitRateLimiter()).navigate_to_espelho(
        BrowserSession().authenticated("ctx"), MenuNavigationRequest("paulo")
    )

    assert result.status == NavigationStatus.FAILED
    assert result.final_step == "Chefia de Unidade"
    assert "Chefia de Unidade" in result.message


def test_missing_homologacao_menu_reports_failed_stage() -> None:
    result = MenuNavigationService(MissingBrowser("Homologacao de Ponto Eletronico"), rate_limiter=NoWaitRateLimiter()).navigate_to_espelho(
        BrowserSession().authenticated("ctx"), MenuNavigationRequest("paulo")
    )

    assert result.status == NavigationStatus.FAILED
    assert result.final_step == "Homologacao de Ponto Eletronico"
