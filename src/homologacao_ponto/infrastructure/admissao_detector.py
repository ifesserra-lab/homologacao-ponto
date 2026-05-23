from __future__ import annotations

import datetime

from homologacao_ponto.models.batch_config import BatchEntry


class AdmissaoNaoDetectadaError(Exception):
    """Levantada quando nenhum período de trabalho é detectado para o servidor."""


class AdmissaoDetector:
    """Detecta o período histórico de trabalho de um servidor via probe regressivo.

    Chama ``_run_single_espelho`` mês a mês a partir do mês corrente; para ao
    encontrar 3 falhas consecutivas, interpretando-as como ausência de vínculo.
    Limite máximo de MAX_ANOS_RETROATIVOS para evitar busca indefinida.
    """

    MAX_ANOS_RETROATIVOS = 30
    _CONSECUTIVE_FAIL_LIMIT = 3

    def detect(
        self,
        app,
        session,
        entry: BatchEntry,
        today: datetime.date,
    ) -> list[tuple[int, int]]:
        """Retorna lista de (mes, ano) em ordem cronológica crescente.

        Raises:
            AdmissaoNaoDetectadaError: quando nenhum período retornou sucesso.
        """
        min_ano = today.year - self.MAX_ANOS_RETROATIVOS
        success_periods: list[tuple[int, int]] = []
        consecutive_fails = 0

        mes = today.month
        ano = today.year

        while ano > min_ano or (ano == min_ano and mes >= 1):
            try:
                result = app._run_single_espelho(
                    session,
                    servidor=entry.nome,
                    siape=entry.siape,
                    mes=mes,
                    ano=ano,
                )
                if result.exit_code == 0:
                    success_periods.append((mes, ano))
                    consecutive_fails = 0
                else:
                    consecutive_fails += 1
                    if consecutive_fails >= self._CONSECUTIVE_FAIL_LIMIT:
                        break
            except Exception:
                consecutive_fails += 1
                if consecutive_fails >= self._CONSECUTIVE_FAIL_LIMIT:
                    break

            if mes == 1:
                mes = 12
                ano -= 1
            else:
                mes -= 1

        if not success_periods:
            raise AdmissaoNaoDetectadaError(
                f"período de trabalho não detectado para {entry.nome}"
            )

        return sorted(success_periods, key=lambda p: (p[1], p[0]))
