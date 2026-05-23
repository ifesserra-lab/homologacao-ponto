# Tasks: Resumo das Horas Apuradas no JSON do Mês

**Input**: Design documents from `/specs/009-resumo-horas-json/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: MANDATORY — testes falhando antes de cada implementação (TDD red→green).

---

## Phase 1: Setup

**Purpose**: Verificar baseline e preparar fixture HTML com seção resumo.

- [x] T001 Verificar que todos os testes existentes passam: `python -m pytest tests/ -x -q && cd dashboard && npm test`
- [x] T002 Adicionar fixture `VALID_ESPELHO_WITH_RESUMO_HTML` em `tests/fixtures/sigrh_espelho_export_pages.py` com tabela "Resumo das Horas Apuradas no Mês" simulando os 16 campos do SIGRH

---

## Phase 2: Foundational (Blocking)

**Purpose**: Modelo `ResumoHorasApuradas` disponível para ambas as user stories.

**⚠️ CRÍTICO**: US1 e US2 dependem desta fase.

- [x] T003 [US1] Escrever teste falhando: `ResumoHorasApuradas` — `to_dict()` retorna dict com 16 campos em `tests/unit/test_resumo_horas_apuradas.py`
- [x] T004 [US1] Escrever teste falhando: `ResumoHorasApuradas` — instância com todos campos None não lança exceção em `tests/unit/test_resumo_horas_apuradas.py`
- [x] T005 [US1] Implementar `ResumoHorasApuradas` frozen dataclass com 16 campos `str | None` e `to_dict()` em `src/homologacao_ponto/models/espelho_ponto_export.py`
- [x] T006 [US1] Exportar `ResumoHorasApuradas` em `src/homologacao_ponto/models/__init__.py`

**Checkpoint**: `python -m pytest tests/unit/test_resumo_horas_apuradas.py -v` deve passar.

---

## Phase 3: User Story 1 — Capturar Resumo Completo do SIGRH (Priority: P1) 🎯 MVP

**Goal**: `EspelhoPontoParser.parse()` extrai os 16 campos do resumo e persiste em `export.resumo`; `to_dict()` inclui `resumo` e `schema_version=2`.

**Independent Test**: Executar `EspelhoPontoParser().parse(snapshot(VALID_ESPELHO_WITH_RESUMO_HTML), ...)` e verificar que `export.resumo.total_horas_homologadas == "49:25"` e `export.resumo.saldo_horas_mes == "-09:10"`.

### Testes para US1 ⚠️ (escrever ANTES da implementação)

- [x] T007 [P] [US1] Teste falhando: `EspelhoPontoExport.to_dict()` contém chave `resumo` e `schema_version == 2` quando `resumo` não é None em `tests/unit/test_espelho_ponto_export.py`
- [x] T008 [P] [US1] Teste falhando: `EspelhoPontoExport.to_dict()` contém `resumo: null` e `schema_version == 2` quando `resumo` é None em `tests/unit/test_espelho_ponto_export.py`
- [x] T009 [P] [US1] Teste falhando: `EspelhoPontoParser.parse()` com `VALID_ESPELHO_WITH_RESUMO_HTML` retorna `export.resumo` com todos os 16 campos preenchidos em `tests/unit/test_espelho_ponto_parser.py`
- [x] T010 [P] [US1] Teste falhando negativo: `EspelhoPontoParser.parse()` com HTML sem seção resumo retorna `export.resumo is None` em `tests/unit/test_espelho_ponto_parser.py`
- [x] T011 [P] [US1] Teste falhando: valores negativos como `"-09:10"` preservados com sinal em `export.resumo.saldo_horas_mes` em `tests/unit/test_espelho_ponto_parser.py`
- [x] T012 [P] [US1] Teste falhando: `EspelhoPontoExport.empty()` tem `resumo: None` em `tests/unit/test_espelho_ponto_export.py`

### Implementação US1

- [x] T013 [US1] Atualizar `EspelhoPontoExport` em `src/homologacao_ponto/models/espelho_ponto_export.py`: adicionar campo `resumo: ResumoHorasApuradas | None = None`, atualizar `to_dict()` com `schema_version=2` e `"resumo": self.resumo.to_dict() if self.resumo else None`, atualizar `with_output_path()` para propagar `resumo`
- [x] T014 [US1] Implementar `_RESUMO_LABEL_MAP` em `src/homologacao_ponto/infrastructure/espelho_ponto_parser.py`: dicionário mapeando substrings normalizadas dos rótulos SIGRH → nome do campo `ResumoHorasApuradas` (16 entradas, ver `research.md`)
- [x] T015 [US1] Implementar `_ResumoHTMLParser(HTMLParser)` em `src/homologacao_ponto/infrastructure/espelho_ponto_parser.py`: detecta início da seção resumo pelo texto "Resumo das Horas Apuradas", captura pares label→valor via células de tabela, método `build_resumo() -> ResumoHorasApuradas | None`
- [x] T016 [US1] Integrar `_ResumoHTMLParser` em `EspelhoPontoParser.parse()` em `src/homologacao_ponto/infrastructure/espelho_ponto_parser.py`: instanciar parser separado, alimentar com mesmo HTML, atribuir resultado ao `EspelhoPontoExport`

**Checkpoint**: `python -m pytest tests/unit/test_espelho_ponto_export.py tests/unit/test_espelho_ponto_parser.py tests/unit/test_resumo_horas_apuradas.py -v` deve passar. JSON exportado contém campo `resumo` com 16 campos.

---

## Phase 4: User Story 2 — Dashboard usa Resumo diretamente (Priority: P2)

**Goal**: Dashboard lê `resumo` do JSON e exibe valores exatos do SIGRH; fallback para cálculo quando `resumo: null`.

**Independent Test**: Abrir `http://localhost:4321/servidor/<slug>/maio-2026` após re-exportação com resumo; stats "Carga Esperada", "Horas Homologadas" e "Falta compensar" batem com os valores do SIGRH.

### Testes para US2 ⚠️ (escrever ANTES da implementação)

- [x] T017 [P] [US2] Teste Vitest falhando: `aggregateMonth` com `resumo` não nulo usa `total_horas_homologadas` como `somaCreditoMin` em `dashboard/src/tests/aggregation.test.ts`
- [x] T018 [P] [US2] Teste Vitest falhando: `aggregateMonth` com `resumo` não nulo usa `saldo_horas_mes` como `balanceMin` em `dashboard/src/tests/aggregation.test.ts`
- [x] T019 [P] [US2] Teste Vitest falhando: `aggregateMonth` com `resumo` não nulo usa `carga_horaria_esperada_mes` como `cargaEsperadaMin` em `dashboard/src/tests/aggregation.test.ts`
- [x] T020 [P] [US2] Teste Vitest: `aggregateMonth` com `resumo: null` usa fallback de cálculo sem erro em `dashboard/src/tests/aggregation.test.ts`
- [x] T021 [P] [US2] Teste Vitest: `aggregateMonth` sem campo `resumo` (JSON v1) usa fallback sem erro em `dashboard/src/tests/aggregation.test.ts`

### Implementação US2

- [x] T022 [US2] Adicionar interface `ResumoHorasApuradas` e campo `resumo?: ResumoHorasApuradas | null` em `dashboard/src/types/dashboard.ts` em `RawEspelho`
- [x] T023 [US2] Atualizar `aggregateMonth` em `dashboard/src/lib/aggregation.ts`: aceitar segundo parâmetro `resumo?: ResumoHorasApuradas | null`; quando não nulo, usar `parseSignedHHMM(resumo.total_horas_homologadas)` para `somaCreditoMin`, `parseSignedHHMM(resumo.total_horas_registradas)` para `somaHrMin`, `parseSignedHHMM(resumo.carga_horaria_esperada_mes)` para `cargaEsperadaMin`, `parseSignedHHMM(resumo.saldo_horas_mes)` para `balanceMin`
- [x] T024 [US2] Atualizar `dashboard/src/pages/servidor/[slug]/[periodo].astro`: passar `espelho.resumo ?? null` para `aggregateMonth`

**Checkpoint**: `cd dashboard && npm test` — todos os testes passam (≥32). Dashboard mostra valores idênticos ao SIGRH para meses re-exportados.

---

## Phase 5: Polish & Cross-Cutting

- [x] T025 [P] Atualizar `docs/espelho-ponto-schema.yaml` — adicionar objeto `resumo` com 16 campos `string | null` e `schema_version: 2`
- [x] T026 [P] Executar suite completa final: `python -m pytest tests/ -q` + `cd dashboard && npm test` — todos passando
- [x] T027 Commit: `git add -p && git commit -m "feat(009): captura resumo horas apuradas no JSON (schema v2)"`

---

## Dependencies & Execution Order

### Dependências entre fases

- **Phase 1 (Setup)**: sem dependências — iniciar imediatamente
- **Phase 2 (Foundational)**: depende de Phase 1 — BLOQUEIA US1 e US2
- **Phase 3 (US1)**: depende de Phase 2
- **Phase 4 (US2)**: depende de Phase 3 (usa tipos Python exportados e TypeScript atualizado)
- **Phase 5 (Polish)**: depende de Phase 3 + Phase 4

### Dentro de cada US

```
Testes falhando (T007–T012) → paralelo entre si
↓
T013 (modelo) → T014 (label map) → T015 (parser) → T016 (integração)
```

### Oportunidades de paralelismo

```bash
# Phase 3 — testes podem rodar em paralelo:
T007, T008, T009, T010, T011, T012  # todos em arquivos diferentes

# Phase 4 — testes Vitest em paralelo:
T017, T018, T019, T020, T021
```

---

## Estratégia de Implementação

### MVP (US1 apenas)

1. Phase 1: Setup + fixture HTML
2. Phase 2: `ResumoHorasApuradas` modelo
3. Phase 3: Parser + `EspelhoPontoExport` atualizado
4. **VALIDAR**: re-exportar maio/2026 → verificar JSON tem campo `resumo`

### Entrega incremental

1. US1 completa → JSON v2 com resumo → re-exportar servidores
2. US2 completa → dashboard usa valores exatos do SIGRH

---

## Notas

- `[P]` = tasks em arquivos diferentes, sem dependência entre si
- Escrever teste falhando e confirmar falha ANTES de implementar
- `schema_version` deve ser `2` em todos os exports (inclusive empty)
- Retro-compatibilidade: `resumo` ausente em JSON v1 tratado como `null` no dashboard
