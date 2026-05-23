from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from uuid import uuid4


class SelectionStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class SelecaoServidorResult:
    username_ref: str
    requested_server: str
    status: SelectionStatus
    final_step: str
    selected_server: str | None = None
    selected_identifier: str | None = None
    message: str | None = None
    run_id: str = field(default_factory=lambda: uuid4().hex)
    completed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    output_path: str | None = None

    def __post_init__(self) -> None:
        if not self.username_ref:
            raise ValueError("username_ref is required")
        if not self.requested_server:
            raise ValueError("requested_server is required")
        if not self.final_step:
            raise ValueError("final_step is required")
        if self.status == SelectionStatus.COMPLETED and not self.selected_server:
            raise ValueError("completed selection requires selected_server")
        if self.status == SelectionStatus.COMPLETED and self.final_step != "Servidor Selecionado":
            raise ValueError("completed selection requires final_step Servidor Selecionado")
        if self.status != SelectionStatus.COMPLETED and not self.message:
            raise ValueError("unsuccessful selection results require a message")

    @property
    def success(self) -> bool:
        return self.status == SelectionStatus.COMPLETED

    @property
    def output_filename(self) -> str:
        return f"selection-result-{self.run_id}.json"

    def with_output_path(self, output_path: Path) -> SelecaoServidorResult:
        return SelecaoServidorResult(
            username_ref=self.username_ref,
            requested_server=self.requested_server,
            status=self.status,
            final_step=self.final_step,
            selected_server=self.selected_server,
            selected_identifier=self.selected_identifier,
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
            "requested_server": self.requested_server,
            "status": self.status.value,
            "success": self.success,
            "final_step": self.final_step,
        }
        if self.selected_server is not None:
            data["selected_server"] = self.selected_server
        if self.selected_identifier is not None:
            data["selected_identifier"] = self.selected_identifier
        if self.message is not None:
            data["message"] = self.message
        if self.output_path is not None:
            data["output_path"] = self.output_path
        return data
