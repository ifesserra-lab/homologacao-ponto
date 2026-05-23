"""Contract: BatchResult.to_dict() with mes/ano validates against updated schema."""

import json
from pathlib import Path

import pytest

from homologacao_ponto.models.batch_result import BatchEntryResult, BatchResult

jsonschema = pytest.importorskip("jsonschema")

SCHEMA_PATH = (
    Path(__file__).parent.parent.parent
    / "specs/007-batch-periodo-anos/contracts/batch-result.schema.json"
)


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


def _make_result(entries):
    return BatchResult(
        run_id="abc123",
        started_at="2026-05-23T10:00:00+00:00",
        finished_at="2026-05-23T10:05:00+00:00",
        total=len(entries),
        succeeded=sum(1 for e in entries if e.status in ("completed", "empty")),
        failed=sum(1 for e in entries if e.status == "failed"),
        entries=entries,
    )


def test_schema_valid_with_mes_ano(schema):
    entries = [
        BatchEntryResult(
            nome="CELIO", siape="123", status="completed", mes=1, ano=2025
        ),
        BatchEntryResult(
            nome="CELIO", siape="123", status="completed", mes=2, ano=2025
        ),
    ]
    result = _make_result(entries)
    jsonschema.validate(result.to_dict(), schema)


def test_schema_valid_without_mes_ano_legacy(schema):
    entries = [
        BatchEntryResult(nome="CELIO", siape="123", status="completed"),
    ]
    result = _make_result(entries)
    jsonschema.validate(result.to_dict(), schema)


def test_schema_valid_mixed(schema):
    entries = [
        BatchEntryResult(
            nome="CELIO", siape="123", status="completed", mes=5, ano=2026
        ),
        BatchEntryResult(nome="CELIO", siape="123", status="failed", error="timeout"),
    ]
    result = _make_result(entries)
    jsonschema.validate(result.to_dict(), schema)
