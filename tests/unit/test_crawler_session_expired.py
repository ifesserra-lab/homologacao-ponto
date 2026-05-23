from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import BrowserSession, CrawlStatus
from homologacao_ponto.services.crawler_service import CrawlerService
from fixtures.sigrh_pages import SESSION_EXPIRED_HTML


class FakeBrowser:
    @staticmethod
    def is_session_expired(html):
        return "expirada" in html.lower()

    @staticmethod
    def is_anti_automation(html):
        return False


def test_crawler_session_expiration_produces_partial_result() -> None:
    snapshot = SigrhPageSnapshot(
        "https://sigrh.ifes.edu.br/sigrh/frequencia/espelho.jsf",
        "Ponto",
        SESSION_EXPIRED_HTML,
        "2026-05-20T12:00:00+00:00",
    )

    result = CrawlerService(FakeBrowser()).crawl_snapshots(
        BrowserSession().authenticated("ctx"), "paulo", [snapshot]
    )

    assert result.status == CrawlStatus.PARTIAL
    assert "expirada" in result.message
