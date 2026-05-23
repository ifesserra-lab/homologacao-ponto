from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import BrowserSession, CrawlStatus
from homologacao_ponto.services.crawler_service import CrawlerService
from fixtures.sigrh_pages import ATTENDANCE_HTML


class FakeBrowser:
    @staticmethod
    def is_session_expired(html):
        return False

    @staticmethod
    def is_anti_automation(html):
        return False


def test_crawler_page_cap_returns_partial_result() -> None:
    snapshots = [
        SigrhPageSnapshot(
            "https://sigrh.ifes.edu.br/sigrh/frequencia/espelho.jsf",
            "Ponto",
            ATTENDANCE_HTML,
            "2026-05-20T12:00:00+00:00",
        )
        for _ in range(21)
    ]

    result = CrawlerService(FakeBrowser()).crawl_snapshots(
        BrowserSession().authenticated("ctx"), "paulo", snapshots
    )

    assert result.status == CrawlStatus.PARTIAL
    assert result.visited_page_count == 20
    assert "limite" in result.message
