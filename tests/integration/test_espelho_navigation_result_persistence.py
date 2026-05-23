import json

from homologacao_ponto.models import NavigationResult, NavigationStatus, NavigationStep, NavigationStepStatus
from homologacao_ponto.services.result_writer import ResultWriter


def test_success_and_missing_menu_results_persist_json(tmp_path) -> None:
    writer = ResultWriter(tmp_path)
    success = writer.write(
        NavigationResult(
            "paulo",
            NavigationStatus.COMPLETED,
            "Espelho do Ponto",
            [NavigationStep("Espelho do Ponto", 4, NavigationStepStatus.CLICKED)],
        )
    )
    failed = writer.write(
        NavigationResult(
            "paulo",
            NavigationStatus.FAILED,
            "Chefia de Unidade",
            [NavigationStep("Chefia de Unidade", 1, NavigationStepStatus.MISSING, "menu não encontrado")],
            "menu não encontrado",
        )
    )

    success_data = json.loads((tmp_path / success.output_filename).read_text(encoding="utf-8"))
    failed_data = json.loads((tmp_path / failed.output_filename).read_text(encoding="utf-8"))

    assert success_data["status"] == "completed"
    assert failed_data["status"] == "failed"
    assert failed_data["message"] == "menu não encontrado"
