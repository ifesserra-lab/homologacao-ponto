# Tasks: Lote de Servidores via Arquivo YAML

**Input**: `specs/006-batch-yaml-servidores/`
**Prerequisites**: plan.md ✓ spec.md ✓ research.md ✓ data-model.md ✓ contracts/ ✓

**Tests**: MANDATORY — failing test before each implementation block (Constitution I).

**User Stories**:
- US1 (P1): Baixar lote de servidores via arquivo YAML
- US2 (P2): Continuar lote após falha parcial de servidor
- US3 (P3): Relatório consolidado JSON do lote

---

## Phase 1: Setup

**Purpose**: Dependência PyYAML e fixtures compartilhadas — bloqueiam todos os user stories.

- [x] T001 Adicionar `pyyaml` em `pyproject.toml` (seção `[project].dependencies`) e instalar com `.venv/bin/pip install -e .`
- [x] T002 [P] Criar `tests/fixtures/batch_fixtures.py` com: YAML string válido (2 servidores), YAML malformado, YAML com lista vazia, objetos `BatchEntry` e `BatchConfig` prontos para reuso nos testes

**Checkpoint**: `import yaml` sem erro no venv; fixtures importáveis.

---

## Phase 2: Foundational — Modelos de Domínio

**Purpose**: `BatchEntry`, `BatchConfig`, `BatchEntryResult`, `BatchResult` — usados por US1, US2 e US3.

### Tests (write first — must FAIL before T005-T006)

- [x] T003 [P] Unit test `tests/unit/test_batch_config.py` — assert `BatchConfigLoader.load()` desserializa YAML válido em `BatchConfig`; assert `BatchEntry` com `mes`/`ano` opcionais; assert erro em YAML malformado (`BatchConfigError`); assert erro em lista vazia; assert override `mes`/`ano` por servidor sobrescreve default do `BatchConfig`
- [x] T004 [P] Unit test `tests/unit/test_batch_result.py` — assert `BatchResult.output_filename` retorna `batch-result-{run_id}.json`; assert `to_dict()` contém `run_id`, `started_at`, `finished_at`, `total`, `succeeded`, `failed`, `entries`; assert `BatchEntryResult.to_dict()` contém `nome`, `siape`, `status`, `export_path` (null quando None), `error` (null quando None); assert sem `output_subdir` (fallback para flat path no ResultWriter)

### Implementation

- [x] T005 Criar `src/homologacao_ponto/models/batch_config.py`: `BatchEntry(nome, siape, mes=None, ano=None)`, `BatchConfig(servidores, mes=None, ano=None)`, `BatchConfigError(ValueError)`, `BatchConfigLoader.load(path: Path) -> BatchConfig` usando `yaml.safe_load` (depende de T001, T003 vermelho)
- [x] T006 [P] Criar `src/homologacao_ponto/models/batch_result.py`: `BatchEntryResult(nome, siape, status, export_path=None, error=None)`, `BatchResult(run_id, started_at, finished_at, total, succeeded, failed, entries, output_path=None)` com `output_filename`, `with_output_path()`, `to_dict()` (depende de T004 vermelho)
- [x] T007 Atualizar `src/homologacao_ponto/models/__init__.py` para exportar `BatchEntry`, `BatchConfig`, `BatchConfigLoader`, `BatchConfigError`, `BatchEntryResult`, `BatchResult`

**Checkpoint**: `pytest tests/unit/test_batch_config.py tests/unit/test_batch_result.py` — todos GREEN.

---

## Phase 3: User Story 1 — Baixar lote via YAML (Priority: P1) 🎯 MVP

**Goal**: `homologacao-ponto batch --file servidores.yaml` processa todos os servidores em sequência e salva JSONs em `data/servidores/{slug}/`.

**Independent Test**: YAML com 2 servidores via FakeBrowser → 2 JSONs gerados em subpastas corretas + `batch-result-{run_id}.json` em `output_dir`.

### Tests for US1 (write first — must FAIL before T011)

- [x] T008 [P] [US1] Unit test `tests/unit/test_batch_service.py` — `BatchService.run()` com FakeBrowser que retorna sucesso: assert `BatchResult.total == 2`, `succeeded == 2`, `failed == 0`; assert cada `BatchEntryResult.status == "completed"`; assert cada `BatchEntryResult.export_path` não-nulo
- [x] T009 [P] [US1] Integration test `tests/integration/test_batch_end_to_end.py` — 2 servidores com SnapshotBrowser (fixture já existente); assert 2 arquivos em `tmp_path/servidores/{slug1}/` e `{slug2}/`; assert `tmp_path/batch-result-{run_id}.json` existe
- [x] T010 [P] [US1] Contract test `tests/contract/test_batch_result_schema.py` — `BatchResult.to_dict()` valida contra `contracts/batch-result.schema.json`

### Implementation for US1

- [x] T011 Extrair `HomologacaoPontoApp._run_single_espelho(session, servidor, siape, mes, ano) -> AppResult` de `run_espelho_ponto()` em `src/homologacao_ponto/app.py`; `run_espelho_ponto()` delega para `_run_single_espelho()` sem mudança de comportamento externo (depende de T008 vermelho)
- [x] T012 Criar `src/homologacao_ponto/services/batch_service.py`: `BatchService(app: HomologacaoPontoApp, result_writer: ResultWriter)`; `run(session, config, run_id) -> BatchResult`; resolve `mes`/`ano` (entry > config > mês/ano corrente); chama `_run_single_espelho()` por servidor; agrega em `BatchResult` com `started_at`/`finished_at` (depende de T006, T011, T009 vermelho)
- [x] T013 Adicionar `HomologacaoPontoApp.run_batch(config: BatchConfig) -> AppResult` em `src/homologacao_ponto/app.py`: autentica uma vez, chama `BatchService.run()`, persiste `BatchResult` via `result_writer.write()`, retorna `AppResult(0, ...)` com resumo (depende de T012)
- [x] T014 Adicionar subcomando `batch` em `src/homologacao_ponto/cli.py`: `--file` (required), `--output-dir`, `--env-file`, `--mes`, `--ano`; carrega YAML via `BatchConfigLoader.load()`; chama `app.run_batch(config)` (depende de T013)

**Checkpoint**: `pytest tests/unit/test_batch_service.py tests/integration/test_batch_end_to_end.py tests/contract/test_batch_result_schema.py` — todos GREEN. US1 funcional.

---

## Phase 4: User Story 2 — Resiliência a falhas parciais (Priority: P2)

**Goal**: Servidor não encontrado ou erro de seleção não aborta o lote; registra falha e continua.

**Independent Test**: YAML com 3 servidores, FakeBrowser retorna erro no 2° — 1° e 3° `completed`, 2° `failed`; `BatchResult.failed == 1`; exit code não-zero.

### Tests for US2 (write first — must FAIL before T016)

- [x] T015 [P] [US2] Unit test `tests/unit/test_batch_service.py` — `BatchService.run()` com FakeBrowser que lança exceção no 2° servidor: assert `total==3`, `succeeded==2`, `failed==1`; assert `entries[1].status == "failed"` e `entries[1].error` não-nulo; assert `entries[0]` e `entries[2]` completados
- [x] T016 [P] [US2] Unit test — sessão expirada detectada (AppResult exit_code==6): `BatchService.run()` chama reautenticação e retenta; assert servidor retentado aparece como `"completed"` no resultado

### Implementation for US2

- [x] T017 Adicionar try/except em `BatchService.run()` em `src/homologacao_ponto/services/batch_service.py`: captura `Exception` por servidor → `BatchEntryResult(status="failed", error=str(exc))`; nunca aborta o loop (depende de T015 vermelho)
- [x] T018 Implementar detecção de sessão expirada em `BatchService.run()`: se `AppResult.exit_code == 6` → chama `app.auth_service.login()` → retenta servidor atual 1x; se falhar novamente registra como `"failed"` (depende de T016 vermelho)
- [x] T019 Garantir exit code não-zero em `HomologacaoPontoApp.run_batch()` quando `BatchResult.failed > 0`: retornar `AppResult(1, ...)` em vez de `AppResult(0, ...)` (depende de T017)

**Checkpoint**: `pytest tests/unit/test_batch_service.py` — todos GREEN incluindo cenários de falha.

---

## Phase 5: User Story 3 — Relatório consolidado (Priority: P3)

**Goal**: `batch-result-{run_id}.json` sempre gerado em `output_dir`, com `started_at`, `finished_at`, contagens e lista de entries.

**Independent Test**: Após lote de 3 servidores (via FakeBrowser), arquivo JSON existe em `tmp_path`; `to_dict()` valida contra schema JSON.

### Tests for US3 (write first — must FAIL before T021)

- [x] T020 [P] [US3] Integration test `tests/integration/test_batch_end_to_end.py` — assert `batch-result-{run_id}.json` existe em `tmp_path` após lote; assert `started_at` e `finished_at` são ISO 8601 válidos; assert `total == len(servidores)`; assert `succeeded + failed == total`
- [x] T021 [P] [US3] Integration test — lote com falha parcial: assert relatório gerado mesmo quando `failed > 0`; assert relatório gerado mesmo quando `failed == total` (falha total)

### Implementation for US3

- [x] T022 Verificar que `ResultWriter.write(BatchResult)` persiste em `{output_dir}/batch-result-{run_id}.json` sem subdiretório (sem `output_subdir` → fallback flat já funciona); confirmar via teste T020 (depende de T020 vermelho)
- [x] T023 Garantir `run_batch()` chama `result_writer.write(batch_result)` mesmo quando `failed == total` (capturar exceções antes do write) (depende de T021 vermelho)

**Checkpoint**: `pytest tests/integration/test_batch_end_to_end.py` — todos GREEN. US3 funcional.

---

## Phase 6: Polish & Cross-Cutting

- [x] T024 [P] Atualizar `docs/architecture/backlog.md`: status 006 muda de Draft → Implemented; atualizar tabela resumo
- [x] T025 [P] Atualizar `docs/architecture/data-flow.md`: adicionar seção "Fluxo Batch" com diagrama ASCII mostrando YAML → BatchService → N × (seleção + exportação) → BatchResult
- [x] T026 [P] Adicionar negative-path tests: YAML inexistente (`FileNotFoundError`); YAML sem campo `servidores`; YAML com `mes: 13` (inválido); `--file` sem argumento
- [x] T027 Rodar `.venv/bin/ruff check src tests` e corrigir erros de lint introduzidos
- [x] T028 Rodar `.venv/bin/ruff format --check src` e corrigir formatação

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Sem dependências — iniciar imediatamente
- **Phase 2 (Modelos)**: Depende de T001 (PyYAML)
- **Phase 3 (US1)**: Depende de T005, T006, T007 (modelos prontos)
- **Phase 4 (US2)**: Depende de T011–T014 (US1 completo)
- **Phase 5 (US3)**: Depende de T012 (BatchService cria `BatchResult`)
- **Phase 6 (Polish)**: Depende de US1, US2, US3 completos

### Within Each Story

```
Tests (T003-T004) FAIL → T005-T007 implement → T003-T004 GREEN
Tests (T008-T010) FAIL → T011-T014 implement → T008-T010 GREEN
Tests (T015-T016) FAIL → T017-T019 implement → T015-T016 GREEN
Tests (T020-T021) FAIL → T022-T023 implement → T020-T021 GREEN
```

### Parallel Opportunities

- T003 e T004 paralelos (arquivos diferentes)
- T005 e T006 paralelos (arquivos diferentes)
- T008, T009, T010 paralelos (arquivos diferentes)
- T015 e T016 paralelos (arquivos diferentes)
- T020 e T021 paralelos (arquivos diferentes)
- T024, T025, T026 paralelos (docs + testes negativos)

---

## Parallel Execution Example

```
# Stream A: Modelos
T003 + T004  (testes paralelos, FAIL)
T005 + T006  (implementação paralela)
T007         (exports __init__)

# Stream B: US1 (após Stream A)
T008 + T009 + T010  (testes paralelos, FAIL)
T011                (extração _run_single_espelho)
T012 → T013 → T014  (sequencial: BatchService → run_batch → CLI)

# Stream C: US2 (após Stream B)
T015 + T016  (testes paralelos, FAIL)
T017 → T018 → T019  (sequencial: try/except → retry → exit code)

# Stream D: US3 (pode rodar em paralelo com Stream C após T012)
T020 + T021  (testes paralelos, FAIL)
T022 → T023  (sequencial)

# Stream E: Polish (após todos)
T024 + T025 + T026  (paralelo)
T027 → T028         (sequencial: lint → format)
```

---

## Implementation Strategy

### MVP (US1 apenas)

1. Phase 1: T001–T002
2. Phase 2: T003–T007
3. Phase 3: T008–T014
4. `homologacao-ponto batch --file servidores.yaml`
5. Verificar `data/runs/servidores/{slug}/espelho-{periodo}.json` + `batch-result-{run_id}.json`

### Full Delivery

1. MVP acima
2. Phase 4: US2 resiliência
3. Phase 5: US3 relatório garantido
4. Phase 6: Polish + docs

---

## Notes

- `[P]` = arquivos distintos, sem dependência de tarefa incompleta — paralelizável
- `[USN]` = rastreabilidade à user story N do spec.md
- Constitution I: teste FAIL antes de código de produção
- `yaml.safe_load` obrigatório (não `yaml.load`) — segurança contra YAML arbitrário
- `BatchResult` sem `output_subdir` → `ResultWriter` usa fallback flat path (compatibilidade garantida)
- `_run_single_espelho()` extrai lógica já testada — nenhum teste existente quebra
- Override `mes`/`ano`: prioridade CLI > entry YAML > config YAML > mês/ano corrente
