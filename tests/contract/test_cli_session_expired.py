from homologacao_ponto import cli


class FakeApp:
    def run(self):
        from homologacao_ponto.app import AppResult
        from homologacao_ponto.models import CrawlResult, CrawlStatus

        return AppResult(
            6,
            "BrowserSession expirada durante o crawl",
            CrawlResult("paulo", 1, [], CrawlStatus.PARTIAL, "BrowserSession expirada"),
        )


def test_cli_session_expired_exit_code(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeApp())

    exit_code = cli.main(["crawl"])

    assert exit_code == 6
    assert "expirada" in capsys.readouterr().err

