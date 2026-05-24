# Data Model: Resumo das Horas Apuradas

## Novo: `ResumoHorasApuradas`

```python
@dataclass(frozen=True)
class ResumoHorasApuradas:
    carga_horaria_contratada: str | None = None
    carga_horaria_esperada_mes: str | None = None
    total_horas_registradas: str | None = None
    total_horas_justificadas: str | None = None
    total_horas_homologadas: str | None = None
    saldo_mes_anterior_compensacao: str | None = None
    total_horas_mes_anterior_compensadas: str | None = None
    debito_mes_anterior_nao_compensado: str | None = None
    debito_mes_atual_nao_autorizado: str | None = None
    outros_debitos_nao_compensados_vencidos: str | None = None
    totalizacao_debito_nao_compensavel: str | None = None
    total_horas_pendentes_compensacao: str | None = None
    saldo_horas_mes: str | None = None
    saldo_horas_mes_compensar_proximo: str | None = None
    credito_horas_disponivel_mes: str | None = None
    credito_em_horas: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "carga_horaria_contratada": self.carga_horaria_contratada,
            "carga_horaria_esperada_mes": self.carga_horaria_esperada_mes,
            "total_horas_registradas": self.total_horas_registradas,
            "total_horas_justificadas": self.total_horas_justificadas,
            "total_horas_homologadas": self.total_horas_homologadas,
            "saldo_mes_anterior_compensacao": self.saldo_mes_anterior_compensacao,
            "total_horas_mes_anterior_compensadas": self.total_horas_mes_anterior_compensadas,
            "debito_mes_anterior_nao_compensado": self.debito_mes_anterior_nao_compensado,
            "debito_mes_atual_nao_autorizado": self.debito_mes_atual_nao_autorizado,
            "outros_debitos_nao_compensados_vencidos": self.outros_debitos_nao_compensados_vencidos,
            "totalizacao_debito_nao_compensavel": self.totalizacao_debito_nao_compensavel,
            "total_horas_pendentes_compensacao": self.total_horas_pendentes_compensacao,
            "saldo_horas_mes": self.saldo_horas_mes,
            "saldo_horas_mes_compensar_proximo": self.saldo_horas_mes_compensar_proximo,
            "credito_horas_disponivel_mes": self.credito_horas_disponivel_mes,
            "credito_em_horas": self.credito_em_horas,
        }
```

## Atualização: `EspelhoPontoExport`

Novo campo opcional:
```python
resumo: ResumoHorasApuradas | None = None
```

`to_dict()` atualizado:
```python
{
    "schema_version": 2,   # bumped de 1 → 2
    ...
    "resumo": self.resumo.to_dict() if self.resumo else None,
    "registros": [...],
    ...
}
```

## JSON Schema v2 (estrutura raiz)

```json
{
  "schema_version": 2,
  "run_id": "...",
  "captured_at": "ISO datetime",
  "status": "completed | empty",
  "servidor": { "nome": "...", "identificador": "...", "texto_visivel": "..." },
  "periodo_referencia": "Maio/2026",
  "mensagens": [],
  "resumo": {
    "carga_horaria_contratada": "160:00",
    "carga_horaria_esperada_mes": "160:00",
    "total_horas_registradas": "50:31",
    "total_horas_justificadas": "00:00",
    "total_horas_homologadas": "49:25",
    "saldo_mes_anterior_compensacao": "00:00",
    "total_horas_mes_anterior_compensadas": "00:00",
    "debito_mes_anterior_nao_compensado": "00:00",
    "debito_mes_atual_nao_autorizado": "-61:25",
    "outros_debitos_nao_compensados_vencidos": "00:00",
    "totalizacao_debito_nao_compensavel": "-61:25",
    "total_horas_pendentes_compensacao": "-09:10",
    "saldo_horas_mes": "-09:10",
    "saldo_horas_mes_compensar_proximo": "-09:10",
    "credito_horas_disponivel_mes": "00:00",
    "credito_em_horas": "00:00"
  },
  "registros": [...],
  "fonte": { ... }
}
```

`resumo: null` quando seção não disponível (mês vazio ou sem acesso).

## Retro-compatibilidade

- JSON v1 (sem campo `resumo`): dashboard trata `resumo` ausente como `null` → fallback de cálculo.
- JSON v2 com `resumo: null`: mesmo comportamento que v1.
- JSON v2 com `resumo` preenchido: dashboard usa valores diretamente.
