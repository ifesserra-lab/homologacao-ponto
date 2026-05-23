import json

from homologacao_ponto.models import CrawlResult, ExportacaoEspelhoResult, ExportStatus
from homologacao_ponto.services.result_writer import ResultWriter


def test_result_writer_writes_json(tmp_path) -> None:
    result = CrawlResult(
        username_ref="paulo",
        visited_page_count=1,
        message="nenhum registro encontrado",
    )

    persisted = ResultWriter(tmp_path).write(result)

    output = json.loads((tmp_path / persisted.output_filename).read_text(encoding="utf-8"))
    assert output["record_count"] == 0
    assert output["username_ref"] == "paulo"
    assert "password" not in json.dumps(output).lower()


def test_result_writer_writes_export_result_json(tmp_path) -> None:
    result = ExportacaoEspelhoResult(
        run_id="run-123",
        started_at="2026-05-20T12:00:00+00:00",
        completed_at="2026-05-20T12:00:01+00:00",
        requested_server="Celio Proliciano Maioli",
        status=ExportStatus.COMPLETED,
        success=True,
        final_step="Espelho Exportado",
        message="ok",
        export_path="data/runs/espelho-ponto-run-123.json",
    )

    persisted = ResultWriter(tmp_path).write(result)

    output = json.loads((tmp_path / "logging" / "export-result-run-123.json").read_text(encoding="utf-8"))
    assert persisted.output_path.endswith("logging/export-result-run-123.json")
    assert output["export_path"] == "data/runs/espelho-ponto-run-123.json"
    assert output["status"] == "completed"
