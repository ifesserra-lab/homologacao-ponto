from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum


class NavigationStepStatus(StrEnum):
    PENDING = "pending"
    FOUND = "found"
    HOVERED = "hovered"
    CLICKED = "clicked"
    MISSING = "missing"
    TIMED_OUT = "timed_out"
    BLOCKED = "blocked"
    EXPIRED = "expired"
    DESTINATION_MISMATCH = "destination_mismatch"


_FAILURE_STATUSES = {
    NavigationStepStatus.MISSING,
    NavigationStepStatus.TIMED_OUT,
    NavigationStepStatus.BLOCKED,
    NavigationStepStatus.EXPIRED,
    NavigationStepStatus.DESTINATION_MISMATCH,
}


@dataclass(frozen=True)
class NavigationStep:
    label: str
    position: int
    status: NavigationStepStatus = NavigationStepStatus.PENDING
    message: str | None = None
    completed_at: str | None = None

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("label is required")
        if self.position < 1:
            raise ValueError("position must be positive")
        if self.status in _FAILURE_STATUSES and not self.message:
            raise ValueError("terminal failure steps require a message")

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["status"] = self.status.value
        if data.get("message") is None:
            data.pop("message", None)
        if data.get("completed_at") is None:
            data.pop("completed_at", None)
        return data
