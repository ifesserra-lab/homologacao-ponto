from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class AttendanceRecord:
    point_date: str
    entry_times: list[str] = field(default_factory=list)
    exit_times: list[str] = field(default_factory=list)
    source_url: str = ""
    collected_at: str = ""

    def __post_init__(self) -> None:
        if not self.point_date:
            raise ValueError("point_date is required")
        if not self.source_url:
            raise ValueError("source_url is required")
        if not self.collected_at:
            raise ValueError("collected_at is required")

    @classmethod
    def from_values(
        cls,
        point_date: str,
        entry_times: list[str],
        exit_times: list[str],
        source_url: str,
        collected_at: datetime,
    ) -> AttendanceRecord:
        return cls(
            point_date=point_date,
            entry_times=entry_times,
            exit_times=exit_times,
            source_url=source_url,
            collected_at=collected_at.isoformat(),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

