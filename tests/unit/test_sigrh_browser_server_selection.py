from homologacao_ponto.infrastructure.sigrh_browser import SigrhBrowser
from fixtures.sigrh_server_selection_pages import SELECTED_SERVER_PAGE_HTML, UNIQUE_SERVER_RESULT_HTML


class FakeLocator:
    def __init__(self, text: str = "", count: int = 1) -> None:
        self._text = text
        self._count = count
        self.clicked = False
        self.first = self

    def count(self) -> int:
        return self._count

    def inner_text(self) -> str:
        return self._text

    def locator(self, selector: str):
        if "Selecionar" in selector or "title" in selector:
            return FakeLocator("Selecionar", 1)
        return FakeLocator("", 0)

    def click(self, **kwargs) -> None:
        self.clicked = True

    def select_option(self, value: str) -> None:
        self._text = value

    def fill(self, value: str) -> None:
        self._text = value


class FakePage:
    def __init__(self, html: str) -> None:
        self._html = html
        self.clicked = False
        self.url = "https://sigrh.ifes.edu.br/sigrh/frequencia/ponto_eletronico/consulta/consulta_ponto_eletronico.jsf"

    def title(self) -> str:
        return "SIGRH"

    def content(self) -> str:
        return self._html

    def locator(self, selector: str):
        if selector == "table.listagem tr":
            return FakeRows()
        return FakeLocator("", 0)


class FakeRows:
    def count(self) -> int:
        return 1

    def nth(self, index: int):
        return FakeLocator("1534589 CELIO PROLICIANO MAIOLI Selecionar")


def test_find_server_results_extracts_row_and_selection_availability() -> None:
    browser = SigrhBrowser()
    browser._page = FakePage(UNIQUE_SERVER_RESULT_HTML)

    results = browser.find_server_results("Celio Proliciano Maioli")

    assert len(results) == 1
    assert results[0].display_name == "CELIO PROLICIANO MAIOLI"
    assert results[0].identifier == "1534589"
    assert results[0].selection_available is True


def test_selected_server_visible_uses_name_or_identifier() -> None:
    browser = SigrhBrowser()
    browser._page = FakePage(SELECTED_SERVER_PAGE_HTML)

    assert browser.selected_server_visible("Celio Proliciano Maioli", "1534589")


class PeriodFakePage(FakePage):
    def __init__(self, html: str) -> None:
        super().__init__(html)
        self.month = FakeLocator()
        self.year = FakeLocator()
        self.check = FakeLocator()
        self.name = FakeLocator()
        self.search = FakeLocator()

    def locator(self, selector: str):
        if selector in {"#form\\:mes", "select[name='form:mes']"}:
            return self.month
        if selector in {"#form\\:ano", "input[name='form:ano']"}:
            return self.year
        if selector in {"#form\\:checkServidor", "input[name='form:checkServidor']"}:
            return self.check
        if selector in {"#form\\:nomeServidor", "input[name='form:nomeServidor']", "input[title='Servidor']"}:
            return self.name
        if selector in {"#form\\:buscarServidores", "input[name='form:buscarServidores']", "input[value='Buscar']"}:
            return self.search
        return FakeLocator("", 0)

    def wait_for_timeout(self, timeout: int) -> None:
        return None


def test_search_server_results_sets_reference_period_before_search() -> None:
    browser = SigrhBrowser()
    page = PeriodFakePage(UNIQUE_SERVER_RESULT_HTML)
    browser._page = page

    browser.search_server_results("Celio Proliciano Maioli", reference_month=12, reference_year=2025)

    assert page.month._text == "12"
    assert page.year._text == "2025"
    assert page.search.clicked is True
