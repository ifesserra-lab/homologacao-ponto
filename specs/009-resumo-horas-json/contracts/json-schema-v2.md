# Contract: JSON Schema v2 — Campo `resumo`

## Mudanças em relação ao v1

| Campo | v1 | v2 |
|-------|----|----|
| `schema_version` | `1` | `2` |
| `resumo` | ausente | `object \| null` |

## Objeto `resumo`

Todos os campos são `string \| null`. Formato: `"HH:MM"` ou `"-HH:MM"`.

```
resumo.carga_horaria_contratada           "160:00"
resumo.carga_horaria_esperada_mes         "160:00"
resumo.total_horas_registradas            "50:31"
resumo.total_horas_justificadas           "00:00"
resumo.total_horas_homologadas            "49:25"
resumo.saldo_mes_anterior_compensacao     "00:00"
resumo.total_horas_mes_anterior_compensadas "00:00"
resumo.debito_mes_anterior_nao_compensado "00:00"
resumo.debito_mes_atual_nao_autorizado    "-61:25"
resumo.outros_debitos_nao_compensados_vencidos "00:00"
resumo.totalizacao_debito_nao_compensavel "-61:25"
resumo.total_horas_pendentes_compensacao  "-09:10"
resumo.saldo_horas_mes                    "-09:10"
resumo.saldo_horas_mes_compensar_proximo  "-09:10"
resumo.credito_horas_disponivel_mes       "00:00"
resumo.credito_em_horas                   "00:00"
```

## Regras

- `resumo: null` quando seção "Resumo das Horas Apuradas no Mês" não estava visível.
- Campos individuais `null` quando o SIGRH não renderizou aquela linha.
- Valores negativos preservados com sinal: `"-09:10"`, nunca `"09:10"` com flag separado.
- Valores zero: `"00:00"` explícito, nunca `null`.

## Retro-compatibilidade

Consumidores devem tratar `resumo` ausente (v1) como `null`.
