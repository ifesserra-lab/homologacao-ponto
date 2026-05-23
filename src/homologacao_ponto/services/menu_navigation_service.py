from __future__ import annotations

import logging
from dataclasses import dataclass, field

from homologacao_ponto.infrastructure.logging import log_navigation_event
from homologacao_ponto.infrastructure.rate_limiter import RateLimiter
from homologacao_ponto.infrastructure.sigrh_browser import (
    MenuNavigationError,
    SigrhBrowser,
)
from homologacao_ponto.models import (
    BrowserSession,
    NavigationPath,
    NavigationResult,
    NavigationStatus,
    NavigationStep,
    NavigationStepStatus,
)


@dataclass(frozen=True)
class MenuNavigationRequest:
    username_ref: str
    path: NavigationPath = field(default_factory=NavigationPath.default)


class MenuNavigationService:
    def __init__(
        self,
        browser: SigrhBrowser,
        rate_limiter: RateLimiter | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.browser = browser
        self.rate_limiter = rate_limiter or RateLimiter(2)
        self.logger = logger or logging.getLogger("homologacao_ponto")

    def navigate_to_espelho(
        self, session: BrowserSession, request: MenuNavigationRequest
    ) -> NavigationResult:
        session.require_authenticated()
        steps: list[NavigationStep] = []
        log_navigation_event(
            self.logger,
            "navigation started",
            destination=request.path.destination_label,
        )
        self.rate_limiter.wait_before_action()

        for position, label in enumerate(request.path.labels, start=1):
            try:
                is_final_step = position == len(request.path.labels)
                if is_final_step:
                    snapshot = self.browser.click_menu_label(
                        label, request.path.max_step_wait_seconds
                    )
                else:
                    hover = getattr(self.browser, "hover_menu_label", None)
                    snapshot = (
                        hover(label, request.path.max_step_wait_seconds)
                        if hover
                        else self.browser.click_menu_label(
                            label, request.path.max_step_wait_seconds
                        )
                    )
            except MenuNavigationError as exc:
                step = NavigationStep(label, position, exc.status, exc.message)
                steps.append(step)
                log_navigation_event(
                    self.logger,
                    "navigation step failed",
                    step=label,
                    status=exc.status.value,
                )
                return self._result_for_step_failure(request.username_ref, step, steps)

            if self.browser.is_anti_automation(snapshot.html):
                step = NavigationStep(
                    label,
                    position,
                    NavigationStepStatus.BLOCKED,
                    "proteção anti-automação impede a automação",
                )
                steps.append(step)
                return NavigationResult(
                    request.username_ref,
                    NavigationStatus.BLOCKED,
                    label,
                    steps,
                    "proteção anti-automação impede a automação",
                )
            if self.browser.is_session_expired(snapshot.html):
                step = NavigationStep(
                    label,
                    position,
                    NavigationStepStatus.EXPIRED,
                    "BrowserSession expirada durante a navegação",
                )
                steps.append(step)
                return NavigationResult(
                    request.username_ref,
                    NavigationStatus.PARTIAL,
                    label,
                    steps,
                    "BrowserSession expirada durante a navegação",
                )

            step_status = (
                NavigationStepStatus.CLICKED
                if is_final_step
                else NavigationStepStatus.HOVERED
            )
            steps.append(NavigationStep(label, position, step_status))
            event = (
                "navigation step clicked"
                if is_final_step
                else "navigation step hovered"
            )
            log_navigation_event(self.logger, event, step=label)

        if not self.browser.destination_visible(request.path.destination_label):
            step = NavigationStep(
                request.path.destination_label,
                len(request.path.labels),
                NavigationStepStatus.DESTINATION_MISMATCH,
                'confirmação visível "Espelho do Ponto" não encontrada',
            )
            steps[-1] = step
            return NavigationResult(
                request.username_ref,
                NavigationStatus.FAILED,
                request.path.destination_label,
                steps,
                'confirmação visível "Espelho do Ponto" não encontrada',
            )

        log_navigation_event(
            self.logger,
            "navigation completed",
            destination=request.path.destination_label,
        )
        return NavigationResult(
            request.username_ref,
            NavigationStatus.COMPLETED,
            request.path.destination_label,
            steps,
            "navegação concluída",
        )

    @staticmethod
    def _result_for_step_failure(
        username_ref: str, step: NavigationStep, steps: list[NavigationStep]
    ) -> NavigationResult:
        if step.status == NavigationStepStatus.BLOCKED:
            status = NavigationStatus.BLOCKED
        elif step.status == NavigationStepStatus.EXPIRED:
            status = NavigationStatus.PARTIAL
        else:
            status = NavigationStatus.FAILED
        return NavigationResult(username_ref, status, step.label, steps, step.message)
