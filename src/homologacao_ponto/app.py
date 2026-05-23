from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from homologacao_ponto.infrastructure import configure_logging
from homologacao_ponto.infrastructure.credential_provider import CredentialProvider
from homologacao_ponto.infrastructure.sigrh_browser import (
    BrowserSetupError,
    SigrhBrowser,
)
from homologacao_ponto.models import (
    BrowserSession,
    BrowserSessionState,
    CrawlResult,
    CrawlStatus,
    ExportacaoEspelhoResult,
    ExportStatus,
    NavigationResult,
    NavigationStatus,
    SelecaoServidorResult,
    SelectionStatus,
)
from homologacao_ponto.models.batch_config import BatchConfig
from homologacao_ponto.services.authentication_service import AuthenticationService
from homologacao_ponto.services.crawler_service import (
    CrawlRequest,
    CrawlerService,
    ScopePolicyError,
)
from homologacao_ponto.services.espelho_export_service import (
    EspelhoExportRequest,
    EspelhoExportService,
)
from homologacao_ponto.services.menu_navigation_service import (
    MenuNavigationRequest,
    MenuNavigationService,
)
from homologacao_ponto.services.result_writer import ResultWriteError, ResultWriter
from homologacao_ponto.services.server_selection_service import (
    ServerSelectionRequest,
    ServerSelectionService,
)


DEFAULT_ATTENDANCE_URL = "https://sigrh.ifes.edu.br/sigrh/frequencia/espelho.jsf"
CURRENT_ESPELHO_PONTO_URL = "https://sigrh.ifes.edu.br/sigrh/frequencia/ponto_eletronico/consulta/consulta_ponto_eletronico.jsf"


@dataclass(frozen=True)
class AppResult:
    exit_code: int
    message: str
    result: (
        CrawlResult
        | NavigationResult
        | SelecaoServidorResult
        | ExportacaoEspelhoResult
        | None
    ) = None


class HomologacaoPontoApp:
    def __init__(
        self,
        credential_provider: CredentialProvider,
        browser: SigrhBrowser,
        auth_service: AuthenticationService,
        crawler_service: CrawlerService,
        result_writer: ResultWriter,
        menu_navigation_service: MenuNavigationService | None = None,
        server_selection_service: ServerSelectionService | None = None,
        espelho_export_service: EspelhoExportService | None = None,
    ) -> None:
        self.credential_provider = credential_provider
        self.browser = browser
        self.auth_service = auth_service
        self.crawler_service = crawler_service
        self.result_writer = result_writer
        self.menu_navigation_service = menu_navigation_service
        self.server_selection_service = server_selection_service
        self.espelho_export_service = espelho_export_service

    def run(self, attendance_urls: list[str] | None = None) -> AppResult:
        try:
            credential = self.credential_provider.load()
            login = self.auth_service.login(credential)
            if login.state == BrowserSessionState.FAILED:
                return AppResult(2, login.message)
            if login.state == BrowserSessionState.BLOCKED:
                return AppResult(3, login.message)
            if not login.success or login.browser_session is None:
                return AppResult(2, login.message)
            result = self.crawler_service.crawl(
                login.browser_session,
                CrawlRequest(
                    username_ref=credential.username_ref(),
                    start_urls=attendance_urls or [DEFAULT_ATTENDANCE_URL],
                ),
            )
            if result.status == CrawlStatus.BLOCKED:
                return AppResult(3, result.message or "proteção anti-automação")
            persisted = self.result_writer.write(result)
            if persisted.status == CrawlStatus.PARTIAL:
                if persisted.message and "expirada" in persisted.message:
                    return AppResult(6, persisted.message, persisted)
                return AppResult(4, persisted.message or "resultado parcial", persisted)
            return AppResult(
                0,
                f"Login realizado com sucesso. {persisted.visited_page_count} páginas visitadas, "
                f"{persisted.record_count} registros coletados. JSON: {persisted.output_path}",
                persisted,
            )
        except BrowserSetupError as exc:
            return AppResult(7, str(exc))
        except ResultWriteError as exc:
            return AppResult(5, str(exc))
        except ScopePolicyError as exc:
            return AppResult(4, str(exc))
        finally:
            self.browser.close()

    def _run_single_espelho(
        self,
        session: "BrowserSession",
        servidor: str | None,
        siape: str | None,
        mes: int | None,
        ano: int | None,
    ) -> AppResult:
        credential = self.credential_provider.load()
        if self.menu_navigation_service is None:
            self.menu_navigation_service = MenuNavigationService(self.browser)
        result = self.menu_navigation_service.navigate_to_espelho(
            session,
            MenuNavigationRequest(username_ref=credential.username_ref()),
        )
        if servidor:
            if result.status != NavigationStatus.COMPLETED:
                if not self._try_direct_espelho_navigation(result):
                    selection_result = self._selection_result_from_navigation_failure(
                        credential.username_ref(), servidor, result
                    )
                    persisted_selection = self.result_writer.write(selection_result)
                    return self._selection_app_result(persisted_selection)
            if self.server_selection_service is None:
                self.server_selection_service = ServerSelectionService(self.browser)
            selection_result = self.server_selection_service.select_server(
                session,
                ServerSelectionRequest(
                    username_ref=credential.username_ref(),
                    requested_server=servidor,
                    reference_month=mes,
                    reference_year=ano,
                    requested_identifier=siape,
                ),
            )
            persisted_selection = self.result_writer.write(selection_result)
            selection_app_result = self._selection_app_result(persisted_selection)
            if not persisted_selection.success:
                return selection_app_result
            if self.espelho_export_service is None:
                self.espelho_export_service = EspelhoExportService(
                    self.browser, self.result_writer
                )
            export_result = self.espelho_export_service.export(
                session,
                EspelhoExportRequest(
                    username_ref=credential.username_ref(),
                    requested_server=servidor,
                    selected_server=persisted_selection.selected_server or servidor,
                    selected_identifier=persisted_selection.selected_identifier,
                    output_dir=self.result_writer.output_dir,
                    run_id=persisted_selection.run_id,
                ),
            )
            return self._export_app_result(export_result)
        persisted = self.result_writer.write(result)
        json_suffix = f" JSON: {persisted.output_path}" if persisted.output_path else ""
        if persisted.status == NavigationStatus.BLOCKED:
            return AppResult(3, f"{persisted.message}{json_suffix}", persisted)
        if persisted.status == NavigationStatus.PARTIAL:
            return AppResult(6, f"{persisted.message}{json_suffix}", persisted)
        if persisted.status == NavigationStatus.FAILED:
            return AppResult(4, f"{persisted.message}{json_suffix}", persisted)
        return AppResult(
            0,
            f"Login realizado com sucesso. Navegação concluída até Espelho do Ponto.{json_suffix}",
            persisted,
        )

    def run_espelho_ponto(
        self,
        servidor: str | None = None,
        mes: int | None = None,
        ano: int | None = None,
        siape: str | None = None,
    ) -> AppResult:
        try:
            credential = self.credential_provider.load()
            login = self.auth_service.login(credential)
            if login.state == BrowserSessionState.FAILED:
                return AppResult(2, login.message)
            if login.state == BrowserSessionState.BLOCKED:
                return AppResult(3, login.message)
            if not login.success or login.browser_session is None:
                return AppResult(2, login.message)
            return self._run_single_espelho(
                login.browser_session, servidor, siape, mes, ano
            )
        except BrowserSetupError as exc:
            return AppResult(7, str(exc))
        except ResultWriteError as exc:
            return AppResult(5, str(exc))
        finally:
            self.browser.close()

    def run_batch(self, config: "BatchConfig") -> "AppResult":
        import uuid
        from homologacao_ponto.services.batch_service import BatchService

        try:
            credential = self.credential_provider.load()
            login = self.auth_service.login(credential)
            if login.state == BrowserSessionState.FAILED:
                return AppResult(2, login.message)
            if login.state == BrowserSessionState.BLOCKED:
                return AppResult(3, login.message)
            if not login.success or login.browser_session is None:
                return AppResult(2, login.message)
            run_id = uuid.uuid4().hex
            batch_service = BatchService(self, self.result_writer)
            result = batch_service.run(login.browser_session, config, run_id=run_id)
            succeeded = result.succeeded
            failed = result.failed
            total = result.total
            path = result.output_path or ""
            if failed > 0:
                return AppResult(
                    1,
                    f"Lote concluído com falhas: {succeeded}/{total} exportados. Relatório: {path}",
                    result,
                )
            return AppResult(
                0,
                f"Lote concluído: {succeeded}/{total} exportados com sucesso. Relatório: {path}",
                result,
            )
        except BrowserSetupError as exc:
            return AppResult(7, str(exc))
        except ResultWriteError as exc:
            return AppResult(5, str(exc))
        finally:
            self.browser.close()

    @staticmethod
    def _selection_result_from_navigation_failure(
        username_ref: str, servidor: str, result: NavigationResult
    ) -> SelecaoServidorResult:
        if result.status == NavigationStatus.BLOCKED:
            status = SelectionStatus.BLOCKED
        elif result.status == NavigationStatus.PARTIAL:
            status = SelectionStatus.PARTIAL
        else:
            status = SelectionStatus.FAILED
        return SelecaoServidorResult(
            username_ref=username_ref,
            requested_server=servidor,
            status=status,
            final_step=result.final_step,
            message=result.message or "navegação até Espelho do Ponto não concluída",
        )

    def _try_direct_espelho_navigation(self, result: NavigationResult) -> bool:
        if result.status != NavigationStatus.FAILED:
            return False
        snapshot = self.browser.goto(CURRENT_ESPELHO_PONTO_URL)
        if self.browser.is_anti_automation(
            snapshot.html
        ) or self.browser.is_session_expired(snapshot.html):
            return False
        return self.browser.destination_visible("Espelho do Ponto")

    @staticmethod
    def _selection_app_result(result: SelecaoServidorResult) -> AppResult:
        json_suffix = f" JSON: {result.output_path}" if result.output_path else ""
        if result.status == SelectionStatus.BLOCKED:
            return AppResult(3, f"{result.message}{json_suffix}", result)
        if result.status == SelectionStatus.PARTIAL:
            return AppResult(6, f"{result.message}{json_suffix}", result)
        if result.status == SelectionStatus.FAILED:
            return AppResult(4, f"{result.message}{json_suffix}", result)
        return AppResult(
            0,
            f"Login realizado com sucesso. Navegação concluída até Espelho do Ponto. "
            f"Servidor selecionado: {result.selected_server}.{json_suffix}",
            result,
        )

    @staticmethod
    def _export_app_result(result: ExportacaoEspelhoResult) -> AppResult:
        result_suffix = (
            f" Resultado: {result.output_path}" if result.output_path else ""
        )
        export_suffix = f" JSON: {result.export_path}" if result.export_path else ""
        if result.status == ExportStatus.BLOCKED:
            return AppResult(5, f"{result.message}{result_suffix}", result)
        if result.status == ExportStatus.FAILED:
            if result.error_code == "session_expired":
                return AppResult(2, f"{result.message}{result_suffix}", result)
            if result.error_code == "write_failed":
                return AppResult(6, f"{result.message}{result_suffix}", result)
            if result.error_code == "wrong_server":
                return AppResult(4, f"{result.message}{result_suffix}", result)
            return AppResult(3, f"{result.message}{result_suffix}", result)
        if result.status == ExportStatus.EMPTY:
            return AppResult(
                0,
                f"Espelho de Ponto sem registros para {result.requested_server}.{export_suffix}{result_suffix}",
                result,
            )
        return AppResult(
            0,
            f"Espelho de Ponto exportado com sucesso para {result.requested_server}."
            f"{export_suffix}{result_suffix}",
            result,
        )


def create_app(
    output_dir: Path | str, env_file: Path | str, headed: bool = False
) -> HomologacaoPontoApp:
    logger = configure_logging()
    browser = SigrhBrowser(headed=headed)
    return HomologacaoPontoApp(
        credential_provider=CredentialProvider(env_file=env_file),
        browser=browser,
        auth_service=AuthenticationService(browser, logger),
        crawler_service=CrawlerService(browser, logger=logger),
        result_writer=ResultWriter(output_dir),
        menu_navigation_service=MenuNavigationService(browser, logger=logger),
        server_selection_service=ServerSelectionService(browser, logger=logger),
        espelho_export_service=None,
    )
