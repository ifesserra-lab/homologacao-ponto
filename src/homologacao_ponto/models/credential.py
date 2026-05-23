from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CredentialSource(StrEnum):
    ENV = "env"
    INTERACTIVE = "interactive"


@dataclass(frozen=True)
class Credential:
    username: str
    password: str
    source: CredentialSource = CredentialSource.ENV
    consent_to_persist: bool = False

    def __post_init__(self) -> None:
        if not self.username or not self.username.strip():
            raise ValueError("username is required")
        if not self.password:
            raise ValueError("password is required")

    def __repr__(self) -> str:
        return (
            "Credential("
            f"username={self.username!r}, password='***', "
            f"source={self.source.value!r}, "
            f"consent_to_persist={self.consent_to_persist!r})"
        )

    def username_ref(self) -> str:
        return self.username
