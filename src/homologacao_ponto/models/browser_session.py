from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum


class BrowserSessionState(StrEnum):
    ANONYMOUS = "anonymous"
    AUTHENTICATED = "authenticated"
    FAILED = "failed"
    BLOCKED = "blocked"
    EXPIRED = "expired"


@dataclass(frozen=True)
class BrowserSession:
    state: BrowserSessionState = BrowserSessionState.ANONYMOUS
    context_id: str | None = None
    current_url: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_navigation_at: datetime | None = None
    failure_reason: str | None = None
    closed: bool = False

    def require_authenticated(self) -> None:
        if self.state != BrowserSessionState.AUTHENTICATED:
            raise ValueError("crawling requires an authenticated BrowserSession")

    @property
    def is_terminal(self) -> bool:
        return self.state in {
            BrowserSessionState.FAILED,
            BrowserSessionState.BLOCKED,
            BrowserSessionState.EXPIRED,
        }

    def authenticated(
        self, context_id: str, current_url: str | None = None
    ) -> BrowserSession:
        if self.state != BrowserSessionState.ANONYMOUS:
            raise ValueError("only an anonymous session can authenticate")
        return replace(
            self,
            state=BrowserSessionState.AUTHENTICATED,
            context_id=context_id,
            current_url=current_url,
        )

    def failed(self, reason: str) -> BrowserSession:
        return replace(self, state=BrowserSessionState.FAILED, failure_reason=reason)

    def blocked(self, reason: str) -> BrowserSession:
        return replace(self, state=BrowserSessionState.BLOCKED, failure_reason=reason)

    def expired(self, reason: str) -> BrowserSession:
        if self.state != BrowserSessionState.AUTHENTICATED:
            raise ValueError("only authenticated sessions can expire during crawl")
        return replace(self, state=BrowserSessionState.EXPIRED, failure_reason=reason)

    def navigated(self, url: str, at: datetime | None = None) -> BrowserSession:
        return replace(
            self,
            current_url=url,
            last_navigation_at=at or datetime.now(timezone.utc),
        )

    def close(self) -> BrowserSession:
        return replace(self, closed=True)
