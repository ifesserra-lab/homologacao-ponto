import json

import pytest

from homologacao_ponto.models import NavigationResult, NavigationStatus, NavigationStep, NavigationStepStatus


def _clicked_steps() -> list[NavigationStep]:
    return [
        NavigationStep("Chefia de Unidade", 1, NavigationStepStatus.CLICKED),
        NavigationStep("Homologacao de Ponto Eletronico", 2, NavigationStepStatus.CLICKED),
        NavigationStep("Relatorio", 3, NavigationStepStatus.CLICKED),
        NavigationStep("Espelho do Ponto", 4, NavigationStepStatus.CLICKED),
    ]


def test_completed_navigation_result_serializes_success() -> None:
    result = NavigationResult(username_ref="paulo", status=NavigationStatus.COMPLETED, final_step="Espelho do Ponto", steps=_clicked_steps())

    data = result.to_dict()

    assert data["success"] is True
    assert data["status"] == "completed"
    assert data["final_step"] == "Espelho do Ponto"
    assert result.output_filename.startswith("navigation-result-")


def test_failed_partial_and_blocked_require_message() -> None:
    step = NavigationStep("Chefia de Unidade", 1, NavigationStepStatus.MISSING, "menu não encontrado")

    for status in (NavigationStatus.FAILED, NavigationStatus.PARTIAL, NavigationStatus.BLOCKED):
        with pytest.raises(ValueError):
            NavigationResult(username_ref="paulo", status=status, final_step="Chefia de Unidade", steps=[step])


def test_navigation_result_excludes_sensitive_values() -> None:
    result = NavigationResult(
        username_ref="paulo",
        status=NavigationStatus.FAILED,
        final_step="Chefia de Unidade",
        steps=[NavigationStep("Chefia de Unidade", 1, NavigationStepStatus.MISSING, "menu não encontrado")],
        message="menu não encontrado",
    )

    rendered = json.dumps(result.to_dict()).lower()

    assert "password" not in rendered
    assert "cookie" not in rendered
    assert "html" not in rendered
