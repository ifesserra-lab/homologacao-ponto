from pathlib import Path

from fixtures.sigrh_espelho_export_pages import EMPTY_ESPELHO_PAGE_HTML, INVALID_PAGE_HTML, VALID_ESPELHO_PAGE_HTML, WRONG_SERVER_PAGE_HTML
from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import BrowserSession, ExportStatus
from homologacao_ponto.services.espelho_export_service import EspelhoExportRequest, EspelhoExportService
from homologacao_ponto.services.result_writer import ResultWriter


class SnapshotBrowser:
    def __init__(self, html: str) -> None:
        self.html = html

    def capture_espelho_snapshot(self):
        return SigrhPageSnapshot("https://sigrh.ifes.edu.br/sigrh/frequencia/espelho.jsf", "Espelho", self.html, "2026-05-20T12:00:00+00:00")

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return "captcha" in html.lower()

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return "sessao expirada" in html.lower()


def request(tmp_path: Path) -> EspelhoExportRequest:
    return EspelhoExportRequest(
        username_ref="paulo",
        requested_server="Celio Proliciano Maioli",
        selected_server="CELIO PROLICIANO MAIOLI",
        selected_identifier="1534589",
        output_dir=tmp_path,
        run_id="run-123",
    )


def test_export_service_writes_success_report_and_result(tmp_path) -> None:
    result = EspelhoExportService(SnapshotBrowser(VALID_ESPELHO_PAGE_HTML), ResultWriter(tmp_path)).export(
        BrowserSession().authenticated("ctx"), request(tmp_path)
    )

    assert result.status == ExportStatus.COMPLETED
    assert result.success is True
    assert (tmp_path / "servidores" / "celio-proliciano-maioli" / "espelho-maio-2026.json").exists()
    assert (tmp_path / "export-result-run-123.json").exists()


def test_export_service_writes_empty_report(tmp_path) -> None:
    result = EspelhoExportService(SnapshotBrowser(EMPTY_ESPELHO_PAGE_HTML), ResultWriter(tmp_path)).export(
        BrowserSession().authenticated("ctx"), request(tmp_path)
    )

    assert result.status == ExportStatus.EMPTY
    assert result.success is True


def test_export_service_fails_wrong_or_invalid_page(tmp_path) -> None:
    for html in (WRONG_SERVER_PAGE_HTML, INVALID_PAGE_HTML):
        result = EspelhoExportService(SnapshotBrowser(html), ResultWriter(tmp_path)).export(
            BrowserSession().authenticated("ctx"), request(tmp_path)
        )
        assert result.status == ExportStatus.FAILED
        assert result.success is False
        assert result.export_path is None


def test_export_service_blocks_anti_automation(tmp_path) -> None:
    result = EspelhoExportService(SnapshotBrowser("<html>captcha</html>"), ResultWriter(tmp_path)).export(
        BrowserSession().authenticated("ctx"), request(tmp_path)
    )

    assert result.status == ExportStatus.BLOCKED
    assert result.error_code == "anti_automation"
