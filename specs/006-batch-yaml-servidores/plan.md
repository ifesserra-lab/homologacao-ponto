# Implementation Plan: Lote de Servidores via Arquivo YAML

**Branch**: `006-batch-yaml-servidores` | **Date**: 2026-05-23 | **Spec**: [spec.md](spec.md)
**Input**: `specs/006-batch-yaml-servidores/spec.md`

## Summary

Adiciona subcomando `batch` ao CLI que lê arquivo YAML com lista de servidores
(nome + SIAPE + período opcional) e baixa o Espelho de Ponto de cada servidor
sequencialmente, reutilizando a sessão Playwright. Persiste um relatório
consolidado `batch-result-{run_id}.json` e retorna exit code não-zero se
qualquer servidor falhou.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: PyYAML (adicionar em `pyproject.toml`); Playwright (já existente)
**Storage**: JSON em disco via `ResultWriter` — sem mudança de infraestrutura
**Testing**: pytest TDD red/green/refactor
**Target Platform**: macOS/Linux (CLI headless)
**Project Type**: CLI
**Performance Goals**: Lote de 10 servidores < 5 minutos headless
**Constraints**: Sessão Playwright única durante todo o lote; sem paralelismo
**Scale/Scope**: Listas de até ~50 servidores por execução

## Constitution Check

| Princípio | Status | Evidência |
|-----------|--------|-----------|
| I. Test-First | ✓ | Testes falham antes de cada bloco de implementação |
| II. Python 3.12+ | ✓ | Sem exceção — PyYAML é pure Python |
| III. OO Domain Design | ✓ | `BatchConfig`, `BatchEntry`, `BatchResult`, `BatchService` como classes de domínio |
| IV. Design Patterns | ✓ | Strategy implícita via `_run_single_espelho()` extraído; sem novos patterns desnecessários |
| V. Quality Gates | ✓ | `pytest -q` + `ruff check` como gates; cada US validável independentemente |

**Complexidade extra**: Nenhuma — PyYAML é dependência mínima para parse de YAML.

## Project Structure

### Documentation (esta feature)

```text
specs/006-batch-yaml-servidores/
├── plan.md              ← este arquivo
├── research.md          ✓
├── data-model.md        ✓
├── contracts/
│   ├── batch-config.schema.yaml   ✓
│   └── batch-result.schema.json   ✓
└── tasks.md             (gerado por /speckit-tasks)
```

### Source Code (novos arquivos)

```text
src/homologacao_ponto/
├── models/
│   ├── batch_config.py         # BatchEntry, BatchConfig
│   └── batch_result.py         # BatchEntryResult, BatchResult
├── services/
│   └── batch_service.py        # BatchService.run()
├── app.py                      # + _run_single_espelho(), run_batch()
└── cli.py                      # + subcomando "batch"

tests/
├── unit/
│   ├── test_batch_config.py
│   ├── test_batch_result.py
│   └── test_batch_service.py
├── integration/
│   └── test_batch_end_to_end.py
├── contract/
│   └── test_batch_result_schema.py
└── fixtures/
    └── batch_fixtures.py
```

## Implementation Phases

### Phase 0 — Setup (bloqueante)

**T001** Adicionar `pyyaml` em `pyproject.toml` e instalar no venv
**T002** Criar `tests/fixtures/batch_fixtures.py` com YAMLs válidos e inválidos, e `BatchConfig`/`BatchEntry` prontos para testes

### Phase 1 — US1: Lote via YAML (P1) 🎯 MVP

**Fluxo de implementação**:
```
Tests (T003-T005) FAIL → implementar T006-T010 → testes GREEN
```

**T003** [P] Unit test `test_batch_config.py` — deserializar YAML válido; validar entradas obrigatórias; erro em YAML malformado; erro em lista vazia; override mes/ano por servidor
**T004** [P] Unit test `test_batch_service.py` — `BatchService.run()` processa 2 servidores; cada entrada captura `AppResult` e gera `BatchEntryResult`; `BatchResult` tem total/succeeded/failed corretos
**T005** [P] Integration test `test_batch_end_to_end.py` — 2 servidores via YAML falso (FakeBrowser); 2 JSONs criados; `batch-result-{run_id}.json` gerado em `output_dir`

**T006** Criar `models/batch_config.py`: `BatchEntry(nome, siape, mes, ano)`, `BatchConfig(servidores, mes, ano)`, `BatchConfigLoader.load(path: Path) -> BatchConfig`
**T007** Criar `models/batch_result.py`: `BatchEntryResult`, `BatchResult` com `output_filename`, `with_output_path()`, `to_dict()`
**T008** Extrair `HomologacaoPontoApp._run_single_espelho()` de `run_espelho_ponto()` — sem mudança de comportamento externo (depende de T003 vermelho)
**T009** Criar `services/batch_service.py`: `BatchService.run()` itera lista, chama `_run_single_espelho()`, agrega em `BatchResult` (depende de T007, T008)
**T010** Adicionar `HomologacaoPontoApp.run_batch(config: BatchConfig) -> AppResult` em `app.py` e subcomando `batch` em `cli.py` (depende de T009)

**Checkpoint**: `pytest tests/unit/test_batch_config.py tests/unit/test_batch_service.py tests/integration/test_batch_end_to_end.py` — todos GREEN

### Phase 2 — US2: Resiliência (P2)

**T011** [P] Unit test `test_batch_service.py` — servidor inválido no meio da lista; restantes processados; `failed=1`; exit code não-zero
**T012** [P] Unit test — sessão expirada detectada durante lote → reautentica → retenta servidor atual → continua

**T013** Implementar tratamento de falha parcial em `BatchService.run()` — captura exceções e `AppResult` com exit code != 0; registra erro em `BatchEntryResult.error` (depende de T011 vermelho)
**T014** Implementar detecção de sessão expirada + retry em `BatchService.run()` (depende de T012 vermelho)

**Checkpoint**: `pytest tests/unit/test_batch_service.py` — todos GREEN incluindo cenários de falha

### Phase 3 — US3: Relatório consolidado (P3)

**T015** [P] Contract test `test_batch_result_schema.py` — `BatchResult.to_dict()` valida contra `batch-result.schema.json`
**T016** [P] Integration test — `batch-result-{run_id}.json` existe em `output_dir` após lote; contém `started_at`, `finished_at`, contagens, entries

**T017** Garantir `ResultWriter.write(BatchResult)` persiste em `{output_dir}/batch-result-{run_id}.json` (sem subdir — `output_subdir` ausente → fallback já existente) (depende de T015 vermelho)

**Checkpoint**: `pytest tests/contract/test_batch_result_schema.py tests/integration/test_batch_end_to_end.py` — GREEN

### Phase 4 — Polish

**T018** Atualizar `docs/architecture/backlog.md` — 006 muda de Draft → Implemented
**T019** Atualizar `docs/architecture/data-flow.md` — adicionar fluxo batch
**T020** `ruff check src tests && ruff format --check src` — zero erros

## Ordem de Execução

```
T001 → T002 (setup, bloqueante)
  ↓
T003 + T004 + T005 (testes em paralelo, todos FAIL)
  ↓
T006 + T007 (modelos, paralelo)
  ↓
T008 → T009 → T010 (sequencial: extração → serviço → CLI)
  ↓
T011 + T012 (testes falha parcial, paralelo)
  ↓
T013 → T014 (implementação resiliência, sequencial)
  ↓
T015 + T016 (testes relatório, paralelo)
  ↓
T017 (garantir persistência)
  ↓
T018 + T019 + T020 (polish, paralelo)
```

## Validação Final

```bash
.venv/bin/pytest -q                          # 182+ testes, todos GREEN
.venv/bin/ruff check src tests               # 0 erros
homologacao-ponto batch --file servidores.yaml  # lote real contra SIGRH
cat data/runs/batch-result-*.json            # relatório com succeeded/failed
ls data/runs/servidores/                     # pasta por servidor
```
