from homologacao_ponto import cli


class FakeApp:
    def run(self):
        from homologacao_ponto.app import AppResult

        return AppResult(2, "Credenciais invalidas.")


def test_cli_auth_failure_exit_code(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeApp())

    exit_code = cli.main(["crawl"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Credenciais" in captured.err

