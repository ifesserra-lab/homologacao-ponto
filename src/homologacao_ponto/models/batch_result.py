from __future__ import annotations
from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class BatchEntryResult:
    nome: str
    siape: str
    status: str  # "completed" | "empty" | "failed" | "blocked"
    export_path: str | None = None
    error: str | None = None
    mes: int | None = None
    ano: int | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "nome": self.nome,
            "siape": self.siape,
            "status": self.status,
            "export_path": self.export_path,
            "error": self.error,
        }
        if self.mes is not None:
            d["mes"] = self.mes
        if self.ano is not None:
            d["ano"] = self.ano
        return d


@dataclass(frozen=True)
class BatchResult:
    """Resultado imutável de uma execução de batch."""

    run_id: str
    started_at: str
    finished_at: str
    total: int
    succeeded: int
    failed: int
    entries: list[BatchEntryResult]
    output_path: str | None = None

    @property
    def output_filename(self) -> str:
        """Nome canônico do arquivo de saída: ``batch-result-<run_id>.json``.

        O prefixo ``batch-result-`` distingue estes arquivos de outros JSONs no
        mesmo diretório de saída (e.g., resultados individuais por servidor).
        """
        return f"batch-result-{self.run_id}.json"

    @property
    def output_subdir(self) -> str:
        return "logging"

    def with_output_path(self, path: Path) -> "BatchResult":
        return replace(self, output_path=str(path))

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "total": self.total,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "output_path": self.output_path,
            "entries": [e.to_dict() for e in self.entries],
        }
