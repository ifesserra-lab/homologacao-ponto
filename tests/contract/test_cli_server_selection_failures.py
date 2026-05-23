import pytest

from homologacao_ponto import cli


class FakeApp:
    def __init__(self, exit_code: int, message: str) -> None:
        self.exit_code = exit_code
        self.message = message

    def run_espelho_ponto(self, servidor: str | None = None, **kwargs):
        from homologacao_ponto.app import AppResult

        assert servidor == "Celio Proliciano Maioli"
        return AppResult(self.exit_code, self.message)


@pytest.mark.parametrize(
    ("exit_code", "message"),
    [
        (3, "proteção anti-automação impede a automação"),
        (4, "servidor não encontrado: Celio Proliciano Maioli"),
        (6, "BrowserSession expirada durante a seleção do servidor"),
    ],
)
def test_cli_server_selection_failure_exit_codes(monkeypatch, capsys, exit_code: int, message: str) -> None:
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeApp(exit_code, message))

    assert cli.main(["espelho-ponto", "--servidor", "Celio Proliciano Maioli"]) == exit_code
    assert message in capsys.readouterr().err
