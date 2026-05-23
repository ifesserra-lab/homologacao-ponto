from homologacao_ponto import cli


class FakeApp:
    def run(self):
        from homologacao_ponto.app import AppResult

        return AppResult(5, "arquivo JSON local não pôde ser escrito")


def test_cli_output_write_failure(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeApp())

    exit_code = cli.main(["crawl"])

    assert exit_code == 5
    assert "JSON" in capsys.readouterr().err

