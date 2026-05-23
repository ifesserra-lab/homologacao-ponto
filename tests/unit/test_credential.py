import pytest

from homologacao_ponto.models import Credential, CredentialSource


def test_credential_requires_username_and_password() -> None:
    with pytest.raises(ValueError):
        Credential("", "secret")
    with pytest.raises(ValueError):
        Credential("paulo", "")


def test_credential_repr_redacts_password() -> None:
    credential = Credential("paulo", "super-secret", CredentialSource.INTERACTIVE)

    rendered = repr(credential)

    assert "paulo" in rendered
    assert "super-secret" not in rendered
    assert "***" in rendered

