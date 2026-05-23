from homologacao_ponto import cli
from homologacao_ponto.app import AppResult
from homologacao_ponto.models import ExportacaoEspelhoResult, ExportStatus


class FakeExportApp:
    def __init__(self, result: AppResult) -> None:
        self.result = result

    def run_espelho_ponto(self, servidor: str | None = None, mes: int | None = None, ano: int | None = None, **kwargs):
        assert servidor == "Celio Proliciano Maioli"
        return self.result


def export_result(status: ExportStatus, success: bool = True) -> ExportacaoEspelhoResult:
    return ExportacaoEspelhoResult(
        run_id="run-123",
        started_at="2026-05-20T12:00:00+00:00",
        completed_at="2026-05-20T12:00:01+00:00",
        requested_server="Celio Proliciano Maioli",
        status=status,
        success=success,
        final_step="Espelho Exportado" if success else "Validar Espelho",
        message="ok" if success else "falha",
        export_path="data/runs/espelho-ponto-run-123.json" if success else None,
        output_path="data/runs/export-result-run-123.json",
    )


def test_cli_espelho_export_success(monkeypatch, capsys) -> None:
    app_result = AppResult(
        0,
        "Espelho de Ponto exportado com sucesso. JSON: data/runs/espelho-ponto-run-123.json Resultado: data/runs/export-result-run-123.json",
        export_result(ExportStatus.COMPLETED),
    )
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeExportApp(app_result))

    exit_code = cli.main(["espelho-ponto", "--servidor", "Celio Proliciano Maioli", "--output-dir", "data/runs"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "espelho-ponto-run-123.json" in captured.out
    assert "export-result-run-123.json" in captured.out


def test_cli_espelho_export_failure_uses_stderr(monkeypatch, capsys) -> None:
    app_result = AppResult(4, "pagina invalida. Resultado: data/runs/export-result-run-123.json", export_result(ExportStatus.FAILED, False))
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeExportApp(app_result))

    exit_code = cli.main(["espelho-ponto", "--servidor", "Celio Proliciano Maioli", "--output-dir", "data/runs"])

    captured = capsys.readouterr()
    assert exit_code == 4
    assert "pagina invalida" in captured.err
