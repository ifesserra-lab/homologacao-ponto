from pathlib import Path
from homologacao_ponto.models.batch_result import BatchEntryResult, BatchResult


def _make_result(run_id="run-001") -> BatchResult:
    return BatchResult(
        run_id=run_id,
        started_at="2026-05-23T10:00:00+00:00",
        finished_at="2026-05-23T10:05:00+00:00",
        total=2,
        succeeded=1,
        failed=1,
        entries=[
            BatchEntryResult(nome="CELIO", siape="123", status="completed", export_path="/data/a.json"),
            BatchEntryResult(nome="OUTRO", siape="456", status="failed", error="não encontrado"),
        ],
    )


def test_output_filename():
    r = _make_result("abc123")
    assert r.output_filename == "batch-result-abc123.json"


def test_no_output_subdir():
    r = _make_result()
    assert not hasattr(r, "output_subdir") or r.output_subdir is None  # flat path no ResultWriter


def test_to_dict_top_level_keys():
    d = _make_result().to_dict()
    for key in ("run_id", "started_at", "finished_at", "total", "succeeded", "failed", "entries"):
        assert key in d, f"chave '{key}' ausente"


def test_to_dict_entries():
    d = _make_result().to_dict()
    assert len(d["entries"]) == 2
    e0 = d["entries"][0]
    assert e0["nome"] == "CELIO"
    assert e0["status"] == "completed"
    assert e0["export_path"] == "/data/a.json"
    assert e0["error"] is None
    e1 = d["entries"][1]
    assert e1["status"] == "failed"
    assert e1["error"] == "não encontrado"
    assert e1["export_path"] is None


def test_with_output_path():
    r = _make_result()
    r2 = r.with_output_path(Path("/tmp/batch-result-run-001.json"))
    assert r2.output_path == "/tmp/batch-result-run-001.json"
    assert r2.run_id == r.run_id
