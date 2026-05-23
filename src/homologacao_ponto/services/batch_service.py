from __future__ import annotations

import datetime

from homologacao_ponto.models.batch_config import BatchConfig
from homologacao_ponto.models.batch_result import BatchEntryResult, BatchResult
from homologacao_ponto.models.browser_session import BrowserSession
from homologacao_ponto.services.periodo_expander import PeriodoExpander
from homologacao_ponto.services.result_writer import ResultWriter


class BatchService:
    def __init__(self, app, result_writer: ResultWriter) -> None:
        self._app = app
        self._writer = result_writer

    def run(
        self, session: BrowserSession, config: BatchConfig, run_id: str
    ) -> BatchResult:
        """Processa todos os servidores da configuração em sequência.

        A sessão do navegador é reutilizada entre servidores para evitar o
        overhead de login repetido; em caso de expiração (exit_code==6) ela é
        renovada uma única vez — mais de um retry mascararia falhas sistêmicas
        de autenticação.
        """
        started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        today = datetime.date.today()
        entries: list[BatchEntryResult] = []

        for entry in config.servidores:
            periodos = PeriodoExpander.expand(config, entry, today)
            if not periodos:
                # anos="All" — AdmissaoDetector (US2)
                from homologacao_ponto.infrastructure.admissao_detector import (
                    AdmissaoDetector,
                    AdmissaoNaoDetectadaError,
                )

                try:
                    periodos = AdmissaoDetector().detect(
                        self._app, session, entry, today
                    )
                except AdmissaoNaoDetectadaError as exc:
                    entries.append(
                        BatchEntryResult(
                            nome=entry.nome,
                            siape=entry.siape,
                            status="failed",
                            error=str(exc),
                        )
                    )
                    continue
            for mes, ano in periodos:
                try:
                    app_result = self._app._run_single_espelho(
                        session,
                        servidor=entry.nome,
                        siape=entry.siape,
                        mes=mes,
                        ano=ano,
                    )
                    if app_result.exit_code == 6:
                        # sessão expirada — reautentica e retenta uma vez
                        try:
                            cred = self._app.credential_provider.load()
                            login = self._app.auth_service.login(cred)
                            if login.success and login.browser_session:
                                session = login.browser_session
                                app_result = self._app._run_single_espelho(
                                    session,
                                    servidor=entry.nome,
                                    siape=entry.siape,
                                    mes=mes,
                                    ano=ano,
                                )
                        except Exception:
                            pass

                    if app_result.exit_code == 0 and app_result.result is not None:
                        export_path = getattr(app_result.result, "output_path", None)
                        status = (
                            getattr(
                                getattr(app_result.result, "status", None),
                                "value",
                                None,
                            )
                            or "completed"
                        )
                        entries.append(
                            BatchEntryResult(
                                nome=entry.nome,
                                siape=entry.siape,
                                status=status
                                if status in ("completed", "empty")
                                else "completed",
                                export_path=str(export_path) if export_path else None,
                                mes=mes,
                                ano=ano,
                            )
                        )
                    else:
                        entries.append(
                            BatchEntryResult(
                                nome=entry.nome,
                                siape=entry.siape,
                                status="failed",
                                # app_result.message pode ser None ou objeto não-string;
                                # guarda isinstance evita TypeError no json.dumps.
                                error=str(app_result.message)
                                if isinstance(app_result.message, str)
                                and app_result.message
                                else f"exit_code={app_result.exit_code}",
                                mes=mes,
                                ano=ano,
                            )
                        )
                except Exception as exc:
                    entries.append(
                        BatchEntryResult(
                            nome=entry.nome,
                            siape=entry.siape,
                            status="failed",
                            error=str(exc),
                            mes=mes,
                            ano=ano,
                        )
                    )

        finished_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        succeeded = sum(1 for e in entries if e.status in ("completed", "empty"))
        failed = len(entries) - succeeded

        result = BatchResult(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            total=len(entries),
            succeeded=succeeded,
            failed=failed,
            entries=entries,
        )
        persisted = self._writer.write(result)
        return persisted
