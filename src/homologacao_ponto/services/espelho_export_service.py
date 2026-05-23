from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from homologacao_ponto.infrastructure.espelho_ponto_parser import (
    EspelhoPontoParseError,
    EspelhoPontoParser,
)
from homologacao_ponto.models import (
    BrowserSession,
    ExportacaoEspelhoResult,
    ExportStatus,
)
from homologacao_ponto.services.result_writer import ResultWriteError, ResultWriter


@dataclass(frozen=True)
class EspelhoExportRequest:
    username_ref: str
    requested_server: str
    selected_server: str
    selected_identifier: str | None = None
    output_dir: Path | str = "data/runs"
    run_id: str | None = None


class EspelhoExportService:
    def __init__(
        self,
        browser,
        result_writer: ResultWriter,
        parser: EspelhoPontoParser | None = None,
    ) -> None:
        self.browser = browser
        self.result_writer = result_writer
        self.parser = parser or EspelhoPontoParser()

    def export(
        self, session: BrowserSession, request: EspelhoExportRequest
    ) -> ExportacaoEspelhoResult:
        session.require_authenticated()
        started_at = datetime.now(timezone.utc).isoformat()
        run_id = request.run_id or uuid4().hex
        try:
            snapshot = self.browser.capture_espelho_snapshot()
            if self.browser.is_anti_automation(snapshot.html):
                return self._persist_result(
                    self._failure(
                        request,
                        run_id,
                        started_at,
                        ExportStatus.BLOCKED,
                        "Validar Espelho",
                        "anti_automation",
                        "proteção anti-automação impede a automação",
                    )
                )
            if self.browser.is_session_expired(snapshot.html):
                return self._persist_result(
                    self._failure(
                        request,
                        run_id,
                        started_at,
                        ExportStatus.FAILED,
                        "Validar Espelho",
                        "session_expired",
                        "BrowserSession expirada durante a exportação",
                    )
                )
            export = self.parser.parse(
                snapshot,
                run_id=run_id,
                expected_server=request.selected_server or request.requested_server,
                expected_identifier=request.selected_identifier,
            )
            persisted_export = self.result_writer.write(export)
            result = ExportacaoEspelhoResult(
                run_id=run_id,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
                requested_server=request.requested_server,
                selected_server=export.servidor,
                periodo_referencia=export.periodo_referencia,
                status=ExportStatus.EMPTY
                if export.status == "empty"
                else ExportStatus.COMPLETED,
                success=True,
                final_step="Espelho Exportado",
                message="Espelho de Ponto sem registros"
                if export.status == "empty"
                else "Espelho de Ponto exportado com sucesso",
                export_path=persisted_export.output_path,
            )
            return self._persist_result(result)
        except EspelhoPontoParseError as exc:
            return self._persist_result(
                self._failure(
                    request,
                    run_id,
                    started_at,
                    ExportStatus.FAILED,
                    "Validar Espelho",
                    exc.code,
                    exc.message,
                )
            )
        except ResultWriteError as exc:
            return self._persist_result(
                self._failure(
                    request,
                    run_id,
                    started_at,
                    ExportStatus.FAILED,
                    "Escrever JSON",
                    "write_failed",
                    str(exc),
                )
            )

    def _persist_result(
        self, result: ExportacaoEspelhoResult
    ) -> ExportacaoEspelhoResult:
        try:
            return self.result_writer.write(result)
        except ResultWriteError:
            if result.success:
                return ExportacaoEspelhoResult(
                    run_id=result.run_id,
                    started_at=result.started_at,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    requested_server=result.requested_server,
                    selected_server=result.selected_server,
                    periodo_referencia=result.periodo_referencia,
                    status=ExportStatus.FAILED,
                    success=False,
                    final_step="Escrever Resultado",
                    message="arquivo JSON local não pôde ser escrito",
                    error_code="write_failed",
                )
            raise

    @staticmethod
    def _failure(
        request: EspelhoExportRequest,
        run_id: str,
        started_at: str,
        status: ExportStatus,
        final_step: str,
        error_code: str,
        message: str,
    ) -> ExportacaoEspelhoResult:
        return ExportacaoEspelhoResult(
            run_id=run_id,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc).isoformat(),
            requested_server=request.requested_server,
            status=status,
            success=False,
            final_step=final_step,
            message=message,
            error_code=error_code,
        )
