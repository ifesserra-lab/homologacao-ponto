import json
from pathlib import Path

import pytest

from homologacao_ponto.models import CrawlResult
from homologacao_ponto.services.result_writer import ResultWriter

jsonschema = pytest.importorskip("jsonschema")


def _schema() -> dict:
    return json.loads(Path("specs/001-login-sigrh/contracts/crawl-result.schema.json").read_text(encoding="utf-8"))


def test_completed_result_matches_schema(tmp_path) -> None:
    result = ResultWriter(tmp_path).write(
        CrawlResult("paulo", 1, message="nenhum registro encontrado")
    )

    jsonschema.validate(result.to_dict(), _schema())


def test_empty_result_has_required_message_and_empty_records(tmp_path) -> None:
    result = ResultWriter(tmp_path).write(
        CrawlResult("paulo", 1, message="nenhum registro encontrado")
    )
    data = json.loads(Path(result.output_path).read_text(encoding="utf-8"))

    assert data["record_count"] == 0
    assert data["records"] == []
    assert data["message"] == "nenhum registro encontrado"

