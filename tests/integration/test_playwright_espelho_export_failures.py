from fixtures.sigrh_espelho_export_pages import INVALID_PAGE_HTML, WRONG_SERVER_PAGE_HTML
from tests.unit.test_espelho_export_service import SnapshotBrowser, request
from homologacao_ponto.models import BrowserSession, ExportStatus
from homologacao_ponto.services.espelho_export_service import EspelhoExportService
from homologacao_ponto.services.result_writer import ResultWriter


def test_route_mocked_espelho_export_invalid_page_failure(tmp_path) -> None:
    result = EspelhoExportService(SnapshotBrowser(INVALID_PAGE_HTML), ResultWriter(tmp_path)).export(
        BrowserSession().authenticated("ctx"), request(tmp_path)
    )

    assert result.status == ExportStatus.FAILED
    assert result.error_code == "invalid_page"


def test_route_mocked_espelho_export_wrong_server_failure(tmp_path) -> None:
    result = EspelhoExportService(SnapshotBrowser(WRONG_SERVER_PAGE_HTML), ResultWriter(tmp_path)).export(
        BrowserSession().authenticated("ctx"), request(tmp_path)
    )

    assert result.status == ExportStatus.FAILED
    assert result.error_code == "wrong_server"
