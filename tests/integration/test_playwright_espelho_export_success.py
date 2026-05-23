from fixtures.sigrh_espelho_export_pages import VALID_ESPELHO_PAGE_HTML
from tests.unit.test_espelho_export_service import SnapshotBrowser, request
from homologacao_ponto.models import BrowserSession, ExportStatus
from homologacao_ponto.services.espelho_export_service import EspelhoExportService
from homologacao_ponto.services.result_writer import ResultWriter


def test_route_mocked_espelho_export_success(tmp_path) -> None:
    result = EspelhoExportService(SnapshotBrowser(VALID_ESPELHO_PAGE_HTML), ResultWriter(tmp_path)).export(
        BrowserSession().authenticated("ctx"), request(tmp_path)
    )

    assert result.status == ExportStatus.COMPLETED
    assert result.export_path.endswith("espelho-maio-2026.json")
