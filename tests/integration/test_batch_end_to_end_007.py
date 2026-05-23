"""Integration tests for batch with anos expansion (feature 007)."""

import json
import datetime

from homologacao_ponto.app import AppResult
from homologacao_ponto.models import BrowserSession
from homologacao_ponto.models.batch_config import BatchConfig, BatchEntry
from homologacao_ponto.services.batch_service import BatchService
from homologacao_ponto.services.result_writer import ResultWriter


class SuccessFakeApp:
    """Fake app that always returns success for any period."""

    def __init__(self, result_writer: ResultWriter) -> None:
        self.result_writer = result_writer
        self.calls: list[tuple] = []

    def _run_single_espelho(self, session, servidor, siape, mes, ano):
        self.calls.append((servidor, siape, mes, ano))
        fake_result = _FakeExportResult(servidor=servidor, mes=mes, ano=ano)
        return AppResult(0, "ok", fake_result)


class _FakeExportResult:
    def __init__(self, servidor: str, mes: int, ano: int) -> None:
        self.output_path = f"/fake/{servidor}/{mes:02d}-{ano}.json"
        self.status = _FakeStatus("completed")


class _FakeStatus:
    def __init__(self, value: str) -> None:
        self.value = value


SESSION = BrowserSession().authenticated("ctx")


def test_batch_anos_single_year_generates_12_entries(tmp_path):
    writer = ResultWriter(tmp_path)
    app = SuccessFakeApp(writer)
    config = BatchConfig(
        servidores=[BatchEntry(nome="CELIO", siape="123")],
        anos=[2025],
    )
    result = BatchService(app, writer).run(SESSION, config, run_id="r007")

    assert result.total == 12
    assert result.succeeded == 12
    assert result.failed == 0
    assert all(e.ano == 2025 for e in result.entries)
    assert [e.mes for e in result.entries] == list(range(1, 13))


def test_batch_anos_entries_have_mes_ano_populated(tmp_path):
    writer = ResultWriter(tmp_path)
    app = SuccessFakeApp(writer)
    config = BatchConfig(
        servidores=[BatchEntry(nome="CELIO", siape="123")],
        anos=[2025],
    )
    result = BatchService(app, writer).run(SESSION, config, run_id="r007b")
    for entry in result.entries:
        assert entry.mes is not None
        assert entry.ano is not None


def test_batch_anos_two_years_excludes_future(tmp_path):
    writer = ResultWriter(tmp_path)
    app = SuccessFakeApp(writer)
    today = datetime.date(2026, 5, 23)
    # patch PeriodoExpander to use fixed today
    from homologacao_ponto.services import batch_service as bs_mod

    original = bs_mod.PeriodoExpander.expand

    def patched_expand(config, entry, today_arg):
        return original(config, entry, today)

    bs_mod.PeriodoExpander.expand = staticmethod(patched_expand)
    try:
        config = BatchConfig(
            servidores=[BatchEntry(nome="CELIO", siape="123")],
            anos=[2025, 2026],
        )
        result = BatchService(app, writer).run(SESSION, config, run_id="r007c")
        # 2025: 12 months + 2026: jan-may = 5 months
        assert result.total == 17
    finally:
        bs_mod.PeriodoExpander.expand = staticmethod(original)


def test_batch_anos_report_file_written(tmp_path):
    writer = ResultWriter(tmp_path)
    app = SuccessFakeApp(writer)
    config = BatchConfig(
        servidores=[BatchEntry(nome="CELIO", siape="123")],
        anos=[2025],
    )
    BatchService(app, writer).run(SESSION, config, run_id="r007d")
    assert (tmp_path / "logging" / "batch-result-r007d.json").exists()
    data = json.loads((tmp_path / "logging" / "batch-result-r007d.json").read_text())
    assert data["total"] == 12
    # entries have mes/ano in JSON
    assert data["entries"][0]["mes"] == 1
    assert data["entries"][0]["ano"] == 2025


def test_batch_anos_all_uses_admissao_detector(tmp_path):
    """US2: anos=All calls AdmissaoDetector and processes detected periods."""
    writer = ResultWriter(tmp_path)
    app = SuccessFakeApp(writer)
    config = BatchConfig(
        servidores=[BatchEntry(nome="CELIO", siape="123")],
        anos="All",
    )
    # Patch AdmissaoDetector.detect to return fixed periods
    from homologacao_ponto.infrastructure.admissao_detector import AdmissaoDetector

    def fake_detect(self, _app, session, entry, today):
        return [(3, 2026), (4, 2026), (5, 2026)]

    original = AdmissaoDetector.detect
    AdmissaoDetector.detect = fake_detect
    try:
        result = BatchService(app, writer).run(SESSION, config, run_id="r007all")
        assert result.total == 3
        assert result.succeeded == 3
        assert [e.mes for e in result.entries] == [3, 4, 5]
        assert all(e.ano == 2026 for e in result.entries)
    finally:
        AdmissaoDetector.detect = original


def test_batch_anos_all_admissao_not_detected_marks_failed(tmp_path):
    """US2: AdmissaoNaoDetectadaError → entry failed, lote continues."""
    writer = ResultWriter(tmp_path)
    app = SuccessFakeApp(writer)
    config = BatchConfig(
        servidores=[
            BatchEntry(nome="CELIO", siape="123"),
            BatchEntry(nome="OUTRO", siape="456"),
        ],
        anos="All",
    )
    from homologacao_ponto.infrastructure.admissao_detector import (
        AdmissaoDetector,
        AdmissaoNaoDetectadaError,
    )

    call_count = [0]

    def fake_detect(self, _app, session, entry, today):
        call_count[0] += 1
        if entry.nome == "CELIO":
            raise AdmissaoNaoDetectadaError("período de trabalho não detectado")
        return [(5, 2026)]

    original = AdmissaoDetector.detect
    AdmissaoDetector.detect = fake_detect
    try:
        result = BatchService(app, writer).run(SESSION, config, run_id="r007err")
        assert result.total == 2  # CELIO failed (1) + OUTRO succeeded (1)
        celio_entry = next(e for e in result.entries if e.nome == "CELIO")
        outro_entry = next(e for e in result.entries if e.nome == "OUTRO")
        assert celio_entry.status == "failed"
        assert "não detectado" in celio_entry.error
        assert outro_entry.status == "completed"
    finally:
        AdmissaoDetector.detect = original


def test_batch_legacy_no_anos_still_works(tmp_path):
    """US3: YAML without anos behaves identically to feature 006."""
    writer = ResultWriter(tmp_path)
    app = SuccessFakeApp(writer)
    config = BatchConfig(
        servidores=[BatchEntry(nome="CELIO", siape="123")],
        mes=5,
        ano=2026,
    )
    result = BatchService(app, writer).run(SESSION, config, run_id="r007e")
    assert result.total == 1
    assert result.succeeded == 1
    assert result.entries[0].mes == 5
    assert result.entries[0].ano == 2026
