# Feature Specification: Período por Anos no Batch YAML

**Feature Branch**: `007-batch-periodo-anos`  
**Created**: 2026-05-23  
**Status**: Draft  
**Input**: User description: "Modificar servidores.yaml para colocar o período em anos que deseja buscar. Se colocar 2025 e 2026, busca o espelho de todos os meses de 2025 e 2026. Se colocar All, busca todos os meses de trabalho do servidor."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baixar espelho de anos específicos (Priority: P1)

O operador informa uma lista de anos (ex: `anos: [2025, 2026]`) no arquivo YAML de batch. O sistema baixa o espelho de ponto de todos os 12 meses de cada ano listado para cada servidor informado.

**Why this priority**: Caso de uso principal — baixar dados históricos de um ou mais anos completos para auditoria ou controle de frequência.

**Independent Test**: Com 1 servidor e `anos: [2025]` no YAML, verificar que o sistema gera 12 entradas no relatório (janeiro a dezembro de 2025).

**Acceptance Scenarios**:

1. **Given** YAML com `anos: [2025, 2026]` e 1 servidor, **When** operador executa batch, **Then** sistema baixa 24 espelhos e relatório contém `total: 24`.
2. **Given** YAML com `anos: [2025]` e 2 servidores, **When** operador executa batch, **Then** sistema gera 12 espelhos por servidor (24 total) em pastas separadas.
3. **Given** YAML com `anos: []` (lista vazia), **When** operador executa batch, **Then** sistema reporta erro "Campo 'anos' não pode ser lista vazia" e não inicia downloads.

---

### User Story 2 - Baixar todos os meses de trabalho do servidor (Priority: P2)

O operador informa `anos: All` no YAML. O sistema detecta o mês de início de trabalho do servidor no SIGRH e baixa o espelho de todos os meses desde a admissão até o mês corrente.

**Why this priority**: Permite extrair histórico completo sem o operador precisar saber a data de admissão de cada servidor.

**Independent Test**: Com `anos: All` e 1 servidor, verificar que relatório contém entradas desde o primeiro mês disponível até o mês corrente.

**Acceptance Scenarios**:

1. **Given** YAML com `anos: All` e servidor com primeiro espelho em março/2020, **When** batch executado em maio/2026, **Then** sistema gera entradas de março/2020 até maio/2026.
2. **Given** YAML com `anos: All` e SIGRH não retorna data de início, **When** operador executa batch, **Then** servidor é marcado como falha com mensagem "período de trabalho não detectado" e lote continua.
3. **Given** YAML com `anos: All` e mês sem espelho disponível, **When** sistema tenta baixar, **Then** entrada registrada como `empty` ou `failed` sem abortar lote.

---

### User Story 3 - Compatibilidade com formato anterior (Priority: P3)

Quando o YAML usa apenas `mes` e `ano` (sem campo `anos`), o comportamento continua idêntico à feature 006.

**Why this priority**: Evita quebra de compatibilidade para operadores que já usam o formato atual.

**Independent Test**: YAML com `mes: 5` e `ano: 2026` sem campo `anos` gera exatamente 1 espelho por servidor.

**Acceptance Scenarios**:

1. **Given** YAML sem campo `anos`, com `mes: 5` e `ano: 2026`, **When** operador executa batch, **Then** sistema baixa 1 espelho por servidor, sem mudança de comportamento.
2. **Given** YAML com `anos: [2025]` e `mes: 5` e `ano: 2026` simultaneamente, **When** operador executa batch, **Then** `anos` tem precedência; sistema loga aviso "campo 'mes'/'ano' ignorado quando 'anos' está presente".

---

### Edge Cases

- O que acontece com `anos: [2025, 2025]` (ano duplicado)? Sistema deduplica automaticamente.
- O que acontece com meses futuros dentro de um ano listado? Ignorados — sistema processa apenas até o mês corrente.
- O que acontece quando SIGRH não tem espelho para um mês passado (servidor sem vínculo)? Registrado como `empty` ou `failed` sem abortar lote.
- O que acontece com `anos: [1900]` (ano absurdo/fora de range)? Sistema reporta erro de validação antes de iniciar.

### Testability Requirements

- Cada user story DEVE ter teste independente sem depender dos outros stories.
- Testes com `anos: All` DEVEM usar data corrente fixa (mock) para garantir determinismo.
- Cenários negativos (lista vazia, valor inválido, SIGRH sem data de admissão) DEVEM ter testes de caminho negativo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O arquivo YAML DEVE aceitar campo `anos` como lista de inteiros (ex: `[2025, 2026]`) ou valor literal `"All"`.
- **FR-002**: Quando `anos` contém lista de inteiros, sistema DEVE expandir para todos os meses de cada ano e executar batch para cada combinação servidor × mês × ano.
- **FR-003**: Meses futuros (após mês corrente) dentro de um ano listado DEVEM ser ignorados automaticamente.
- **FR-004**: Anos duplicados em `anos` DEVEM ser deduplizados antes de expansão.
- **FR-005**: `anos: []` DEVE resultar em erro de validação com mensagem clara antes de iniciar qualquer download.
- **FR-006**: `anos` inválido (ex: inteiro fora de range razoável) DEVE resultar em erro de validação.
- **FR-007**: Quando `anos: All`, sistema DEVE detectar o primeiro mês com espelho disponível para o servidor no SIGRH e expandir período desde esse mês até o mês corrente.
- **FR-008**: Quando `anos: All` e data de início não detectável, sistema DEVE registrar falha por servidor e continuar o lote.
- **FR-009**: Quando `anos` presente junto com `mes`/`ano`, `anos` DEVE ter precedência e sistema DEVE registrar aviso no log.
- **FR-010**: Sem campo `anos`, comportamento DEVE ser idêntico à feature 006 (compatibilidade total).
- **FR-011**: Relatório consolidado DEVE refletir total expandido (N servidores × M períodos).

### Key Entities

- **BatchConfig** (modificado): Recebe campo opcional `anos` (lista de inteiros ou literal `"All"`).
- **BatchPeriodo**: Lista de `(mes: int, ano: int)` gerada internamente a partir de `anos` ou `mes`/`ano`.
- **AdmissaoDetector**: Responsável por detectar primeiro mês disponível para servidor quando `anos: All`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Com `anos: [2025, 2026]` e 1 servidor, relatório gerado com `total: 24` sem intervenção manual.
- **SC-002**: Com `anos: All`, sistema detecta período de trabalho e expande automaticamente sem entrada adicional do operador.
- **SC-003**: YAMLs existentes sem campo `anos` funcionam sem modificação — 100% de compatibilidade reversa.
- **SC-004**: Falhas em meses individuais não interrompem o lote — 100% de continuação após falha parcial.
- **SC-005**: Relatório consolidado contém `total`, `succeeded` e `failed` corretos para lotes expandidos.

## Assumptions

- SIGRH exibe espelho mês a mês; não existe endpoint de múltiplos meses em uma única requisição.
- Para `anos: All`, o primeiro mês disponível é inferido tentando espelhos mês a mês em ordem decrescente até encontrar "espelho não disponível" ou usando data de admissão visível na tela do SIGRH.
- Meses futuros não têm espelho disponível no SIGRH.
- A ordem de processamento é: servidor por servidor, meses em ordem cronológica crescente.
- Anos válidos estão no intervalo 2000–2099 (anos fora desse intervalo são rejeitados na validação).
