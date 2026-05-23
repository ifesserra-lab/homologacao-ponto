from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import BrowserSession, NavigationStatus
from homologacao_ponto.services.menu_navigation_service import MenuNavigationRequest, MenuNavigationService


class NoWaitRateLimiter:
    def __init__(self) -> None:
        self.calls = 0

    def wait_before_action(self) -> None:
        self.calls += 1


class SuccessfulBrowser:
    def __init__(self) -> None:
        self.clicked: list[str] = []

    def click_menu_label(self, label: str, timeout_seconds: int):
        self.clicked.append(label)
        return SigrhPageSnapshot("https://sigrh.ifes.edu.br/sigrh/menu", "SIGRH", "<html></html>", "2026-05-20T12:00:00+00:00")

    def hover_menu_label(self, label: str, timeout_seconds: int):
        self.clicked.append(label)
        return SigrhPageSnapshot("https://sigrh.ifes.edu.br/sigrh/menu", "SIGRH", "<html></html>", "2026-05-20T12:00:00+00:00")

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return False

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return False

    @staticmethod
    def destination_visible(label: str) -> bool:
        return label == "Espelho do Ponto"


def test_menu_navigation_service_clicks_canonical_path_and_completes() -> None:
    browser = SuccessfulBrowser()
    limiter = NoWaitRateLimiter()

    result = MenuNavigationService(browser, rate_limiter=limiter).navigate_to_espelho(
        BrowserSession().authenticated("ctx"),
        MenuNavigationRequest(username_ref="paulo"),
    )

    assert browser.clicked == [
        "Chefia de Unidade",
        "Homologacao de Ponto Eletronico",
        "Relatorio",
        "Espelho do Ponto",
    ]
    assert limiter.calls == 1
    assert result.status == NavigationStatus.COMPLETED
    assert result.final_step == "Espelho do Ponto"
    assert [step.status.value for step in result.steps] == ["hovered", "hovered", "hovered", "clicked"]
