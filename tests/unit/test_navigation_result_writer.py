import json

import pytest

from homologacao_ponto.models import NavigationResult, NavigationStatus, NavigationStep, NavigationStepStatus
from homologacao_ponto.services.result_writer import ResultWriteError, ResultWriter


def test_result_writer_writes_navigation_json(tmp_path) -> None:
    result = NavigationResult(
        username_ref="paulo",
        status=NavigationStatus.COMPLETED,
        final_step="Espelho do Ponto",
        steps=[NavigationStep("Espelho do Ponto", 4, NavigationStepStatus.CLICKED)],
    )

    persisted = ResultWriter(tmp_path).write(result)
    data = json.loads((tmp_path / persisted.output_filename).read_text(encoding="utf-8"))

    assert data["status"] == "completed"
    assert data["success"] is True
    assert data["output_path"] == str(tmp_path / persisted.output_filename)


def test_result_writer_reports_navigation_write_failure(tmp_path) -> None:
    output_dir = tmp_path / "not-a-dir"
    output_dir.write_text("blocked", encoding="utf-8")
    result = NavigationResult(
        username_ref="paulo",
        status=NavigationStatus.COMPLETED,
        final_step="Espelho do Ponto",
        steps=[NavigationStep("Espelho do Ponto", 4, NavigationStepStatus.CLICKED)],
    )

    with pytest.raises(ResultWriteError):
        ResultWriter(output_dir).write(result)
