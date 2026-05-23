import pytest

from homologacao_ponto.models import ExportacaoEspelhoResult, ExportStatus, ServidorSelecionado


def test_export_result_success_requires_export_path() -> None:
    with pytest.raises(ValueError):
        ExportacaoEspelhoResult(
            run_id="run-123",
            started_at="2026-05-20T12:00:00+00:00",
            completed_at="2026-05-20T12:00:01+00:00",
            requested_server="Celio Proliciano Maioli",
            status=ExportStatus.COMPLETED,
            success=True,
            final_step="Espelho Exportado",
            message="ok",
        )


def test_export_result_serializes_success() -> None:
    result = ExportacaoEspelhoResult(
        run_id="run-123",
        started_at="2026-05-20T12:00:00+00:00",
        completed_at="2026-05-20T12:00:01+00:00",
        requested_server="Celio Proliciano Maioli",
        status=ExportStatus.COMPLETED,
        success=True,
        final_step="Espelho Exportado",
        message="ok",
        selected_server=ServidorSelecionado("CELIO PROLICIANO MAIOLI", "1534589"),
        periodo_referencia="Maio/2026",
        export_path="data/runs/espelho-ponto-run-123.json",
    )

    data = result.to_dict()

    assert data["success"] is True
    assert data["status"] == "completed"
    assert data["selected_server"]["identificador"] == "1534589"
