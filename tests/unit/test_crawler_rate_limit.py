from homologacao_ponto.infrastructure.rate_limiter import RateLimiter
from homologacao_ponto.models import BrowserSession
from homologacao_ponto.services.crawler_service import CrawlRequest, CrawlerService
from fixtures.clock import FakeClock
from fixtures.sigrh_pages import EMPTY_ATTENDANCE_HTML


class FakeBrowser:
    @staticmethod
    def is_session_expired(html):
        return False

    @staticmethod
    def is_anti_automation(html):
        return False

    def goto(self, url):
        from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot

        return SigrhPageSnapshot(url, "Ponto", EMPTY_ATTENDANCE_HTML, "2026-05-20T12:00:00+00:00")


def test_crawler_uses_rate_limiter_before_navigation() -> None:
    clock = FakeClock()
    limiter = RateLimiter(clock=clock.now, sleeper=clock.sleep)
    service = CrawlerService(FakeBrowser(), rate_limiter=limiter)

    service.crawl(
        BrowserSession().authenticated("ctx"),
        CrawlRequest(
            "paulo",
            [
                "https://sigrh.ifes.edu.br/sigrh/frequencia/1",
                "https://sigrh.ifes.edu.br/sigrh/frequencia/2",
            ],
        ),
    )

    assert clock.sleeps == [2.0]
