from homologacao_ponto.infrastructure.credential_provider import CredentialProvider


def test_provider_does_not_persist_credentials_without_consent(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("SIGRH_USERNAME", raising=False)
    monkeypatch.delenv("SIGRH_PASSWORD", raising=False)

    CredentialProvider(
        env_file=tmp_path / ".env",
        input_func=lambda _: "paulo",
        password_func=lambda _: "secret",
    ).load()

    assert not any(tmp_path.iterdir())

