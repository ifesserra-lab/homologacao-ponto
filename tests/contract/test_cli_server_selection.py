from homologacao_ponto import cli
from homologacao_ponto.models import SelecaoServidorResult, SelectionStatus


class FakeApp:
    def __init__(self) -> None:
        self.mes = None
        self.ano = None

    def run_espelho_ponto(self, servidor: str | None = None, mes: int | None = None, ano: int | None = None, **kwargs):
        from homologacao_ponto.app import AppResult

        assert servidor == "Celio Proliciano Maioli"
        self.mes = mes
        self.ano = ano
        result = SelecaoServidorResult(
            "paulo",
            "Celio Proliciano Maioli",
            SelectionStatus.COMPLETED,
            "Servidor Selecionado",
            selected_server="CELIO PROLICIANO MAIOLI",
            output_path="out/selection-result-run.json",
        )
        return AppResult(0, "Servidor selecionado: CELIO PROLICIANO MAIOLI. JSON: out/selection-result-run.json", result)


def test_cli_server_selection_success_exit_code_and_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeApp())

    exit_code = cli.main(["espelho-ponto", "--servidor", "Celio Proliciano Maioli", "--output-dir", "out"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Servidor selecionado" in captured.out
    assert "selection-result" in captured.out


def test_cli_server_selection_accepts_month_and_year(monkeypatch, capsys) -> None:
    fake_app = FakeApp()
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: fake_app)

    exit_code = cli.main(
        [
            "espelho-ponto",
            "--servidor",
            "Celio Proliciano Maioli",
            "--mes",
            "12",
            "--ano",
            "2025",
            "--output-dir",
            "out",
        ]
    )

    assert exit_code == 0
    assert fake_app.mes == 12
    assert fake_app.ano == 2025
