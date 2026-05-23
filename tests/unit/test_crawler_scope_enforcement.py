import pytest

from homologacao_ponto.models import BrowserSession
from homologacao_ponto.services.crawler_service import CrawlRequest, CrawlerService, ScopePolicyError


class FakeBrowser:
    @staticmethod
    def is_session_expired(html):
        return False

    @staticmethod
    def is_anti_automation(html):
        return False

    def goto(self, url):
        raise AssertionError("out-of-scope URL should not be visited")


def test_crawler_rejects_out_of_scope_before_navigation() -> None:
    service = CrawlerService(FakeBrowser())
    session = BrowserSession().authenticated("ctx")

    with pytest.raises(ScopePolicyError):
        service.crawl(session, CrawlRequest("paulo", ["https://sigrh.ifes.edu.br/sigrh/relatorios"]))

