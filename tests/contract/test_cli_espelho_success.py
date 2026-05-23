from homologacao_ponto import cli
from homologacao_ponto.models import NavigationResult, NavigationStatus, NavigationStep, NavigationStepStatus


class FakeApp:
    def run_espelho_ponto(self, **kwargs):
        from homologacao_ponto.app import AppResult

        result = NavigationResult(
            "paulo",
            NavigationStatus.COMPLETED,
            "Espelho do Ponto",
            [NavigationStep("Espelho do Ponto", 4, NavigationStepStatus.CLICKED)],
            output_path="out/navigation-result-run.json",
        )
        return AppResult(0, "Login realizado com sucesso. Navegação concluída até Espelho do Ponto. JSON: out/navigation-result-run.json", result)


def test_cli_espelho_success_exit_code_and_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeApp())

    exit_code = cli.main(["espelho-ponto", "--output-dir", "out"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Espelho do Ponto" in captured.out
    assert "navigation-result" in captured.out
