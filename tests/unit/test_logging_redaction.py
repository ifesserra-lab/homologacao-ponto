from homologacao_ponto.infrastructure import redact_sensitive


def test_redact_sensitive_values() -> None:
    rendered = redact_sensitive("SIGRH_PASSWORD=secret cookie=abc password: top")

    assert "secret" not in rendered
    assert "abc" not in rendered
    assert "top" not in rendered
    assert "***" in rendered

