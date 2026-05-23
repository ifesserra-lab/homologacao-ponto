from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from homologacao_ponto.models.navigation_step import NavigationStep


class NavigationStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class NavigationResult:
    username_ref: str
    status: NavigationStatus
    final_step: str
    steps: list[NavigationStep]
    message: str | None = None
    run_id: str = field(default_factory=lambda: uuid4().hex)
    completed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    output_path: str | None = None

    def __post_init__(self) -> None:
        if not self.username_ref:
            raise ValueError("username_ref is required")
        if not self.final_step:
            raise ValueError("final_step is required")
        if not self.steps:
            raise ValueError("steps are required")
        if (
            self.status == NavigationStatus.COMPLETED
            and self.final_step != "Espelho do Ponto"
        ):
            raise ValueError(
                "completed navigation requires final_step Espelho do Ponto"
            )
        if self.status != NavigationStatus.COMPLETED and not self.message:
            raise ValueError("unsuccessful navigation results require a message")

    @property
    def success(self) -> bool:
        return self.status == NavigationStatus.COMPLETED

    @property
    def output_filename(self) -> str:
        return f"navigation-result-{self.run_id}.json"

    def with_output_path(self, output_path: Path) -> NavigationResult:
        return NavigationResult(
            username_ref=self.username_ref,
            status=self.status,
            final_step=self.final_step,
            steps=self.steps,
            message=self.message,
            run_id=self.run_id,
            completed_at=self.completed_at,
            output_path=str(output_path),
        )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "run_id": self.run_id,
            "completed_at": self.completed_at,
            "username_ref": self.username_ref,
            "status": self.status.value,
            "success": self.success,
            "final_step": self.final_step,
            "steps": [step.to_dict() for step in self.steps],
        }
        if self.message is not None:
            data["message"] = self.message
        if self.output_path is not None:
            data["output_path"] = self.output_path
        return data
