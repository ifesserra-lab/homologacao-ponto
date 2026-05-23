from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from uuid import uuid4

from homologacao_ponto.models.espelho_ponto_export import ServidorSelecionado


class ExportStatus(StrEnum):
    COMPLETED = "completed"
    EMPTY = "empty"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ExportacaoEspelhoResult:
    requested_server: str
    status: ExportStatus
    success: bool
    final_step: str
    message: str
    run_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    selected_server: ServidorSelecionado | None = None
    periodo_referencia: str | None = None
    export_path: str | None = None
    error_code: str | None = None
    output_path: str | None = None

    def __post_init__(self) -> None:
        if not self.requested_server:
            raise ValueError("requested_server is required")
        if not self.final_step:
            raise ValueError("final_step is required")
        if not self.message:
            raise ValueError("message is required")
        if self.success and self.status not in {
            ExportStatus.COMPLETED,
            ExportStatus.EMPTY,
        }:
            raise ValueError("successful export requires completed or empty status")
        if self.success and not self.export_path:
            raise ValueError("successful export requires export_path")
        if not self.success and self.status in {
            ExportStatus.COMPLETED,
            ExportStatus.EMPTY,
        }:
            raise ValueError("unsuccessful export cannot use successful status")
        if not self.run_id:
            object.__setattr__(self, "run_id", uuid4().hex)
        now = datetime.now(timezone.utc).isoformat()
        if not self.started_at:
            object.__setattr__(self, "started_at", now)
        if not self.completed_at:
            object.__setattr__(self, "completed_at", now)

    @property
    def output_filename(self) -> str:
        return f"export-result-{self.run_id}.json"

    def with_output_path(self, output_path: Path) -> ExportacaoEspelhoResult:
        return ExportacaoEspelhoResult(
            run_id=self.run_id,
            started_at=self.started_at,
            completed_at=self.completed_at,
            requested_server=self.requested_server,
            selected_server=self.selected_server,
            periodo_referencia=self.periodo_referencia,
            status=self.status,
            success=self.success,
            final_step=self.final_step,
            message=self.message,
            export_path=self.export_path,
            error_code=self.error_code,
            output_path=str(output_path),
        )

    def with_export_path(self, export_path: Path) -> ExportacaoEspelhoResult:
        return ExportacaoEspelhoResult(
            run_id=self.run_id,
            started_at=self.started_at,
            completed_at=self.completed_at,
            requested_server=self.requested_server,
            selected_server=self.selected_server,
            periodo_referencia=self.periodo_referencia,
            status=self.status,
            success=self.success,
            final_step=self.final_step,
            message=self.message,
            export_path=str(export_path),
            error_code=self.error_code,
            output_path=self.output_path,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "success": self.success,
            "status": self.status.value,
            "final_step": self.final_step,
            "requested_server": self.requested_server,
            "selected_server": self.selected_server.to_dict()
            if self.selected_server
            else None,
            "periodo_referencia": self.periodo_referencia,
            "export_path": self.export_path,
            "message": self.message,
            "error_code": self.error_code,
        }
