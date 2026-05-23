from homologacao_ponto import cli


class FakeApp:
    def __init__(self, exit_code: int, message: str) -> None:
        self.exit_code = exit_code
        self.message = message

    def run_espelho_ponto(self, **kwargs):
        from homologacao_ponto.app import AppResult

        return AppResult(self.exit_code, self.message)


def test_cli_espelho_prints_json_path_for_handled_failure(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeApp(4, "menu não encontrado. JSON: out/navigation-result-run.json"))

    assert cli.main(["espelho-ponto"]) == 4
    assert "navigation-result-run.json" in capsys.readouterr().err


def test_cli_espelho_write_failure_exit_code(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeApp(5, "arquivo JSON local não pôde ser escrito"))

    assert cli.main(["espelho-ponto"]) == 5
    assert "não pôde ser escrito" in capsys.readouterr().err
