from homologacao_ponto.infrastructure.sigrh_browser import SigrhBrowser


class FakePage:
    def __init__(self, title: str, html: str) -> None:
        self._title = title
        self._html = html

    def title(self) -> str:
        return self._title

    def content(self) -> str:
        return self._html


def test_destination_visible_uses_title_heading_or_breadcrumb() -> None:
    browser = SigrhBrowser()
    browser._page = FakePage("SIGRH", "<h1>Espelho do Ponto</h1>")

    assert browser.destination_visible("Espelho do Ponto")


def test_destination_visible_rejects_generic_ponto_text() -> None:
    browser = SigrhBrowser()
    browser._page = FakePage("Relatório", "<p>ponto eletrônico</p>")

    assert not browser.destination_visible("Espelho do Ponto")


def test_label_variants_include_accented_sigrh_labels() -> None:
    assert "Homologação de Ponto Eletrônico" in SigrhBrowser._label_variants("Homologacao de Ponto Eletronico")
    assert "Relatório" in SigrhBrowser._label_variants("Relatorio")
    assert "Relatórios" in SigrhBrowser._label_variants("Relatorio")
    assert "Espelho de Ponto" in SigrhBrowser._label_variants("Espelho do Ponto")


def test_destination_visible_accepts_real_espelho_de_ponto_label() -> None:
    browser = SigrhBrowser()
    browser._page = FakePage("SIGRH", "<h1>Espelho de Ponto</h1>")

    assert browser.destination_visible("Espelho do Ponto")
