from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass(frozen=True)
class CrawlScope:
    allowed_paths: tuple[str, ...] = field(
        default_factory=lambda: (
            "/sigrh/frequencia",
            "/sigrh/ponto",
            "/sigrh/portal/servidor/frequencia",
        )
    )
    max_pages: int = 20
    min_navigation_interval_seconds: int = 2
    host: str = "sigrh.ifes.edu.br"

    def __post_init__(self) -> None:
        if self.max_pages != 20:
            raise ValueError("max_pages is fixed at 20 for this feature")
        if self.min_navigation_interval_seconds != 2:
            raise ValueError("minimum navigation interval is fixed at 2 seconds")

    def allows(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        if parsed.netloc != self.host:
            return False
        normalized_path = parsed.path.lower()
        return any(normalized_path.startswith(path) for path in self.allowed_paths)

    def assert_allows(self, url: str) -> None:
        if not self.allows(url):
            raise ValueError(f"out-of-scope SIGRH URL rejected: {url}")
