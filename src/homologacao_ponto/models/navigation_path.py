from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


CANONICAL_NAVIGATION_LABELS = [
    "Chefia de Unidade",
    "Homologacao de Ponto Eletronico",
    "Relatorio",
    "Espelho do Ponto",
]


def normalize_navigation_label(label: str) -> str:
    normalized = unicodedata.normalize("NFKD", label)
    ascii_label = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", ascii_label).strip().casefold()


@dataclass(frozen=True)
class NavigationPath:
    labels: list[str] = field(default_factory=lambda: list(CANONICAL_NAVIGATION_LABELS))
    destination_label: str = "Espelho do Ponto"
    max_step_wait_seconds: int = 15

    @classmethod
    def default(cls) -> NavigationPath:
        return cls()

    def __post_init__(self) -> None:
        if self.labels != CANONICAL_NAVIGATION_LABELS:
            raise ValueError("navigation path must use the canonical SIGRH menu order")
        if self.max_step_wait_seconds != 15:
            raise ValueError("max_step_wait_seconds must be 15")

    def matches(self, expected: str, actual: str) -> bool:
        return normalize_navigation_label(expected) == normalize_navigation_label(
            actual
        )
