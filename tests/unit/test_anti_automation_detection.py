from homologacao_ponto.infrastructure.sigrh_browser import SigrhBrowser


def test_detects_anti_automation_signals() -> None:
    assert SigrhBrowser.is_anti_automation("<p>CAPTCHA obrigatorio</p>")
    assert SigrhBrowser.is_anti_automation("<p>MFA requerido</p>")
    assert not SigrhBrowser.is_anti_automation("<p>Portal do servidor</p>")

