import json

from fixtures.sigrh_espelho_export_pages import VALID_ESPELHO_PAGE_HTML
from tests.unit.test_espelho_export_service import SnapshotBrowser, request
from homologacao_ponto.models import BrowserSession
from homologacao_ponto.services.espelho_export_service import EspelhoExportService
from homologacao_ponto.services.result_writer import ResultWriter


def test_espelho_export_result_persistence(tmp_path) -> None:
    result = EspelhoExportService(SnapshotBrowser(VALID_ESPELHO_PAGE_HTML), ResultWriter(tmp_path)).export(
        BrowserSession().authenticated("ctx"), request(tmp_path)
    )

    data = json.loads((tmp_path / result.output_filename).read_text(encoding="utf-8"))
    assert data["success"] is True
    assert data["export_path"].endswith("espelho-maio-2026.json")
