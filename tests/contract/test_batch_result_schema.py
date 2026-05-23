import json
from pathlib import Path

import jsonschema
import pytest

from homologacao_ponto.models.batch_result import BatchEntryResult, BatchResult

SCHEMA_PATH = Path("specs/006-batch-yaml-servidores/contracts/batch-result.schema.json")


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


def _make_result(succeeded=2, failed=0) -> BatchResult:
    entries = []
    for i in range(succeeded):
        entries.append(BatchEntryResult(
            nome=f"SERVIDOR {i}",
            siape=str(1000 + i),
            status="completed",
            export_path=f"/data/servidor-{i}/espelho-maio-2026.json",
        ))
    for i in range(failed):
        entries.append(BatchEntryResult(
            nome=f"FALHOU {i}",
            siape=str(9000 + i),
            status="failed",
            error="servidor não encontrado",
        ))
    return BatchResult(
        run_id="run-schema-test",
        started_at="2026-05-23T10:00:00+00:00",
        finished_at="2026-05-23T10:05:00+00:00",
        total=succeeded + failed,
        succeeded=succeeded,
        failed=failed,
        entries=entries,
    )


def test_batch_result_validates_against_schema(schema):
    data = _make_result().to_dict()
    jsonschema.validate(data, schema)


def test_batch_result_with_failures_validates(schema):
    data = _make_result(succeeded=1, failed=1).to_dict()
    jsonschema.validate(data, schema)


def test_null_export_path_allowed(schema):
    entry = BatchEntryResult(nome="X", siape="1", status="failed", error="err")
    assert entry.to_dict()["export_path"] is None
    data = _make_result(succeeded=0, failed=1).to_dict()
    jsonschema.validate(data, schema)
