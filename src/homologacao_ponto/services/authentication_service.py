from __future__ import annotations

import logging

from homologacao_ponto.infrastructure.sigrh_browser import (
    SigrhBrowser,
    SigrhLoginResult,
)
from homologacao_ponto.models import Credential


class AuthenticationService:
    def __init__(
        self, browser: SigrhBrowser, logger: logging.Logger | None = None
    ) -> None:
        self.browser = browser
        self.logger = logger or logging.getLogger("homologacao_ponto")

    def login(self, credential: Credential) -> SigrhLoginResult:
        result = self.browser.login(credential)
        self.logger.info("login outcome: %s", result.state.value)
        return result
