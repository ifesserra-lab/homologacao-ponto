from __future__ import annotations

import datetime

from homologacao_ponto.models.batch_config import BatchConfig, BatchEntry


class PeriodoExpander:
    @staticmethod
    def expand(
        config: BatchConfig,
        entry: BatchEntry,
        today: datetime.date,
    ) -> list[tuple[int, int]]:
        """Expande config.anos em lista de (mes, ano) em ordem cronológica.

        Retorna lista vazia quando anos=="All" — sinaliza para o BatchService
        que AdmissaoDetector deve ser usado em vez do expander estático.
        """
        anos = config.anos

        if anos is None:
            mes = entry.mes or config.mes or today.month
            ano = entry.ano or config.ano or today.year
            return [(mes, ano)]

        if isinstance(anos, str):
            return []

        periodos: list[tuple[int, int]] = []
        for ano in sorted(set(anos)):
            for mes in range(1, 13):
                if ano > today.year or (ano == today.year and mes > today.month):
                    break
                periodos.append((mes, ano))
        return periodos
