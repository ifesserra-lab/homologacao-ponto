from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import (
    BrowserSession,
    BrowserSessionState,
    Credential,
    NavigationStepStatus,
    ServidorResultado,
    normalize_navigation_label,
    normalize_server_name,
)


LOGIN_URL = "https://sigrh.ifes.edu.br/sigrh/login.jsf"


class BrowserSetupError(RuntimeError):
    pass


class MenuNavigationError(RuntimeError):
    def __init__(self, label: str, status: NavigationStepStatus, message: str) -> None:
        super().__init__(message)
        self.label = label
        self.status = status
        self.message = message


@dataclass(frozen=True)
class SigrhLoginResult:
    success: bool
    state: BrowserSessionState
    message: str
    landing_url: str | None = None
    browser_session: BrowserSession | None = None


class SigrhBrowser:
    def __init__(self, headed: bool = False) -> None:
        self.headed = headed
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._page: Any = None

    def start(self) -> BrowserSession:
        try:
            from playwright.sync_api import Error, sync_playwright

            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=not self.headed)
            self._context = self._browser.new_context()
            self._page = self._context.new_page()
        except Exception as exc:
            if "Error" in locals() and isinstance(exc, Error):
                raise BrowserSetupError(
                    "Playwright browser could not start. Run: python -m playwright install chromium"
                ) from exc
            raise BrowserSetupError(
                "Playwright browser could not start. Run: python -m playwright install chromium"
            ) from exc
        return BrowserSession(context_id=uuid4().hex)

    def login(self, credential: Credential) -> SigrhLoginResult:
        session = BrowserSession(context_id=uuid4().hex)
        if self._page is None:
            self.start()
        page = self._page
        page.goto(LOGIN_URL)
        self._fill_first_available(page, ["input[name='username']", "input[name='login']", "#username"], credential.username)
        self._fill_first_available(page, ["input[type='password']", "input[name='password']", "#password"], credential.password)
        self._click_first_available(page, ["input[type='submit']", "button[type='submit']", "button:has-text('Entrar')"])
        html = page.content()
        current_url = getattr(page, "url", LOGIN_URL)
        return self.detect_login_result(html, current_url, session)

    def detect_login_result(
        self, html: str, current_url: str, session: BrowserSession | None = None
    ) -> SigrhLoginResult:
        base_session = session or BrowserSession(context_id=uuid4().hex)
        if self.is_anti_automation(html):
            return SigrhLoginResult(
                success=False,
                state=BrowserSessionState.BLOCKED,
                message="CAPTCHA, MFA ou proteção anti-automação impede a automação.",
                landing_url=current_url,
                browser_session=base_session.blocked("anti-automation protection"),
            )
        if self.is_session_expired(html):
            return SigrhLoginResult(
                success=False,
                state=BrowserSessionState.EXPIRED,
                message="BrowserSession expirada.",
                landing_url=current_url,
                browser_session=base_session.failed("session expired before authentication"),
            )
        if self.is_invalid_login(html):
            return SigrhLoginResult(
                success=False,
                state=BrowserSessionState.FAILED,
                message="Credenciais invalidas.",
                landing_url=current_url,
                browser_session=base_session.failed("invalid credentials"),
            )
        return SigrhLoginResult(
            success=True,
            state=BrowserSessionState.AUTHENTICATED,
            message="Login realizado com sucesso.",
            landing_url=current_url,
            browser_session=base_session.authenticated(base_session.context_id or uuid4().hex, current_url),
        )

    def capture_snapshot(self) -> SigrhPageSnapshot:
        if self._page is None:
            raise RuntimeError("browser page is not started")
        return SigrhPageSnapshot(
            url=self._page.url,
            title=self._page.title(),
            html=self._page.content(),
            captured_at=datetime.now(timezone.utc).isoformat(),
        )

    def capture_espelho_snapshot(self) -> SigrhPageSnapshot:
        snapshot = self.capture_snapshot()
        return SigrhPageSnapshot(
            url=snapshot.url,
            title=snapshot.title,
            html=f"{snapshot.html}{self._espelho_form_context_html()}",
            captured_at=snapshot.captured_at,
        )

    def goto(self, url: str) -> SigrhPageSnapshot:
        if self._page is None:
            self.start()
        self._page.goto(url)
        return self.capture_snapshot()

    def click_menu_path(self, labels: list[str], timeout_seconds: int = 15) -> SigrhPageSnapshot:
        snapshot: SigrhPageSnapshot | None = None
        for label in labels:
            snapshot = self.click_menu_label(label, timeout_seconds)
        if snapshot is None:
            raise MenuNavigationError("", NavigationStepStatus.MISSING, "caminho de menu vazio")
        return snapshot

    def wait_for_menu_label(self, label: str, timeout_seconds: int = 15):
        if self._page is None:
            self.start()
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            for variant in self._label_variants(label):
                exact_text = re.compile(rf"^\s*{re.escape(variant)}\s*$", re.IGNORECASE)
                loose_text = re.compile(re.escape(variant), re.IGNORECASE)
                for locator in self._menu_label_locators(exact_text, loose_text):
                    try:
                        if locator.count() and locator.first.is_visible():
                            return locator.first
                    except Exception:
                        continue
            self._page.wait_for_timeout(200)
        raise MenuNavigationError(
            label,
            NavigationStepStatus.TIMED_OUT,
            f"menu não encontrado em até {timeout_seconds} segundos: {label}",
        )

    def click_menu_label(self, label: str, timeout_seconds: int = 15) -> SigrhPageSnapshot:
        locator = self.wait_for_menu_label(label, timeout_seconds)
        locator.click()
        self._wait_after_menu_click(timeout_seconds)
        return self.capture_snapshot()

    def hover_menu_label(self, label: str, timeout_seconds: int = 15) -> SigrhPageSnapshot:
        locator = self.wait_for_menu_label(label, timeout_seconds)
        locator.hover()
        return self.capture_snapshot()

    def destination_visible(self, label: str) -> bool:
        if self._page is None:
            return False
        visible_text = f"{self._page.title()} {self._page.content()}"
        normalized_text = normalize_navigation_label(visible_text)
        return any(
            normalize_navigation_label(variant) in normalized_text
            for variant in self._label_variants(label)
        )

    def search_server_results(
        self,
        server_name: str,
        timeout_seconds: int = 15,
        reference_month: int | None = None,
        reference_year: int | None = None,
        identifier_hint: str | None = None,
    ) -> SigrhPageSnapshot:
        if self._page is None:
            self.start()
        page = self._page
        self._select_reference_period(page, reference_month, reference_year)
        self._check_first_available(page, ["#form\\:checkServidor", "input[name='form:checkServidor']"])
        field = self._first_available(page, ["#form\\:nomeServidor", "input[name='form:nomeServidor']", "input[title='Servidor']"])
        if field is not None:
            field.click()
            field.fill("")
            try:
                field.type(server_name, delay=50)
            except Exception:
                field.fill(server_name)
        page.wait_for_timeout(1000)
        self._click_server_suggestion(server_name, identifier_hint=identifier_hint)
        self._click_buscar(page)
        self._wait_after_menu_click(timeout_seconds)
        return self.capture_snapshot()

    def _select_reference_period(
        self, page: Any, reference_month: int | None, reference_year: int | None
    ) -> None:
        if reference_month is not None:
            month = self._first_available(page, ["#form\\:mes", "select[name='form:mes']"])
            if month is not None:
                month.select_option(str(reference_month))
        if reference_year is not None:
            year = self._first_available(page, ["#form\\:ano", "input[name='form:ano']"])
            if year is not None:
                year.fill(str(reference_year))

    def find_server_results(self, server_name: str) -> list[ServidorResultado]:
        if self._page is None:
            return []
        rows = self._page.locator("table.listagem tr")
        results: list[ServidorResultado] = []
        for index in range(rows.count()):
            row = rows.nth(index)
            try:
                row_text = row.inner_text().strip()
            except Exception:
                continue
            if not row_text or "SIAPE" in row_text.upper():
                continue
            selection_available = self._row_selection_locator(row).count() > 0
            identifier_match = re.search(r"\b\d{5,}\b", row_text)
            identifier = identifier_match.group(0) if identifier_match else None
            display_name = self._display_name_from_row(row_text, identifier)
            if display_name:
                results.append(ServidorResultado(display_name, identifier, row_text, selection_available))
        return results

    def empty_query_matches_server(self, server_name: str) -> bool:
        if self._page is None:
            return False
        server_value = self._input_value(["#form\\:nomeServidor", "input[name='form:nomeServidor']"])
        if normalize_server_name(server_name) not in normalize_server_name(server_value):
            return False
        try:
            body_text = self._page.locator("body").inner_text()
        except Exception:
            body_text = self._page.content()
        normalized_text = normalize_server_name(body_text)
        return "nenhum registro de ponto" in normalized_text or "nenhum registro" in normalized_text

    def queried_server_name(self) -> str | None:
        value = self._input_value(["#form\\:nomeServidor", "input[name='form:nomeServidor']"])
        return value or None

    def select_server_result(self, result: ServidorResultado, timeout_seconds: int = 15) -> SigrhPageSnapshot:
        if self._page is None:
            self.start()
        rows = self._page.locator("table.listagem tr")
        for index in range(rows.count()):
            row = rows.nth(index)
            try:
                row_text = row.inner_text().strip()
            except Exception:
                continue
            if normalize_server_name(row_text) != result.normalized_row_text:
                continue
            locator = self._row_selection_locator(row)
            if locator.count():
                locator.first.click()
                self._wait_after_menu_click(timeout_seconds)
                return self.capture_snapshot()
        raise MenuNavigationError(
            "Selecionar Servidor",
            NavigationStepStatus.MISSING,
            f"seleção não disponível para servidor: {result.display_name}",
        )

    def selected_server_visible(self, server_name: str, identifier: str | None = None) -> bool:
        if self._page is None:
            return False
        visible_text = f"{self._page.title()} {self._page.content()}"
        normalized_text = normalize_server_name(visible_text)
        if normalize_server_name(server_name) in normalized_text:
            return True
        return bool(identifier and identifier in visible_text)

    def close(self) -> None:
        for resource in (self._context, self._browser):
            if resource is not None:
                resource.close()
        if self._playwright is not None:
            self._playwright.stop()
        self._context = None
        self._browser = None
        self._playwright = None
        self._page = None

    @staticmethod
    def is_invalid_login(html: str) -> bool:
        lowered = html.lower()
        return any(token in lowered for token in ("senha inval", "senha invál", "usuario ou senha", "usuário ou senha"))

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        lowered = html.lower()
        return any(token in lowered for token in ("captcha", "mfa", "anti-autom", "bloqueio de autom"))

    @staticmethod
    def is_session_expired(html: str) -> bool:
        lowered = html.lower()
        return "sessao expirada" in lowered or "sessão expirada" in lowered

    @staticmethod
    def _fill_first_available(page: Any, selectors: list[str], value: str) -> None:
        for selector in selectors:
            locator = page.locator(selector)
            if locator.count():
                locator.first.fill(value)
                return

    @staticmethod
    def _click_first_available(page: Any, selectors: list[str]) -> None:
        for selector in selectors:
            locator = page.locator(selector)
            if locator.count():
                locator.first.click()
                return

    @staticmethod
    def _first_available(page: Any, selectors: list[str]):
        for selector in selectors:
            locator = page.locator(selector)
            if locator.count():
                return locator.first
        return None

    @staticmethod
    def _check_first_available(page: Any, selectors: list[str]) -> None:
        for selector in selectors:
            locator = page.locator(selector)
            if locator.count():
                try:
                    locator.first.check()
                except Exception:
                    locator.first.click()
                return

    def _espelho_form_context_html(self) -> str:
        server = self._input_value(["#form\\:nomeServidor", "input[name='form:nomeServidor']"])
        year = self._input_value(["#form\\:ano", "input[name='form:ano']"])
        month = self._input_value(["#form\\:mes", "select[name='form:mes']"])
        pieces: list[str] = []
        if server:
            pieces.append(f'<div class="servidor">Servidor: {server}</div>')
        if month and year:
            pieces.append(f'<div class="periodo">Periodo: {self._month_name(month)}/{year}</div>')
        return "".join(pieces)

    def _input_value(self, selectors: list[str]) -> str:
        if self._page is None:
            return ""
        locator = self._first_available(self._page, selectors)
        if locator is None:
            return ""
        try:
            return str(locator.input_value()).strip()
        except Exception:
            try:
                return str(locator.get_attribute("value") or "").strip()
            except Exception:
                return ""

    @staticmethod
    def _month_name(month: str) -> str:
        names = {
            "1": "Janeiro",
            "2": "Fevereiro",
            "3": "Marco",
            "4": "Abril",
            "5": "Maio",
            "6": "Junho",
            "7": "Julho",
            "8": "Agosto",
            "9": "Setembro",
            "10": "Outubro",
            "11": "Novembro",
            "12": "Dezembro",
        }
        key = str(int(month)) if str(month).isdigit() else month
        return names.get(key, month)

    @staticmethod
    def _label_variants(label: str) -> list[str]:
        variants = [label]
        replacements = {
            "Homologacao de Ponto Eletronico": "Homologação de Ponto Eletrônico",
            "Relatorio": "Relatório",
            "Espelho do Ponto": "Espelho de Ponto",
        }
        if label in replacements:
            variants.append(replacements[label])
        if label == "Relatorio":
            variants.append("Relatórios")
        return variants

    def _wait_after_menu_click(self, timeout_seconds: int) -> None:
        if self._page is None:
            return
        try:
            self._page.wait_for_load_state("domcontentloaded", timeout=timeout_seconds * 1000)
        except Exception:
            pass
        self._page.wait_for_timeout(500)

    def _menu_label_locators(self, exact_text: re.Pattern[str], loose_text: re.Pattern[str]) -> list[Any]:
        if self._page is None:
            return []
        return [
            self._page.locator("a:visible").filter(has_text=exact_text),
            self._page.locator("span:visible").filter(has_text=exact_text),
            self._page.locator("td:visible").filter(has_text=exact_text),
            self._page.locator("li:visible").filter(has_text=exact_text),
            self._page.get_by_text(exact_text),
            self._page.locator("a:visible").filter(has_text=loose_text),
            self._page.locator("span:visible").filter(has_text=loose_text),
            self._page.locator("td:visible").filter(has_text=loose_text),
            self._page.locator("li:visible").filter(has_text=loose_text),
        ]

    def _click_server_suggestion(self, server_name: str, identifier_hint: str | None = None) -> None:
        if self._page is None:
            return
        deadline = time.monotonic() + 8
        normalized_name = normalize_server_name(server_name)
        selectors = [
            "td.richfaces_suggestionSelectValue:visible",
            "tr.richfaces_suggestionEntry:visible td",
            "#form\\:suggestionServidor\\:suggest tr td",
            "[id='form:suggestionServidor:suggest'] tr td",
            "[id='form:suggestionServidor'] td",
        ]
        while time.monotonic() < deadline:
            for selector in selectors:
                suggestions = self._page.locator(selector)
                try:
                    for index in range(suggestions.count()):
                        item = suggestions.nth(index)
                        try:
                            text = item.inner_text().strip()
                        except Exception:
                            continue
                        if text and normalized_name in normalize_server_name(text):
                            if identifier_hint is None or identifier_hint in text:
                                item.click(force=True)
                                self._page.wait_for_timeout(1500)
                                return
                except Exception:
                    continue
            self._page.wait_for_timeout(300)
        try:
            field = self._first_available(self._page, ["#form\\:nomeServidor", "input[name='form:nomeServidor']"])
            if field is not None:
                field.press("ArrowDown")
                self._page.wait_for_timeout(800)
                field.press("Enter")
                self._page.wait_for_timeout(1500)
        except Exception:
            return

    def _click_buscar(self, page: Any) -> None:
        buscar_selectors = ["#form\\:buscarServidores", "input[name='form:buscarServidores']", "input[value='Buscar']"]
        buscar = self._first_available(page, buscar_selectors)
        if buscar is None:
            return
        try:
            buscar.click()
        except Exception:
            buscar.click(force=True)

    @staticmethod
    def _row_selection_locator(row: Any):
        return row.locator(
            "a[title*='Selecionar'], a:has-text('Selecionar Servidor'), "
            "input[title*='Selecionar'], input[alt*='Selecionar'], button:has-text('Selecionar')"
        )

    @staticmethod
    def _display_name_from_row(row_text: str, identifier: str | None) -> str:
        text = re.sub(r"\bSIAPE\b|\bNome\b|\bCargo\b|Selecionar( Servidor)?", " ", row_text, flags=re.IGNORECASE)
        if identifier:
            text = text.replace(identifier, " ")
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return ""
        professor_index = normalize_server_name(text).find(" professor")
        if professor_index > 0:
            text = text[:professor_index].strip()
        return text
