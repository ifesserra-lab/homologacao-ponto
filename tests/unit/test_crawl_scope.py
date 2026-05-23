import pytest

from homologacao_ponto.models import CrawlScope


def test_crawl_scope_allows_only_sigrh_attendance_paths() -> None:
    scope = CrawlScope()

    assert scope.allows("https://sigrh.ifes.edu.br/sigrh/frequencia/espelho.jsf")
    assert not scope.allows("https://sigrh.ifes.edu.br/sigrh/relatorios/admin.jsf")
    assert not scope.allows("https://example.org/sigrh/frequencia/espelho.jsf")


def test_crawl_scope_fixed_limits() -> None:
    scope = CrawlScope()

    assert scope.max_pages == 20
    assert scope.min_navigation_interval_seconds == 2
    with pytest.raises(ValueError):
        CrawlScope(max_pages=10)

