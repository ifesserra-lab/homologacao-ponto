from homologacao_ponto.models import ResumoHorasApuradas


_EXPECTED_FIELDS = [
    "carga_horaria_contratada",
    "carga_horaria_esperada_mes",
    "total_horas_registradas",
    "total_horas_justificadas",
    "total_horas_homologadas",
    "saldo_mes_anterior_compensacao",
    "total_horas_mes_anterior_compensadas",
    "debito_mes_anterior_nao_compensado",
    "debito_mes_atual_nao_autorizado",
    "outros_debitos_nao_compensados_vencidos",
    "totalizacao_debito_nao_compensavel",
    "total_horas_pendentes_compensacao",
    "saldo_horas_mes",
    "saldo_horas_mes_compensar_proximo",
    "credito_horas_disponivel_mes",
    "credito_em_horas",
]


def test_resumo_to_dict_returns_16_fields() -> None:
    resumo = ResumoHorasApuradas(
        carga_horaria_contratada="160:00",
        carga_horaria_esperada_mes="160:00",
        total_horas_registradas="50:31",
        total_horas_justificadas="00:00",
        total_horas_homologadas="49:25",
        saldo_mes_anterior_compensacao="00:00",
        total_horas_mes_anterior_compensadas="00:00",
        debito_mes_anterior_nao_compensado="00:00",
        debito_mes_atual_nao_autorizado="-61:25",
        outros_debitos_nao_compensados_vencidos="00:00",
        totalizacao_debito_nao_compensavel="-61:25",
        total_horas_pendentes_compensacao="-09:10",
        saldo_horas_mes="-09:10",
        saldo_horas_mes_compensar_proximo="-09:10",
        credito_horas_disponivel_mes="00:00",
        credito_em_horas="00:00",
    )

    result = resumo.to_dict()

    assert len(result) == 16
    for field in _EXPECTED_FIELDS:
        assert field in result


def test_resumo_all_none_does_not_raise() -> None:
    resumo = ResumoHorasApuradas()
    result = resumo.to_dict()
    assert len(result) == 16
    for field in _EXPECTED_FIELDS:
        assert result[field] is None
