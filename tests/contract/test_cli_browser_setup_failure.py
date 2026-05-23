from homologacao_ponto import cli


class FakeApp:
    def run(self):
        from homologacao_ponto.app import AppResult

        return AppResult(
            7,
            "Playwright browser could not start. Run: python -m playwright install chromium",
        )


def test_cli_browser_setup_failure(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeApp())

    exit_code = cli.main(["crawl"])

    assert exit_code == 7
    assert "playwright" in capsys.readouterr().err.lower()

