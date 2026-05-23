"""US3: BatchService backward compatibility — anos=None behaves like feature 006."""

from unittest.mock import MagicMock

from homologacao_ponto.models.batch_config import BatchConfig, BatchEntry
from homologacao_ponto.services.batch_service import BatchService
from homologacao_ponto.services.result_writer import ResultWriter


def _fake_app(exit_code=0):
    app = MagicMock()
    result = MagicMock()
    result.exit_code = exit_code
    result.result = None
    result.message = "ok" if exit_code == 0 else "falhou"
    app._run_single_espelho.return_value = result
    return app


def test_legacy_no_anos_calls_run_single_exactly_once_per_server(tmp_path):
    app = _fake_app()
    writer = ResultWriter(tmp_path)
    config = BatchConfig(
        servidores=[
            BatchEntry(nome="CELIO", siape="123"),
            BatchEntry(nome="OUTRO", siape="456"),
        ],
        mes=5,
        ano=2026,
    )
    BatchService(app, writer).run(MagicMock(), config, run_id="leg-test")
    assert app._run_single_espelho.call_count == 2


def test_legacy_entry_result_has_correct_mes_ano(tmp_path):
    app = MagicMock()
    fake_result = MagicMock()
    fake_result.exit_code = 0
    fake_result.result = MagicMock()
    fake_result.result.output_path = "/fake/path.json"
    fake_result.result.status = MagicMock()
    fake_result.result.status.value = "completed"
    app._run_single_espelho.return_value = fake_result

    writer = ResultWriter(tmp_path)
    config = BatchConfig(
        servidores=[BatchEntry(nome="CELIO", siape="123")],
        mes=5,
        ano=2026,
    )
    result = BatchService(app, writer).run(MagicMock(), config, run_id="mes-test")
    assert result.entries[0].mes == 5
    assert result.entries[0].ano == 2026


def test_legacy_total_is_one_per_server(tmp_path):
    app = _fake_app(exit_code=0)
    writer = ResultWriter(tmp_path)
    config = BatchConfig(
        servidores=[BatchEntry(nome="CELIO", siape="123")],
        mes=5,
        ano=2026,
    )
    result = BatchService(app, writer).run(MagicMock(), config, run_id="tot-test")
    assert result.total == 1
