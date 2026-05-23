from pathlib import Path

import pytest

from homologacao_ponto.models import CrawlResult, EspelhoPontoExport, RegistroDiaPonto, ServidorSelecionado
from homologacao_ponto.services.result_writer import ResultWriteError, ResultWriter


def test_result_writer_surfaces_write_failure(monkeypatch, tmp_path) -> None:
    result = CrawlResult(
        username_ref="paulo",
        visited_page_count=1,
        message="nenhum registro encontrado",
    )
    monkeypatch.setattr(Path, "write_text", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("denied")))

    with pytest.raises(ResultWriteError):
        ResultWriter(tmp_path).write(result)


def test_result_writer_surfaces_export_report_write_failure(monkeypatch, tmp_path) -> None:
    result = EspelhoPontoExport(
        run_id="run-123",
        captured_at="2026-05-20T12:00:00+00:00",
        servidor=ServidorSelecionado("CELIO PROLICIANO MAIOLI"),
        registros=[RegistroDiaPonto(data="2026-05-02", marcacoes=["08:00"])],
    )
    monkeypatch.setattr(Path, "write_text", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("denied")))

    with pytest.raises(ResultWriteError):
        ResultWriter(tmp_path).write(result)
