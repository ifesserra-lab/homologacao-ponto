from __future__ import annotations

import logging
from dataclasses import dataclass

from homologacao_ponto.infrastructure.attendance_parser import AttendanceParser, SigrhPageSnapshot
from homologacao_ponto.infrastructure.rate_limiter import RateLimiter
from homologacao_ponto.infrastructure.sigrh_browser import SigrhBrowser
from homologacao_ponto.models import BrowserSession, CrawlResult, CrawlScope, CrawlStatus


class ScopePolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class CrawlRequest:
    username_ref: str
    start_urls: list[str]


class CrawlerService:
    def __init__(
        self,
        browser: SigrhBrowser,
        parser: AttendanceParser | None = None,
        scope: CrawlScope | None = None,
        rate_limiter: RateLimiter | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.browser = browser
        self.scope = scope or CrawlScope()
        self.parser = parser or AttendanceParser(self.scope)
        self.rate_limiter = rate_limiter or RateLimiter(self.scope.min_navigation_interval_seconds)
        self.logger = logger or logging.getLogger("homologacao_ponto")

    def crawl(self, session: BrowserSession, request: CrawlRequest) -> CrawlResult:
        session.require_authenticated()
        records = []
        visited = 0
        for url in request.start_urls:
            if visited >= self.scope.max_pages:
                return CrawlResult(
                    username_ref=request.username_ref,
                    visited_page_count=visited,
                    records=records,
                    status=CrawlStatus.PARTIAL,
                    message="limite de páginas atingido",
                )
            if not self.scope.allows(url):
                self.logger.warning("rejected out-of-scope URL: %s", url)
                raise ScopePolicyError(f"out-of-scope URL: {url}")
            self.rate_limiter.wait_before_action()
            snapshot = self.browser.goto(url)
            visited += 1
            if self.browser.is_anti_automation(snapshot.html):
                return CrawlResult(
                    username_ref=request.username_ref,
                    visited_page_count=visited,
                    records=records,
                    status=CrawlStatus.BLOCKED,
                    message="proteção anti-automação impede a automação",
                )
            if self.browser.is_session_expired(snapshot.html):
                return CrawlResult(
                    username_ref=request.username_ref,
                    visited_page_count=visited,
                    records=records,
                    status=CrawlStatus.PARTIAL,
                    message="BrowserSession expirada durante o crawl",
                )
            records.extend(self.parser.parse(snapshot))
        if not records:
            return CrawlResult(
                username_ref=request.username_ref,
                visited_page_count=visited,
                records=[],
                status=CrawlStatus.COMPLETED,
                message="nenhum registro encontrado",
            )
        return CrawlResult(
            username_ref=request.username_ref,
            visited_page_count=visited,
            records=records,
            status=CrawlStatus.COMPLETED,
        )

    def crawl_snapshots(self, session: BrowserSession, username_ref: str, snapshots: list[SigrhPageSnapshot]) -> CrawlResult:
        session.require_authenticated()
        records = []
        for index, snapshot in enumerate(snapshots[: self.scope.max_pages], start=1):
            if not self.scope.allows(snapshot.url):
                raise ScopePolicyError(f"out-of-scope URL: {snapshot.url}")
            if self.browser.is_session_expired(snapshot.html):
                return CrawlResult(username_ref, index, records, CrawlStatus.PARTIAL, "BrowserSession expirada durante o crawl")
            if self.browser.is_anti_automation(snapshot.html):
                return CrawlResult(username_ref, index, records, CrawlStatus.BLOCKED, "proteção anti-automação impede a automação")
            records.extend(self.parser.parse(snapshot))
        if len(snapshots) > self.scope.max_pages:
            return CrawlResult(username_ref, self.scope.max_pages, records, CrawlStatus.PARTIAL, "limite de páginas atingido")
        if not records:
            return CrawlResult(username_ref, len(snapshots), [], CrawlStatus.COMPLETED, "nenhum registro encontrado")
        return CrawlResult(username_ref, len(snapshots), records)

