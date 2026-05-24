# Feature Specification: Resumo das Horas Apuradas no JSON do Mês

**Feature Branch**: `009-resumo-horas-json`  
**Created**: 2026-05-23  
**Status**: Draft  
**Input**: User description: "adicione os dados do Resumo das Horas Apuradas no Mês no json que representa o mes. com todo os campos"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capturar Resumo Completo do SIGRH (Priority: P1)

Um operador executa a exportação do espelho de ponto de um servidor. O sistema captura todos os campos da seção "Resumo das Horas Apuradas no Mês" exibida pelo SIGRH e os persiste no arquivo JSON do mês, junto com os registros diários já existentes.

**Why this priority**: Sem esses dados, o dashboard precisa aproximar valores (carga esperada, saldo, débitos não compensáveis) que o próprio SIGRH já calcula. Capturar diretamente elimina divergências e é a fonte da verdade.

**Independent Test**: Executar exportação de um mês com resumo visível no SIGRH. O JSON gerado deve conter o objeto `resumo` com todos os 16 campos preenchidos com os valores exatos exibidos na tela.

**Acceptance Scenarios**:

1. **Given** um mês com registros e resumo visível no SIGRH, **When** o scraper exporta o espelho, **Then** o JSON contém o objeto `resumo` com todos os campos da seção "Resumo das Horas Apuradas no Mês".
2. **Given** um mês onde a seção de resumo não está disponível (ex: mês vazio), **When** o scraper exporta, **Then** o JSON contém `"resumo": null` sem falhar.
3. **Given** um campo do resumo com valor `00:00`, **When** exportado, **Then** o valor é persistido como `"00:00"` (não omitido nem convertido).
4. **Given** um campo do resumo com valor negativo `-09:10`, **When** exportado, **Then** o valor é persistido como `"-09:10"` mantendo o sinal.

---

### User Story 2 - Dashboard usa valores do Resumo diretamente (Priority: P2)

O dashboard lê os valores do objeto `resumo` do JSON e os exibe na página de detalhe do mês, substituindo os cálculos aproximados atuais pelos valores exatos do SIGRH.

**Why this priority**: Melhora a confiabilidade. Valores como "Carga Horária Esperada", "Horas Homologadas" e "Falta compensar" passam a vir diretamente do SIGRH.

**Independent Test**: Abrir a página de detalhe de um mês no dashboard após re-exportação com resumo. Os stats devem bater exatamente com os valores do SIGRH.

**Acceptance Scenarios**:

1. **Given** um JSON com `resumo` preenchido, **When** o dashboard carrega a página do mês, **Then** os stats exibem os valores do `resumo` sem recalcular.
2. **Given** um JSON com `resumo: null` (dado legado), **When** o dashboard carrega, **Then** stats usam fallback de cálculo atual sem quebrar.

---

### Edge Cases

- Mês em andamento: campos com valor `00:00` ou parcialmente preenchidos devem ser preservados como estão.
- Campos ausentes na tela do SIGRH: persistir como `null`.
- Valores negativos nos campos de débito: preservar o sinal `-`.
- Meses antigos exportados sem `resumo`: retrocompatibilidade com `resumo: null`.

### Testability Requirements

- Teste unitário verificando parsing e mapeamento de cada campo do resumo.
- Teste de integração verificando que o scraper captura e persiste o objeto `resumo`.
- Teste do dashboard verificando exibição dos valores e funcionamento do fallback.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O scraper DEVE capturar todos os 16 campos da seção "Resumo das Horas Apuradas no Mês" ao exportar um espelho.
- **FR-002**: Os campos DEVEM ser persistidos num objeto `resumo` no nível raiz do JSON (junto com `registros`, `servidor`, etc.).
- **FR-003**: Se a seção de resumo não estiver disponível, o sistema DEVE persistir `"resumo": null` sem falhar.
- **FR-004**: Valores negativos (ex: `-09:10`) DEVEM ser preservados com o sinal.
- **FR-005**: Valores `00:00` DEVEM ser persistidos explicitamente, não omitidos.
- **FR-006**: O dashboard DEVE usar os valores de `resumo` quando disponíveis, com fallback para cálculo aproximado quando `resumo` for `null`.
- **FR-007**: O `schema_version` do JSON DEVE ser incrementado para 2 para indicar a presença do campo `resumo`.
- **FR-008**: JSONs sem `resumo` (schema_version 1) DEVEM continuar funcionando no dashboard.

### Key Entities

- **ResumoHorasApuradas**: Objeto com os 16 campos do resumo mensal:
  - `carga_horaria_contratada`: carga horária contratada do servidor
  - `carga_horaria_esperada_mes`: carga esperada para o mês (dias úteis × jornada)
  - `total_horas_registradas`: total bruto de horas registradas no relógio
  - `total_horas_justificadas`: horas cobertas por justificativas/abonos
  - `total_horas_homologadas`: horas homologadas pelo SIGRH (crédito efetivo)
  - `saldo_mes_anterior_compensacao`: saldo do mês anterior disponível para compensar
  - `total_horas_mes_anterior_compensadas`: quanto do saldo anterior foi compensado neste mês
  - `debito_mes_anterior_nao_compensado`: débito do mês anterior não compensado
  - `debito_mes_atual_nao_autorizado`: débito do mês atual fora da janela de compensação
  - `outros_debitos_nao_compensados_vencidos`: outros débitos vencidos sem compensação
  - `totalizacao_debito_nao_compensavel`: soma total dos débitos não compensáveis
  - `total_horas_pendentes_compensacao`: horas pendentes de compensação
  - `saldo_horas_mes`: saldo final de horas do mês
  - `saldo_horas_mes_compensar_proximo`: saldo a compensar até o próximo mês
  - `credito_horas_disponivel_mes`: crédito disponível no mês
  - `credito_em_horas`: crédito em horas acumulado

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos 16 campos do resumo são capturados quando a seção está visível no SIGRH.
- **SC-002**: Os valores exibidos no dashboard batem 100% com os valores da tela do SIGRH para meses com `resumo` preenchido.
- **SC-003**: JSONs sem `resumo` continuam carregando no dashboard sem erros.
- **SC-004**: Nenhuma regressão nos 27 testes unitários e 2 testes de integração existentes.

## Assumptions

- A seção "Resumo das Horas Apuradas no Mês" está sempre na mesma posição da página do SIGRH para meses com registros.
- Os rótulos dos campos no SIGRH são estáveis entre versões.
- O formato dos valores é sempre `HH:MM` ou `-HH:MM`.
- Meses sem registros (status `empty`) não exibem a seção; `resumo: null` é correto.
- `schema_version` 1→2 é suficiente para sinalizar a presença do novo campo.
