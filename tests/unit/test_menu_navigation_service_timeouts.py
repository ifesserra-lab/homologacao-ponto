from homologacao_ponto.infrastructure.sigrh_browser import MenuNavigationError
from homologacao_ponto.models import BrowserSession, NavigationStatus, NavigationStepStatus
from homologacao_ponto.services.menu_navigation_service import MenuNavigationRequest, MenuNavigationService


class NoWaitRateLimiter:
    def wait_before_action(self) -> None:
        return None


class TimeoutBrowser:
    def click_menu_label(self, label: str, timeout_seconds: int):
        raise MenuNavigationError(label, NavigationStepStatus.TIMED_OUT, f"menu não encontrado em até {timeout_seconds} segundos: {label}")

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return False

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return False


class DestinationMismatchBrowser:
    def click_menu_label(self, label: str, timeout_seconds: int):
        return type("Snapshot", (), {"html": "<html></html>"})()

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return False

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return False

    @staticmethod
    def destination_visible(label: str) -> bool:
        return False


def test_step_timeout_fails_with_stage_message() -> None:
    result = MenuNavigationService(TimeoutBrowser(), rate_limiter=NoWaitRateLimiter()).navigate_to_espelho(
        BrowserSession().authenticated("ctx"), MenuNavigationRequest("paulo")
    )

    assert result.status == NavigationStatus.FAILED
    assert "15 segundos" in result.message


def test_destination_mismatch_fails_after_clicks() -> None:
    result = MenuNavigationService(DestinationMismatchBrowser(), rate_limiter=NoWaitRateLimiter()).navigate_to_espelho(
        BrowserSession().authenticated("ctx"), MenuNavigationRequest("paulo")
    )

    assert result.status == NavigationStatus.FAILED
    assert result.steps[-1].status == NavigationStepStatus.DESTINATION_MISMATCH
