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


def test_route_mocked_attendance_crawl() -> None:
    snapshot = SigrhPageSnapshot(
        "https://sigrh.ifes.edu.br/sigrh/frequencia/espelho.jsf",
        "Ponto",
        ATTENDANCE_HTML,
        "2026-05-20T12:00:00+00:00",
    )

    result = CrawlerService(FakeBrowser()).crawl_snapshots(
        BrowserSession().authenticated("ctx"), "paulo", [snapshot]
    )

    assert result.status == CrawlStatus.COMPLETED
    assert result.record_count == 1
