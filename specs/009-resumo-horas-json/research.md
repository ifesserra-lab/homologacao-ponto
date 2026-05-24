# Research: Resumo das Horas Apuradas no JSON

## Decisão 1: Estratégia de parsing do resumo

**Decision**: Text-label matching com `_ResumoHTMLParser` separado, varrendo pares label→valor.

**Rationale**: O SIGRH renderiza o resumo como tabela HTML com células contendo rótulos em português e valores `HH:MM`. Não temos o HTML real salvo, mas os rótulos são estáveis (ex: "Carga Horária Contratada:", "Total de Horas Registradas:"). A estratégia de mapear texto de rótulo → nome de campo é resiliente a variações de ID/classe CSS e compatível com o `HTMLParser` já usado.

**Alternatives considered**:
- XPath/CSS selectors: requer BeautifulSoup ou lxml, dependência extra não justificada.
- Regex sobre o HTML completo: frágil a mudanças de formatação.
- Capturar `visible_text` e parsear como texto plano: já feito; problemático para separar valores de rótulos compostos.

---

## Decisão 2: Localização do campo `resumo` no JSON

**Decision**: Campo `resumo` no nível raiz do JSON, ao lado de `registros`.

**Rationale**: Consistente com a estrutura atual (`registros`, `servidor`, `mensagens`). O resumo é um sumário mensal independente dos registros diários.

**Alternatives considered**:
- Dentro de um objeto `metadata`: adiciona nesting sem benefício.
- Como campo separado em arquivo distinto: fragmenta os dados de um mês.

---

## Decisão 3: Modelo de dados em Python

**Decision**: `@dataclass(frozen=True) ResumoHorasApuradas` com 16 campos `str | None`, todos opcionais.

**Rationale**: Frozen dataclass garante imutabilidade como `RegistroDiaPonto`. Campos `str | None` preservam o formato original `HH:MM` ou `-HH:MM` sem conversão — consistente com todos os outros campos de tempo do modelo. Nenhum campo é obrigatório porque o SIGRH pode não exibir todos para meses parciais.

**Alternatives considered**:
- TypedDict: menos expressivo para validação de domínio.
- Converter para minutos na criação: perde o formato original; conversão já feita na aggregation do dashboard.

---

## Decisão 4: Bumping do `schema_version`

**Decision**: `schema_version` 1 → 2 no `to_dict()` quando `resumo` é não-nulo.

**Rationale**: JSONs antigos têm `schema_version: 1` e `resumo` ausente. O dashboard e outros consumidores podem usar `schema_version` para detectar disponibilidade do resumo. JSONs com `resumo: None` exportados após esta feature mantêm `schema_version: 2` para indicar que o scraper tentou capturar (mas a seção não estava disponível).

**Alternatives considered**:
- Sempre schema_version 2 independente: mais simples, adotado.
- Manter schema_version 1: confunde consumidores.

---

## Decisão 5: Fallback no dashboard

**Decision**: `aggregation.ts` usa `resumo` quando `espelho.resumo !== null`; caso contrário mantém lógica atual de cálculo.

**Rationale**: JSONs anteriores sem `resumo` devem continuar funcionando. O fallback preserva retro-compatibilidade e permite migração incremental conforme os servidores são re-exportados.

---

## Mapeamento de rótulos SIGRH → campos Python

| Rótulo SIGRH (parcial) | Campo Python |
|------------------------|-------------|
| Carga Horária Contratada | `carga_horaria_contratada` |
| Carga Horária Esperada no Mês | `carga_horaria_esperada_mes` |
| Total de Horas Registradas | `total_horas_registradas` |
| Total de Horas Justificadas | `total_horas_justificadas` |
| Total de Horas Homologadas | `total_horas_homologadas` |
| Saldo de ... Para Compensação | `saldo_mes_anterior_compensacao` |
| Total de Horas de ... Compensadas | `total_horas_mes_anterior_compensadas` |
| Débito de ... Não Compensado em | `debito_mes_anterior_nao_compensado` |
| Débito de ... Não Autorizado | `debito_mes_atual_nao_autorizado` |
| Outros Débitos Não Compensados Vencidos | `outros_debitos_nao_compensados_vencidos` |
| Totalização do Débito Não Compensável | `totalizacao_debito_nao_compensavel` |
| Total de Horas Pendentes de Compensação | `total_horas_pendentes_compensacao` |
| Saldo de Horas de ... : | `saldo_horas_mes` |
| Saldo de Horas de ... a compensar | `saldo_horas_mes_compensar_proximo` |
| Crédito de Horas Disponível em | `credito_horas_disponivel_mes` |
| Crédito em Horas | `credito_em_horas` |

Matching: normalização de texto (minúsculas, sem acentos, whitespace colapsado) + correspondência por substring dos primeiros tokens significativos do rótulo.
