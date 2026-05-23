from homologacao_ponto import cli


class FakeApp:
    def __init__(self, exit_code: int, message: str) -> None:
        self.exit_code = exit_code
        self.message = message

    def run_espelho_ponto(self, servidor: str | None = None, **kwargs):
        from homologacao_ponto.app import AppResult

        return AppResult(self.exit_code, self.message)


def test_cli_server_selection_prints_json_output_path(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeApp(0, "Servidor selecionado. JSON: out/selection-result-run.json"))

    assert cli.main(["espelho-ponto", "--servidor", "Celio Proliciano Maioli"]) == 0
    assert "selection-result-run.json" in capsys.readouterr().out


def test_cli_server_selection_write_failure_exit_code(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeApp(5, "arquivo JSON local não pôde ser escrito"))

    assert cli.main(["espelho-ponto", "--servidor", "Celio Proliciano Maioli"]) == 5
    assert "arquivo JSON local" in capsys.readouterr().err
