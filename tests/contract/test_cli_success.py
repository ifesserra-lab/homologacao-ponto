from homologacao_ponto import cli
from homologacao_ponto.models import CrawlResult


class FakeApp:
    def run(self):
        from homologacao_ponto.app import AppResult

        return AppResult(
            0,
            "Login realizado com sucesso. 1 páginas visitadas, 0 registros coletados. JSON: out.json",
            CrawlResult("paulo", 1, message="nenhum registro encontrado"),
        )


def test_cli_success_exit_code_and_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeApp())

    exit_code = cli.main(["crawl", "--output-dir", "out"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Login realizado com sucesso" in captured.out

