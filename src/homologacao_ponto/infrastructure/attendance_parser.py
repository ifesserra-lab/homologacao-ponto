from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser

from homologacao_ponto.models import AttendanceRecord
from homologacao_ponto.models.crawl_scope import CrawlScope


@dataclass(frozen=True)
class SigrhPageSnapshot:
    url: str
    title: str | None
    html: str
    captured_at: str


class _AttendanceHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, list[str] | str]] = []
        self._current: dict[str, list[str] | str] | None = None
        self._capture_class: str | None = None
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = set((attrs_dict.get("class") or "").split())
        if tag == "tr" and "registro-ponto" in classes:
            self._current = {
                "point_date": attrs_dict.get("data-date") or "",
                "entry_times": [],
                "exit_times": [],
            }
        if self._current is not None and tag in {"td", "span"}:
            if "data" in classes:
                self._capture_class = "point_date"
            elif "entrada" in classes:
                self._capture_class = "entry_times"
            elif "saida" in classes:
                self._capture_class = "exit_times"
            if self._capture_class:
                self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._capture_class:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._current is not None and self._capture_class and tag in {"td", "span"}:
            value = " ".join(part.strip() for part in self._buffer if part.strip())
            if value:
                if self._capture_class == "point_date":
                    self._current["point_date"] = value
                else:
                    self._current[self._capture_class].append(value)  # type: ignore[index]
            self._capture_class = None
            self._buffer = []
        if tag == "tr" and self._current is not None:
            self.rows.append(self._current)
            self._current = None


class AttendanceParser:
    TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b")

    def __init__(self, scope: CrawlScope | None = None) -> None:
        self.scope = scope or CrawlScope()

    def parse(self, snapshot: SigrhPageSnapshot) -> list[AttendanceRecord]:
        self.scope.assert_allows(snapshot.url)
        parser = _AttendanceHTMLParser()
        parser.feed(snapshot.html)
        collected_at = snapshot.captured_at or datetime.now(timezone.utc).isoformat()
        records: list[AttendanceRecord] = []
        for row in parser.rows:
            point_date = str(row.get("point_date") or "").strip()
            if not point_date:
                continue
            entry_times = [
                t for t in row.get("entry_times", []) if self.TIME_RE.match(t)
            ]  # type: ignore[arg-type]
            exit_times = [t for t in row.get("exit_times", []) if self.TIME_RE.match(t)]  # type: ignore[arg-type]
            try:
                records.append(
                    AttendanceRecord(
                        point_date=point_date,
                        entry_times=entry_times,
                        exit_times=exit_times,
                        source_url=snapshot.url,
                        collected_at=collected_at,
                    )
                )
            except ValueError:
                continue
        return records
