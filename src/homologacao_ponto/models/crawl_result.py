from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from homologacao_ponto.models.attendance_record import AttendanceRecord


class CrawlStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class CrawlResult:
    username_ref: str
    visited_page_count: int
    records: list[AttendanceRecord] = field(default_factory=list)
    status: CrawlStatus = CrawlStatus.COMPLETED
    message: str | None = None
    run_id: str = field(default_factory=lambda: uuid4().hex)
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    output_path: str | None = None

    def __post_init__(self) -> None:
        if not self.username_ref:
            raise ValueError("username_ref is required")
        if self.visited_page_count < 0 or self.visited_page_count > 20:
            raise ValueError("visited_page_count must be between 0 and 20")
        if self.status == CrawlStatus.PARTIAL and not self.message:
            raise ValueError("partial results require a message")
        if self.status == CrawlStatus.BLOCKED and not self.message:
            raise ValueError("blocked results require a message")
        if (
            self.status == CrawlStatus.COMPLETED
            and len(self.records) == 0
            and not self.message
        ):
            raise ValueError("empty completed results require a no-records message")

    @property
    def record_count(self) -> int:
        return len(self.records)

    @property
    def output_filename(self) -> str:
        return f"crawl-result-{self.run_id}.json"

    def with_output_path(self, output_path: Path) -> CrawlResult:
        return CrawlResult(
            username_ref=self.username_ref,
            visited_page_count=self.visited_page_count,
            records=self.records,
            status=self.status,
            message=self.message,
            run_id=self.run_id,
            collected_at=self.collected_at,
            output_path=str(output_path),
        )

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["status"] = self.status.value
        data["record_count"] = self.record_count
        data["records"] = [record.to_dict() for record in self.records]
        if data.get("output_path") is None:
            data.pop("output_path", None)
        return data
