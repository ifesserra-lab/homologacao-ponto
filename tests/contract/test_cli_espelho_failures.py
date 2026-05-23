import pytest

from homologacao_ponto import cli


class FakeApp:
    def __init__(self, exit_code: int, message: str) -> None:
        self.exit_code = exit_code
        self.message = message

    def run_espelho_ponto(self, **kwargs):
        from homologacao_ponto.app import AppResult

        return AppResult(self.exit_code, self.message)


@pytest.mark.parametrize(
    ("exit_code", "message"),
    [
        (3, "proteção anti-automação impede a automação"),
        (4, "menu não encontrado: Chefia de Unidade"),
        (6, "BrowserSession expirada durante a navegação"),
    ],
)
def test_cli_espelho_failure_exit_codes(monkeypatch, capsys, exit_code: int, message: str) -> None:
    monkeypatch.setattr(cli, "create_app", lambda **kwargs: FakeApp(exit_code, message))

    assert cli.main(["espelho-ponto"]) == exit_code
    assert message in capsys.readouterr().err
