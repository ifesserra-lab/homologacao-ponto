
from homologacao_ponto.infrastructure.credential_provider import CredentialProvider
from homologacao_ponto.models import CredentialSource


def test_credential_provider_loads_env_file(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("SIGRH_USERNAME", raising=False)
    monkeypatch.delenv("SIGRH_PASSWORD", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("SIGRH_USERNAME=paulo\nSIGRH_PASSWORD=secret\n", encoding="utf-8")

    credential = CredentialProvider(env_file).load()

    assert credential.username == "paulo"
    assert credential.password == "secret"
    assert credential.source == CredentialSource.ENV


def test_credential_provider_prompts_when_env_missing(monkeypatch) -> None:
    monkeypatch.delenv("SIGRH_USERNAME", raising=False)
    monkeypatch.delenv("SIGRH_PASSWORD", raising=False)

    credential = CredentialProvider(
        env_file="missing.env",
        input_func=lambda _: "paulo",
        password_func=lambda _: "secret",
    ).load()

    assert credential.source == CredentialSource.INTERACTIVE
    assert not credential.consent_to_persist

