from __future__ import annotations

import logging
from dataclasses import dataclass

from homologacao_ponto.infrastructure.logging import log_navigation_event
from homologacao_ponto.infrastructure.rate_limiter import RateLimiter
from homologacao_ponto.infrastructure.sigrh_browser import SigrhBrowser
from homologacao_ponto.models import (
    BrowserSession,
    SelecaoServidorResult,
    SelectionStatus,
    ServidorConsulta,
)


@dataclass(frozen=True)
class ServerSelectionRequest:
    username_ref: str
    requested_server: str
    max_step_wait_seconds: int = 15
    reference_month: int | None = None
    reference_year: int | None = None
    requested_identifier: str | None = None

    def __post_init__(self) -> None:
        if self.reference_month is not None and not 1 <= self.reference_month <= 12:
            raise ValueError("reference_month must be between 1 and 12")
        if self.reference_year is not None and self.reference_year < 1900:
            raise ValueError("reference_year must be a valid year")


class ServerSelectionService:
    def __init__(
        self,
        browser: SigrhBrowser,
        rate_limiter: RateLimiter | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.browser = browser
        self.rate_limiter = rate_limiter or RateLimiter(2)
        self.logger = logger or logging.getLogger("homologacao_ponto")

    def select_server(
        self, session: BrowserSession, request: ServerSelectionRequest
    ) -> SelecaoServidorResult:
        session.require_authenticated()
        consulta = ServidorConsulta(
            request.requested_server, request.requested_identifier
        )
        log_navigation_event(
            self.logger,
            "server selection started",
            requested_server=request.requested_server,
        )

        self.rate_limiter.wait_before_action()
        if request.reference_month is None and request.reference_year is None:
            search_snapshot = self.browser.search_server_results(
                request.requested_server,
                request.max_step_wait_seconds,
                identifier_hint=request.requested_identifier,
            )
        else:
            search_snapshot = self.browser.search_server_results(
                request.requested_server,
                request.max_step_wait_seconds,
                request.reference_month,
                request.reference_year,
                identifier_hint=request.requested_identifier,
            )
        if self.browser.is_anti_automation(search_snapshot.html):
            return self._blocked(request, "Busca de Servidor")
        if self.browser.is_session_expired(search_snapshot.html):
            return self._partial(request, "Busca de Servidor")

        matches = [
            result
            for result in self.browser.find_server_results(request.requested_server)
            if result.matches(consulta)
        ]
        if not matches:
            if (
                request.reference_month is not None
                or request.reference_year is not None
            ) and self._empty_query_matches_server(request):
                selected_server = (
                    self.browser.queried_server_name() or request.requested_server
                )
                return SelecaoServidorResult(
                    username_ref=request.username_ref,
                    requested_server=request.requested_server,
                    status=SelectionStatus.COMPLETED,
                    final_step="Servidor Selecionado",
                    selected_server=selected_server.upper(),
                    message="servidor selecionado sem registros no periodo",
                )
            return self._failed(
                request,
                "Busca de Servidor",
                f"servidor não encontrado: {request.requested_server}",
            )
        if len(matches) > 1:
            return self._failed(
                request,
                "Busca de Servidor",
                f"resultado ambíguo para servidor: {request.requested_server}",
            )

        selected = matches[0]
        if not selected.can_select:
            return self._failed(
                request,
                "Selecionar Servidor",
                f"seleção não disponível para servidor: {selected.display_name}",
            )

        self.rate_limiter.wait_before_action()
        selection_snapshot = self.browser.select_server_result(
            selected, request.max_step_wait_seconds
        )
        if self.browser.is_anti_automation(selection_snapshot.html):
            return self._blocked(request, "Selecionar Servidor")
        if self.browser.is_session_expired(selection_snapshot.html):
            return self._partial(request, "Selecionar Servidor")
        if not self.browser.selected_server_visible(
            selected.display_name, selected.identifier
        ):
            return self._failed(
                request,
                "Servidor Selecionado",
                f"confirmação visível do servidor selecionado não encontrada: {selected.display_name}",
            )

        log_navigation_event(
            self.logger,
            "server selection completed",
            selected_server=selected.display_name,
        )
        return SelecaoServidorResult(
            username_ref=request.username_ref,
            requested_server=request.requested_server,
            status=SelectionStatus.COMPLETED,
            final_step="Servidor Selecionado",
            selected_server=selected.display_name,
            selected_identifier=selected.identifier,
            message="servidor selecionado",
        )

    @staticmethod
    def _failed(
        request: ServerSelectionRequest, final_step: str, message: str
    ) -> SelecaoServidorResult:
        return SelecaoServidorResult(
            request.username_ref,
            request.requested_server,
            SelectionStatus.FAILED,
            final_step,
            message=message,
        )

    @staticmethod
    def _partial(
        request: ServerSelectionRequest, final_step: str
    ) -> SelecaoServidorResult:
        return SelecaoServidorResult(
            request.username_ref,
            request.requested_server,
            SelectionStatus.PARTIAL,
            final_step,
            message="BrowserSession expirada durante a seleção do servidor",
        )

    @staticmethod
    def _blocked(
        request: ServerSelectionRequest, final_step: str
    ) -> SelecaoServidorResult:
        return SelecaoServidorResult(
            request.username_ref,
            request.requested_server,
            SelectionStatus.BLOCKED,
            final_step,
            message="proteção anti-automação impede a automação",
        )

    def _empty_query_matches_server(self, request: ServerSelectionRequest) -> bool:
        checker = getattr(self.browser, "empty_query_matches_server", None)
        return bool(checker and checker(request.requested_server))
