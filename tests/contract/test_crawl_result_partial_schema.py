import json
from pathlib import Path

import pytest

from homologacao_ponto.models import CrawlResult, CrawlStatus

jsonschema = pytest.importorskip("jsonschema")


def test_partial_results_match_schema() -> None:
    schema = json.loads(Path("specs/001-login-sigrh/contracts/crawl-result.schema.json").read_text(encoding="utf-8"))

    session_expired = CrawlResult("paulo", 1, [], CrawlStatus.PARTIAL, "BrowserSession expirada")
    page_cap = CrawlResult("paulo", 20, [], CrawlStatus.PARTIAL, "limite de páginas atingido")

    jsonschema.validate(session_expired.to_dict(), schema)
    jsonschema.validate(page_cap.to_dict(), schema)

