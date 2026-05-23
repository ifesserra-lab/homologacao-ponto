# Tasks: Período por Anos no Batch YAML

**Input**: `specs/007-batch-periodo-anos/`
**Prerequisites**: plan.md ✓ spec.md ✓ research.md ✓ data-model.md ✓ contracts/ ✓

**Tests**: MANDATORY — failing test before each implementation block (Constitution I).

**User Stories**:
- US1 (P1): `anos: [2025, 2026]` — expande para todos os meses de cada ano
- US2 (P2): `anos: All` — histórico completo desde primeiro espelho disponível
- US3 (P3): compatibilidade com `mes`/`ano` legado (feature 006)

---

## Phase 1: Setup

**Purpose**: Fixtures compartilhadas para todos os user stories — bloqueiam testes das fases seguintes.

- [x] T001 Criar `tests/fixtures/batch_periodo_fixtures.py`: strings YAML com `anos: [2025]`, `anos: [2025, 2026]`, `anos: "All"`, `anos: []` (inválido), `anos: ["Invalido"]` (inválido), YAML legado sem `anos`; objetos `BatchConfig` com `anos` prontos para reuso

**Checkpoint**: `from tests.fixtures.batch_periodo_fixtures import *` sem erro.

---

## Phase 2: Foundational — Modelos Modificados

**Purpose**: `BatchConfig.anos` e `BatchEntryResult.mes`/`ano` — usados por US1, US2 e US3.

### Tests (escrever primeiro — devem FALHAR antes de T004-T005)

- [x] T002 [P] Unit test `tests/unit/test_batch_config_007.py`: assert `BatchConfigLoader.load()` aceita `anos: [2025, 2026]` → `BatchConfig.anos == [2025, 2026]`; assert `anos: "All"` (case-insensitive) → `BatchConfig.anos == "All"`; assert `anos: []` → `BatchConfigError`; assert `anos: ["x"]` → `BatchConfigError`; assert `anos: [1900]` → `BatchConfigError`; assert `anos` coexistindo com `mes`/`ano` → aceito sem erro; assert YAML sem `anos` → `BatchConfig.anos is None` (compatibilidade)
- [x] T003 [P] Unit test `tests/unit/test_batch_result_007.py`: assert `BatchEntryResult(mes=5, ano=2025)` popula campos; assert `to_dict()` inclui `mes` e `ano` quando não-None; assert `BatchEntryResult()` sem `mes`/`ano` → `to_dict()` omite esses campos (compatibilidade legado)

### Implementation

- [x] T004 Modificar `src/homologacao_ponto/models/batch_config.py`: adicionar `anos: list[int] | str | None = None` ao `BatchConfig`; no `BatchConfigLoader.load()` ler `data.get("anos")`, validar (lista int range [2000,2100], string "All" case-insensitive, lista vazia → erro, string inválida → erro), deduplicar e ordenar lista; logar warning quando `anos` coexiste com `mes`/`ano` (depende de T002 vermelho)
- [x] T005 [P] Modificar `src/homologacao_ponto/models/batch_result.py`: adicionar `mes: int | None = None` e `ano: int | None = None` ao `BatchEntryResult`; atualizar `to_dict()` para incluir `mes`/`ano` somente quando não-None (depende de T003 vermelho)
- [x] T006 Verificar `src/homologacao_ponto/models/__init__.py`: nenhuma exportação nova necessária (tipos adicionados como campos, não classes novas)

**Checkpoint**: `pytest tests/unit/test_batch_config_007.py tests/unit/test_batch_result_007.py` — todos GREEN.

---

## Phase 3: User Story 1 — Anos específicos (Priority: P1) 🎯 MVP

**Goal**: `anos: [2025, 2026]` no YAML → batch expande para 24 períodos (12 × 2) por servidor.

**Independent Test**: YAML com `anos: [2025]` + 1 servidor via FakeBrowser → relatório com `total: 12`, 12 arquivos em subpasta do servidor, `BatchEntryResult.mes` e `BatchEntryResult.ano` preenchidos.

### Tests for US1 (escrever primeiro — devem FALHAR antes de T010-T011)

- [x] T007 [P] [US1] Unit test `tests/unit/test_periodo_expander.py`: assert `PeriodoExpander.expand(config_anos_2025, entry, today=date(2026,5,23))` retorna 12 tuplas `(mes, 2025)` de jan a dez; assert `anos: [2025, 2026]` + `today=date(2026,5,23)` retorna 12+5=17 períodos (jan-dez/2025 + jan-mai/2026); assert anos duplicados deduplizados; assert `anos: None` retorna `[(mes_entry, ano_entry)]` único; assert `anos: "All"` retorna `[]` (sinaliza para usar AdmissaoDetector)
- [x] T008 [P] [US1] Integration test `tests/integration/test_batch_end_to_end_007.py`: `anos: [2025]` + 1 servidor com SnapshotBrowser → `BatchResult.total == 12`; assert `batch-result-{run_id}.json` existe em `tmp_path`; assert `entries[0].mes is not None` e `entries[0].ano == 2025`
- [x] T009 [P] [US1] Contract test `tests/contract/test_batch_result_schema_007.py`: `BatchResult.to_dict()` com entries contendo `mes`/`ano` valida contra `contracts/batch-result.schema.json` de feature 007

### Implementation for US1

- [x] T010 Criar `src/homologacao_ponto/services/periodo_expander.py`: `PeriodoExpander` com método estático `expand(config: BatchConfig, entry: BatchEntry, today: date) -> list[tuple[int, int]]`; lista retorna `(mes, ano)` em ordem cronológica crescente; meses futuros excluídos; `anos="All"` retorna lista vazia (sinaliza uso do detector); `anos=None` retorna 1 período (compatibilidade legado) (depende de T007 vermelho)
- [x] T011 Modificar `src/homologacao_ponto/services/batch_service.py`: substituir cálculo inline de `mes`/`ano` por `PeriodoExpander.expand()`; adicionar loop interno `for (mes, ano) in periodos:` dentro do loop de entries; passar `mes=mes, ano=ano` para cada `BatchEntryResult` criado; tratar `periodos == []` como sinal para `AdmissaoDetector` (US2 — deixar como `NotImplemented` por ora, pode ser stub que lança `AdmissaoNaoDetectadaError`) (depende de T005, T010, T008 vermelho)

**Checkpoint**: `pytest tests/unit/test_periodo_expander.py tests/integration/test_batch_end_to_end_007.py tests/contract/test_batch_result_schema_007.py` — todos GREEN. US1 funcional.

---

## Phase 4: User Story 2 — Histórico completo (Priority: P2)

**Goal**: `anos: All` → `AdmissaoDetector` detecta primeiro espelho disponível e expande todos os meses desde então até hoje.

**Independent Test**: `anos: All` com FakeApp que retorna sucesso para meses recentes e falha para meses antigos → relatório contém apenas meses onde FakeApp retornou sucesso; `AdmissaoNaoDetectadaError` → entry marcado como `failed`.

### Tests for US2 (escrever primeiro — devem FALHAR antes de T014-T015)

- [x] T012 [P] [US2] Unit test `tests/unit/test_admissao_detector.py`: FakeApp retorna sucesso para 3 meses recentes e falha para todo o resto → assert detector retorna exatamente 3 períodos em ordem crescente; assert parada após 3 falhas consecutivas; FakeApp retorna falha para todos os meses → assert `AdmissaoNaoDetectadaError` levantado; assert limite máximo de busca (30 anos retroativos) respeita teto de anos
- [x] T013 [P] [US2] Integration test `tests/integration/test_batch_end_to_end_007.py` (novo teste no mesmo arquivo): `anos: All` com FakeBatchApp pré-configurado → relatório contém entries com `status` correto e `mes`/`ano` preenchidos; assert entry com `AdmissaoNaoDetectadaError` → `status=="failed"` e `error` não-nulo

### Implementation for US2

- [x] T014 Criar `src/homologacao_ponto/infrastructure/admissao_detector.py`: `AdmissaoNaoDetectadaError(Exception)`; `AdmissaoDetector` com método `detect(app, session, entry: BatchEntry, today: date) -> list[tuple[int, int]]`; probe regressivo mês a mês a partir de `today`; para após 3 falhas consecutivas (exit_code ≠ 0 exceto "empty"); limite de 30 anos retroativos; retorna períodos em ordem crescente; `AdmissaoNaoDetectadaError` se nenhum período bem-sucedido (depende de T012 vermelho)
- [x] T015 Modificar `src/homologacao_ponto/services/batch_service.py`: quando `periodos == []` (sinal de `anos="All"`), instanciar `AdmissaoDetector` e chamar `detect()`; capturar `AdmissaoNaoDetectadaError` → `BatchEntryResult(status="failed", error=str(exc))`; continuar lote após falha de detecção (depende de T014, T013 vermelho)

**Checkpoint**: `pytest tests/unit/test_admissao_detector.py tests/integration/test_batch_end_to_end_007.py` — todos GREEN incluindo cenários de `All`.

---

## Phase 5: User Story 3 — Compatibilidade legado (Priority: P3)

**Goal**: YAML sem `anos` funciona identicamente à feature 006 — sem mudança de comportamento externo.

**Independent Test**: YAML com `mes: 5` e `ano: 2026` sem campo `anos` gera `BatchResult.total == 1` por servidor; `BatchEntryResult.mes == 5` e `BatchEntryResult.ano == 2026`.

### Tests for US3 (escrever primeiro — devem FALHAR antes de T017)

- [x] T016 [P] [US3] Unit test `tests/unit/test_batch_service_007.py`: `BatchConfig(servidores=[entry], mes=5, ano=2026, anos=None)` → `BatchService.run()` chama `_run_single_espelho` exatamente 1x por servidor; `BatchEntryResult.mes == 5` e `BatchEntryResult.ano == 2026`; assert `anos=None` não altera exit_code ou estrutura do relatório vs comportamento 006
- [x] T017 [P] [US3] Integration test `tests/integration/test_batch_end_to_end_007.py` (novo teste): YAML legado (sem `anos`) via SnapshotBrowser → `BatchResult.total == 1` por servidor; JSON gerado em subpasta correta; `to_dict()` omite campos `mes`/`ano` (pois feature 006 não os incluía) — OU inclui com valores corretos (sem quebra de schema)

### Implementation for US3

- [x] T018 Verificar `src/homologacao_ponto/services/batch_service.py`: confirmar que `anos=None` → `PeriodoExpander.expand()` retorna 1 período e loop processa identicamente ao 006; nenhuma mudança de comportamento necessária se T011 foi implementado corretamente (validação via T016)

**Checkpoint**: `pytest tests/unit/test_batch_service_007.py tests/integration/test_batch_end_to_end_007.py` — todos GREEN incluindo cenários legado.

---

## Phase 6: Polish & Cross-Cutting

- [x] T019 [P] Atualizar `servidores.yaml` no root: adicionar exemplos comentados de `anos: [2025, 2026]` e `anos: All`; manter exemplo legado (sem `anos`) como default funcional
- [x] T020 [P] Negative-path tests `tests/unit/test_batch_config_007.py` (adicionar): YAML com `anos: []`; `anos: "Invalido"`; `anos: [1900]`; `anos` com elemento não-int; `anos: [2025]` + `mes: 5` coexistindo (aceito com warning)
- [x] T021 [P] Atualizar `docs/architecture/backlog.md`: status 007 de Draft → Implemented; atualizar tabela Resumo (EPIC-4: Draft 1→0, Implemented 0→1)
- [x] T022 Rodar `.venv/bin/ruff check src tests` e corrigir erros de lint introduzidos
- [x] T023 Rodar `.venv/bin/ruff format --check src` e corrigir formatação

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Sem dependências — iniciar imediatamente
- **Phase 2 (Modelos)**: Depende de T001 (fixtures)
- **Phase 3 (US1)**: Depende de T004, T005 (modelos modificados)
- **Phase 4 (US2)**: Depende de T010, T011 (PeriodoExpander + BatchService base)
- **Phase 5 (US3)**: Depende de T010, T011 (mesma base — validação de compat)
- **Phase 6 (Polish)**: Depende de US1, US2, US3 completos

### Within Each Story

```
Tests (T002-T003) FAIL → T004-T005 implement → T002-T003 GREEN
Tests (T007-T009) FAIL → T010-T011 implement → T007-T009 GREEN
Tests (T012-T013) FAIL → T014-T015 implement → T012-T013 GREEN
Tests (T016-T017) FAIL → T018 verify → T016-T017 GREEN
```

### Parallel Opportunities

- T002 e T003 paralelos (arquivos diferentes)
- T004 e T005 paralelos (arquivos diferentes)
- T007, T008, T009 paralelos (arquivos diferentes)
- T012 e T013 paralelos (arquivos diferentes)
- T016 e T017 paralelos (arquivos diferentes)
- T019, T020, T021 paralelos (docs + testes negativos)

---

## Parallel Execution Example

```
# Stream A: Modelos Foundational
T001              (fixtures)
T002 + T003       (testes paralelos, FAIL)
T004 + T005       (implementação paralela)
T006              (verificação exports)

# Stream B: US1 (após Stream A)
T007 + T008 + T009  (testes paralelos, FAIL)
T010              (PeriodoExpander)
T011              (BatchService — depende de T010)

# Stream C: US2 (após Stream B)
T012 + T013  (testes paralelos, FAIL)
T014         (AdmissaoDetector)
T015         (BatchService All — depende de T014)

# Stream D: US3 (em paralelo com Stream C, após Stream B)
T016 + T017  (testes paralelos, FAIL)
T018         (verificação compat)

# Stream E: Polish (após todos)
T019 + T020 + T021  (paralelo)
T022 → T023         (lint → format)
```

---

## Implementation Strategy

### MVP (US1 apenas)

1. Phase 1: T001
2. Phase 2: T002–T006
3. Phase 3: T007–T011
4. `homologacao-ponto batch --file servidores.yaml` com `anos: [2025]`
5. Verificar 12 JSONs + `batch-result-{run_id}.json`

### Full Delivery

1. MVP acima
2. Phase 4: US2 (`anos: All`)
3. Phase 5: US3 (compatibilidade)
4. Phase 6: Polish + docs

---

## Notes

- `[P]` = arquivos distintos, sem dependência de tarefa incompleta — paralelizável
- `[USN]` = rastreabilidade à user story N do spec.md
- Constitution I: teste FAIL antes de código de produção
- `PeriodoExpander.expand()` recebe `today: date` como parâmetro para garantir determinismo em testes
- `AdmissaoDetector` usa `app._run_single_espelho` — já testado na feature 006; probe apenas observa exit_code
- `BatchEntryResult.mes`/`ano` com default `None` → `to_dict()` os omite → backward compat garantida
- `anos: "all"` (lowercase) normalizado para `"All"` no loader — case-insensitive
