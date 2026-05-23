from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


def normalize_server_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    ascii_value = re.sub(r"[^\w\s]", " ", ascii_value)
    return re.sub(r"\s+", " ", ascii_value).strip().casefold()


@dataclass(frozen=True)
class ServidorConsulta:
    requested_name: str
    requested_identifier: str | None = None

    def __post_init__(self) -> None:
        if not self.requested_name.strip():
            raise ValueError("requested_name is required")

    @property
    def normalized_name(self) -> str:
        return normalize_server_name(self.requested_name)


@dataclass(frozen=True)
class ServidorResultado:
    display_name: str
    identifier: str | None
    row_text: str
    selection_available: bool

    def __post_init__(self) -> None:
        if not self.display_name.strip():
            raise ValueError("display_name is required")
        if not self.row_text.strip():
            raise ValueError("row_text is required")

    @property
    def can_select(self) -> bool:
        return self.selection_available

    @property
    def normalized_row_text(self) -> str:
        return normalize_server_name(self.row_text)

    def matches(self, consulta: ServidorConsulta) -> bool:
        requested = consulta.normalized_name
        if (
            consulta.requested_identifier
            and consulta.requested_identifier not in self.row_text
        ):
            return False
        return requested in self.normalized_row_text
