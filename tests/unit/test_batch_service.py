from unittest.mock import MagicMock

from homologacao_ponto.models.batch_config import BatchConfig, BatchEntry
from homologacao_ponto.models.batch_result import BatchResult
from homologacao_ponto.services.batch_service import BatchService


def _make_app(exit_code=0, export_path="/data/celio.json"):
    app = MagicMock()
    result = MagicMock()
    result.exit_code = exit_code
    result.result = MagicMock()
    result.result.output_path = export_path
    result.result.status = "completed"
    app._run_single_espelho.return_value = result
    return app


def _make_writer(tmp_path):
    writer = MagicMock()
    writer.output_dir = tmp_path

    def write(obj):
        import json
        p = tmp_path / obj.output_filename
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj.to_dict()), encoding="utf-8")
        return obj.with_output_path(p)

    writer.write.side_effect = write
    return writer


def test_run_two_servers_success(tmp_path):
    config = BatchConfig(
        servidores=[
            BatchEntry(nome="CELIO", siape="123", mes=5, ano=2026),
            BatchEntry(nome="OUTRO", siape="456", mes=5, ano=2026),
        ],
        mes=5,
        ano=2026,
    )
    app = _make_app(exit_code=0)
    service = BatchService(app, _make_writer(tmp_path))
    session = MagicMock()

    result = service.run(session, config, run_id="run-test")

    assert isinstance(result, BatchResult)
    assert result.total == 2
    assert result.succeeded == 2
    assert result.failed == 0
    assert all(e.status == "completed" for e in result.entries)
    assert all(e.export_path is not None for e in result.entries)
    assert app._run_single_espelho.call_count == 2


def test_run_resolves_default_period(tmp_path):
    import datetime
    now = datetime.date.today()
    config = BatchConfig(servidores=[BatchEntry(nome="X", siape="1")])
    app = _make_app()
    service = BatchService(app, _make_writer(tmp_path))
    service.run(MagicMock(), config, run_id="r1")
    _, kwargs = app._run_single_espelho.call_args
    assert kwargs.get("mes") == now.month or app._run_single_espelho.call_args[0][3] == now.month


def test_batch_result_has_timestamps(tmp_path):
    config = BatchConfig(servidores=[BatchEntry(nome="X", siape="1", mes=5, ano=2026)])
    app = _make_app()
    service = BatchService(app, _make_writer(tmp_path))
    result = service.run(MagicMock(), config, run_id="r1")
    assert result.started_at
    assert result.finished_at
    assert result.started_at <= result.finished_at


def test_partial_failure_continues(tmp_path):
    """Servidor no meio da lista falha — os outros continuam."""
    call_count = [0]

    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 2:
            raise RuntimeError("servidor não encontrado no SIGRH")
        result = MagicMock()
        result.exit_code = 0
        result.result = MagicMock()
        result.result.output_path = f"/data/s{call_count[0]}.json"
        result.result.status = "completed"
        return result

    app = MagicMock()
    app._run_single_espelho.side_effect = side_effect

    config = BatchConfig(
        servidores=[
            BatchEntry(nome="S1", siape="1", mes=5, ano=2026),
            BatchEntry(nome="S2", siape="2", mes=5, ano=2026),
            BatchEntry(nome="S3", siape="3", mes=5, ano=2026),
        ],
    )
    service = BatchService(app, _make_writer(tmp_path))
    result = service.run(MagicMock(), config, run_id="r-fail")

    assert result.total == 3
    assert result.succeeded == 2
    assert result.failed == 1
    assert result.entries[1].status == "failed"
    assert result.entries[1].error is not None
    assert result.entries[0].status == "completed"
    assert result.entries[2].status == "completed"


def test_failed_batch_exit_nonzero(tmp_path):
    """BatchResult com failed > 0 indica falha."""
    app = _make_app(exit_code=4)  # exit_code != 0 → falha
    service = BatchService(app, _make_writer(tmp_path))
    config = BatchConfig(servidores=[BatchEntry(nome="X", siape="1", mes=5, ano=2026)])
    result = service.run(MagicMock(), config, run_id="r-err")
    assert result.failed == 1
    assert result.succeeded == 0


def test_session_expired_retries(tmp_path):
    """Sessão expirada (exit_code=6) → reautentica e retenta."""
    retry_count = [0]
    success_result = MagicMock()
    success_result.exit_code = 0
    success_result.result = MagicMock()
    success_result.result.output_path = "/data/ok.json"
    success_result.result.status = "completed"

    expired_result = MagicMock()
    expired_result.exit_code = 6
    expired_result.result = None

    def side_effect(*args, **kwargs):
        retry_count[0] += 1
        if retry_count[0] == 1:
            return expired_result
        return success_result

    app = MagicMock()
    app._run_single_espelho.side_effect = side_effect
    new_session = MagicMock()
    login_result = MagicMock()
    login_result.success = True
    login_result.browser_session = new_session
    app.auth_service.login.return_value = login_result
    app.credential_provider.load.return_value = MagicMock()

    config = BatchConfig(servidores=[BatchEntry(nome="X", siape="1", mes=5, ano=2026)])
    service = BatchService(app, _make_writer(tmp_path))
    result = service.run(MagicMock(), config, run_id="r-retry")

    assert result.succeeded == 1
    assert result.failed == 0
    assert app._run_single_espelho.call_count == 2
