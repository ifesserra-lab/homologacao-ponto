import pytest

from homologacao_ponto.models import NavigationStep, NavigationStepStatus


def test_navigation_step_accepts_clicked_status() -> None:
    step = NavigationStep("Chefia de Unidade", 1, NavigationStepStatus.CLICKED)

    assert step.label == "Chefia de Unidade"
    assert step.status == NavigationStepStatus.CLICKED


def test_terminal_failure_status_requires_message() -> None:
    with pytest.raises(ValueError):
        NavigationStep("Chefia de Unidade", 1, NavigationStepStatus.MISSING)

    step = NavigationStep("Chefia de Unidade", 1, NavigationStepStatus.MISSING, "menu não encontrado")

    assert step.message == "menu não encontrado"
