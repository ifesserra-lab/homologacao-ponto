from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import BrowserSession, CrawlStatus
from homologacao_ponto.services.crawler_service import CrawlerService
from fixtures.sigrh_pages import ANTI_AUTOMATION_HTML


class FakeBrowser:
    @staticmethod
    def is_session_expired(html):
        return False

    @staticmethod
    def is_anti_automation(html):
        return "captcha" in html.lower()


def test_anti_automation_abort() -> None:
    snapshot = SigrhPageSnapshot(
        "https://sigrh.ifes.edu.br/sigrh/frequencia/espelho.jsf",
        "Ponto",
        ANTI_AUTOMATION_HTML,
        "2026-05-20T12:00:00+00:00",
    )

    result = CrawlerService(FakeBrowser()).crawl_snapshots(
        BrowserSession().authenticated("ctx"), "paulo", [snapshot]
    )

    assert result.status == CrawlStatus.BLOCKED
    assert result.record_count == 0
