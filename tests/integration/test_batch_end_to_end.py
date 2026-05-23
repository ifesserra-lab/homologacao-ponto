import json

from fixtures.sigrh_espelho_export_pages import VALID_ESPELHO_PAGE_HTML
from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.models import BrowserSession
from homologacao_ponto.models.batch_config import BatchConfig, BatchEntry
from homologacao_ponto.services.batch_service import BatchService
from homologacao_ponto.services.espelho_export_service import EspelhoExportService
from homologacao_ponto.services.result_writer import ResultWriter


class SnapshotBrowser:
    def __init__(self, html: str) -> None:
        self.html = html

    def capture_espelho_snapshot(self):
        return SigrhPageSnapshot(
            "https://sigrh.ifes.edu.br/sigrh/frequencia/espelho.jsf",
            "Espelho",
            self.html,
            "2026-05-20T12:00:00+00:00",
        )

    @staticmethod
    def is_anti_automation(html: str) -> bool:
        return "captcha" in html.lower()

    @staticmethod
    def is_session_expired(html: str) -> bool:
        return "sessao expirada" in html.lower()


class FakeApp:
    """Fake app that skips navigation/selection and goes straight to export."""

    def __init__(self, browser, result_writer):
        self.browser = browser
        self.result_writer = result_writer
        self.espelho_export_service = None

    def _run_single_espelho(self, session, servidor, siape, mes, ano):
        from homologacao_ponto.app import AppResult
        from homologacao_ponto.services.espelho_export_service import EspelhoExportRequest

        if self.espelho_export_service is None:
            self.espelho_export_service = EspelhoExportService(self.browser, self.result_writer)

        export_result = self.espelho_export_service.export(
            session,
            EspelhoExportRequest(
                username_ref="test",
                requested_server=servidor,
                selected_server=servidor.upper(),
                selected_identifier=siape,
                output_dir=self.result_writer.output_dir,
                run_id=f"run-{siape}",
            ),
        )
        if export_result.success:
            return AppResult(0, "ok", export_result)
        return AppResult(4, "falhou", export_result)


def test_batch_creates_json_per_server(tmp_path):
    browser = SnapshotBrowser(VALID_ESPELHO_PAGE_HTML)
    writer = ResultWriter(tmp_path)
    app = FakeApp(browser, writer)
    config = BatchConfig(
        servidores=[
            BatchEntry(nome="Celio Proliciano Maioli", siape="1534589", mes=5, ano=2026),
            BatchEntry(nome="Celio Proliciano Maioli", siape="1534589", mes=4, ano=2026),
        ],
        mes=5,
        ano=2026,
    )
    session = BrowserSession().authenticated("ctx")

    result = BatchService(app, writer).run(session, config, run_id="batch-test")

    assert result.total == 2
    assert result.succeeded == 2
    assert result.failed == 0
    batch_file = tmp_path / "logging" / "batch-result-batch-test.json"
    assert batch_file.exists()
    data = json.loads(batch_file.read_text())
    assert data["total"] == 2
    assert data["succeeded"] == 2


def test_batch_result_file_written(tmp_path):
    browser = SnapshotBrowser(VALID_ESPELHO_PAGE_HTML)
    writer = ResultWriter(tmp_path)
    app = FakeApp(browser, writer)
    config = BatchConfig(
        servidores=[BatchEntry(nome="Celio Proliciano Maioli", siape="1534589", mes=5, ano=2026)],
    )
    session = BrowserSession().authenticated("ctx")
    BatchService(app, writer).run(session, config, run_id="r99")
    assert (tmp_path / "logging" / "batch-result-r99.json").exists()


def test_batch_result_has_timestamps(tmp_path):
    import re
    ISO_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    browser = SnapshotBrowser(VALID_ESPELHO_PAGE_HTML)
    writer = ResultWriter(tmp_path)
    app = FakeApp(browser, writer)
    config = BatchConfig(
        servidores=[BatchEntry(nome="Celio Proliciano Maioli", siape="1534589", mes=5, ano=2026)],
    )
    result = BatchService(app, writer).run(BrowserSession().authenticated("ctx"), config, run_id="ts-test")
    assert ISO_RE.match(result.started_at)
    assert ISO_RE.match(result.finished_at)
    assert result.started_at <= result.finished_at


def test_batch_result_written_even_with_total_failure(tmp_path):
    """Relatório sempre gerado mesmo quando todos os servidores falham."""
    from unittest.mock import MagicMock

    app = MagicMock()
    fail_result = MagicMock()
    fail_result.exit_code = 4
    fail_result.result = None
    fail_result.message = "servidor não encontrado"
    app._run_single_espelho.return_value = fail_result

    writer = ResultWriter(tmp_path)
    config = BatchConfig(
        servidores=[
            BatchEntry(nome="X", siape="1", mes=5, ano=2026),
            BatchEntry(nome="Y", siape="2", mes=5, ano=2026),
        ],
    )
    result = BatchService(app, writer).run(MagicMock(), config, run_id="all-fail")
    assert result.total == 2
    assert result.failed == 2
    assert result.succeeded == 0
    assert (tmp_path / "logging" / "batch-result-all-fail.json").exists()
