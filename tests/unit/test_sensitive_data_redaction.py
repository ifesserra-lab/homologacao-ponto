import json

from homologacao_ponto.infrastructure import redact_sensitive
from homologacao_ponto.models import CrawlResult


def test_logs_and_json_do_not_include_password() -> None:
    assert "secret" not in redact_sensitive("password=secret")
    result_json = json.dumps(
        CrawlResult("paulo", 1, message="nenhum registro encontrado").to_dict()
    )
    assert "secret" not in result_json
    assert "SIGRH_PASSWORD" not in result_json

