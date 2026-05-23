from __future__ import annotations

import json
from pathlib import Path

from homologacao_ponto.models import CrawlResult, EspelhoPontoExport, ExportacaoEspelhoResult, NavigationResult, SelecaoServidorResult


class ResultWriteError(RuntimeError):
    pass


class ResultWriter:
    def __init__(self, output_dir: Path | str = "data/runs") -> None:
        self.output_dir = Path(output_dir)

    def write(
        self, result: CrawlResult | NavigationResult | SelecaoServidorResult | EspelhoPontoExport | ExportacaoEspelhoResult
    ) -> CrawlResult | NavigationResult | SelecaoServidorResult | EspelhoPontoExport | ExportacaoEspelhoResult:
        subdir = getattr(result, "output_subdir", None)
        output_path = (
            self.output_dir / subdir / result.output_filename
            if subdir
            else self.output_dir / result.output_filename
        )
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            persisted = result.with_output_path(output_path)
            output_path.write_text(
                json.dumps(persisted.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return persisted
        except OSError as exc:
            raise ResultWriteError(f"arquivo JSON local não pôde ser escrito: {exc}") from exc
