import json

import pytest

from homologacao_ponto.models import SelecaoServidorResult, SelectionStatus
from homologacao_ponto.services.result_writer import ResultWriteError, ResultWriter


def _completed_result() -> SelecaoServidorResult:
    return SelecaoServidorResult(
        username_ref="paulo",
        requested_server="Celio Proliciano Maioli",
        status=SelectionStatus.COMPLETED,
        final_step="Servidor Selecionado",
        selected_server="CELIO PROLICIANO MAIOLI",
    )


def test_result_writer_writes_selection_json(tmp_path) -> None:
    persisted = ResultWriter(tmp_path).write(_completed_result())
    data = json.loads((tmp_path / persisted.output_filename).read_text(encoding="utf-8"))

    assert data["status"] == "completed"
    assert data["output_path"] == str(tmp_path / persisted.output_filename)


def test_result_writer_reports_selection_write_failure(tmp_path) -> None:
    output_dir = tmp_path / "not-a-dir"
    output_dir.write_text("blocked", encoding="utf-8")

    with pytest.raises(ResultWriteError):
        ResultWriter(output_dir).write(_completed_result())
