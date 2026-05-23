# Tasks: Exportar Tabela Completa do Espelho de Ponto por Servidor

**Input**: `specs/005-exportar-espelho-json/`
**Prerequisites**: plan.md ✓ spec.md ✓ research.md ✓ data-model.md ✓ contracts/ ✓

**Tests**: MANDATORY — failing test before each implementation block (Constitution I).

**User Stories**:
- US1 (P1): Capturar tabela completa com campos calculados (HR, HC, HE, HA, HH, Crédito, Débito, Saldo, CrédAcum, DNC)
- US2 (P1): Organizar arquivos JSON em pasta por servidor (`data/servidores/{slug}/`)
- US3 (P2): Preservar compatibilidade com schema anterior (spec 004)

---

## Phase 1: Setup

**Purpose**: Fixtures e helpers compartilhados — bloqueiam todos os user stories.

- [x] T001 Expand `tests/fixtures/sigrh_espelho_export_pages.py` with 12-column SIGRH HTML fixture (full table: Data, Horários Registrados, HR, HC, HE, HA, HH, Crédito, Débito, Saldo No Mês, Crédito Acumulado, DNC)
- [x] T002 [P] Add `_slug()` and `_periodo_slug()` module-level helpers to `src/homologacao_ponto/models/espelho_ponto_export.py` (no other changes yet — only helpers)
- [x] T003 [P] Update `specs/005-exportar-espelho-json/contracts/registro_dia_ponto.json` to include all 10 new fields (already done in plan — verify file is complete)

**Checkpoint**: Fixtures and helpers in place. US1, US2, US3 can start.

---

## Phase 2: User Story 1 — Capturar campos calculados (Priority: P1) 🎯 MVP

**Goal**: `RegistroDiaPonto` carries 10 new optional column fields; parser extracts them from SIGRH HTML.

**Independent Test**: Parse the 12-column fixture from T001; assert all 10 new fields present and non-null in the record for a day with full data.

### Tests for US1 (write first — must FAIL before T010)

- [x] T004 [P] [US1] Unit test: `tests/unit/test_registro_dia_ponto_new_fields.py` — assert `RegistroDiaPonto` accepts all 10 new fields; `to_dict()` includes them with correct keys; `None` renders as `null` not omitted
- [x] T005 [P] [US1] Unit test: `tests/unit/test_espelho_ponto_parser_columns.py` — parse 12-column fixture; assert each new field extracted at correct cell offset; assert `---` and empty cells map to `None`; assert missing cells (row with < 12 cells) map to `None` gracefully
- [x] T006 [P] [US1] Contract test: `tests/contract/test_espelho_ponto_export_schema.py` — add assertions that JSON output from a completed export contains all 10 new fields in each `registros` entry

### Implementation for US1

- [x] T007 [US1] Extend `RegistroDiaPonto` in `src/homologacao_ponto/models/espelho_ponto_export.py`: add 10 optional fields (`hr`, `hc`, `he`, `ha`, `hh`, `credito`, `debito`, `saldo_no_mes`, `credito_acumulado`, `dnc`), all `str | None = None`; update `to_dict()` to include them (depends on T004 red)
- [x] T008 [US1] Add `_cell_value(cells, date_idx, offset)` helper to `src/homologacao_ponto/infrastructure/espelho_ponto_parser.py`: returns `cell.strip()` or `None` when cell missing or contains only `---`
- [x] T009 [US1] Extend `_sigrh_extract_row()` in `src/homologacao_ponto/infrastructure/espelho_ponto_parser.py`: extract offsets +2..+11 using `_cell_value()` and include them in the returned row dict (depends on T005 red, T008)
- [x] T010 [US1] Update `_row_to_record()` in `EspelhoPontoParser` to pass 10 new fields from row dict to `RegistroDiaPonto` constructor (depends on T007, T009)

**Checkpoint**: `pytest tests/unit/test_registro_dia_ponto_new_fields.py tests/unit/test_espelho_ponto_parser_columns.py` — all green. US1 independently functional.

---

## Phase 3: User Story 2 — Organizar por pasta de servidor (Priority: P1)

**Goal**: Each `EspelhoPontoExport` saved to `data/servidores/{servidor-slug}/espelho-{periodo}.json`. Sub-folder created automatically. Re-run for same server/period overwrites previous file.

**Independent Test**: Write two exports for different servers; verify two separate sub-folders created; verify filenames derived from period; verify re-run overwrites (not duplicates).

### Tests for US2 (write first — must FAIL before T016)

- [x] T011 [P] [US2] Unit test: `tests/unit/test_espelho_ponto_export_path.py` — assert `EspelhoPontoExport.output_subdir` returns `"servidores/celio-proliciano-maioli"` for server "CELIO PROLICIANO MAIOLI"; assert `output_filename` returns `"espelho-dezembro-2025.json"` for periodo "Dezembro/2025"; assert fallback `espelho-{run_id}.json` when `periodo_referencia=None`
- [x] T012 [P] [US2] Unit test: `tests/unit/test_slug_normalization.py` — assert `_slug()` strips accents, lowercases, replaces spaces/specials with `-`, collapses repeated hyphens; test edge cases: all-caps, accented chars (é→e, ã→a), apostrophe, slash
- [x] T013 [P] [US2] Integration test: `tests/integration/test_result_writer_servidor_path.py` — write `EspelhoPontoExport` via `ResultWriter`; assert file created at `{output_dir}/servidores/{slug}/espelho-{periodo}.json`; assert sub-folder created automatically; assert re-write overwrites (file count stays 1 per server/period); assert `ExportacaoEspelhoResult` still writes to flat `{output_dir}/{filename}` (no `output_subdir` → unchanged)

### Implementation for US2

- [x] T014 [US2] Add `output_subdir` and updated `output_filename` properties to `EspelhoPontoExport` in `src/homologacao_ponto/models/espelho_ponto_export.py`, using `_slug()` and `_periodo_slug()` helpers from T002 (depends on T011 red, T002)
- [x] T015 [US2] Update `with_output_path()` in `EspelhoPontoExport` — no change needed to signature; verify `output_path` stored as string of full resolved path (auto-pass once T014 done)
- [x] T016 [US2] Update `ResultWriter.write()` in `src/homologacao_ponto/services/result_writer.py`: resolve `subdir = getattr(result, "output_subdir", None)`; build `output_path = output_dir / subdir / filename` when subdir non-None, else `output_dir / filename`; call `output_path.parent.mkdir(parents=True, exist_ok=True)` (depends on T013 red)

**Checkpoint**: `pytest tests/unit/test_espelho_ponto_export_path.py tests/integration/test_result_writer_servidor_path.py` — all green. US2 independently functional.

---

## Phase 4: User Story 3 — Preservar compatibilidade (Priority: P2)

**Goal**: Zero fields removed or renamed from spec-004 schema. Existing tests all pass.

**Independent Test**: Run full test suite (`pytest -q`); all 143+ existing tests pass. Compare JSON output keys against spec-004 field list.

### Tests for US3 (write first — must FAIL if any field missing)

- [x] T017 [P] [US3] Contract test: `tests/contract/test_espelho_004_compatibility.py` — build `EspelhoPontoExport` and `RegistroDiaPonto` with only spec-004 fields; assert `to_dict()` output contains ALL fields from spec-004 list (`data`, `dia_semana`, `marcacoes`, `ocorrencias`, `observacoes`, `situacao`, `textos_visiveis`, `run_id`, `captured_at`, `status`, `servidor`, `periodo_referencia`, `registros`, `fonte`); assert new fields are additive (no key removed)
- [x] T018 [P] [US3] Regression: run `pytest -q` and assert exit 0 — all pre-existing tests from spec-004 pass unchanged

### Implementation for US3

- [x] T019 [US3] Review `RegistroDiaPonto.to_dict()` after T007 — confirm all original 7 keys present before the 10 new ones; fix if any key was accidentally dropped (depends on T017 red)
- [x] T020 [US3] Review `EspelhoPontoExport.to_dict()` — confirm `schema_version`, `run_id`, `captured_at`, `status`, `servidor`, `periodo_referencia`, `mensagens`, `registros`, `fonte` all present unchanged (depends on T017 red)

**Checkpoint**: `pytest -q` — all tests green including spec-004 regression.

---

## Phase 5: Polish & Cross-Cutting

- [x] T021 [P] Update `docs/architecture/backlog.md`: mark `005-exportar-espelho-json` tasks as ✓
- [x] T022 [P] Update `docs/architecture/data-flow.md`: JSON example block now shows all 10 new fields; storage layout diagram shows `data/servidores/` tree
- [x] T023 Update `docs/architecture/overview.md` if `ResultWriter` contract section needs refreshing
- [x] T024 [P] Add negative-path tests: `tests/unit/test_espelho_ponto_parser_columns.py` — row with only 2 cells (no calculated columns); row with `---` in all calculated cells; row with negative saldo (`-08:00`)
- [x] T025 Run `ruff check src tests` and fix any linting issues introduced by new fields/helpers

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (US1)**: Depends on T001 (fixture), T002 (helpers)
- **Phase 3 (US2)**: Depends on T001, T002 — can run in parallel with US1 once Phase 1 done
- **Phase 4 (US3)**: Depends on US1 (T007–T010) and US2 (T014–T016) both complete
- **Phase 5 (Polish)**: Depends on all user stories complete

### Within Each Story

```
Tests (T004-T006) must FAIL → then T007-T010 implement → T004-T006 go GREEN
Tests (T011-T013) must FAIL → then T014-T016 implement → T011-T013 go GREEN
Tests (T017-T018) must FAIL → then T019-T020 implement → T017-T018 go GREEN
```

### Parallel Opportunities

- T004, T005, T006 can run in parallel (different test files)
- T007 and T008 can run in parallel (different methods)
- T011, T012, T013 can run in parallel (different test files)
- US1 phases and US2 phases can run in parallel once Phase 1 complete

---

## Parallel Example: US1 + US2 simultaneously (after Phase 1)

```
# Stream A: US1 — Column capture
T004 → T005 → T006  (tests, parallel)
T007 + T008         (parallel model + helper)
T009 → T010         (sequential: parser then record converter)

# Stream B: US2 — Per-server path (can run alongside Stream A)
T011 + T012 + T013  (tests, parallel)
T014 → T015 → T016  (sequential: model props then writer)
```

---

## Implementation Strategy

### MVP (US1 + US2 only)

1. Phase 1: T001–T003 (fixtures + helpers)
2. Phase 2 + Phase 3 in parallel (US1 columns + US2 path routing)
3. Run `pytest -q` — green
4. Run `homologacao-ponto espelho-ponto --servidor "CELIO ..." --mes 12 --ano 2025 --siape 1534589 --headed`
5. Verify `data/servidores/celio-proliciano-maioli/espelho-dezembro-2025.json` contains `hr`, `hc`, etc.

### Full Delivery

1. MVP above
2. Phase 4: US3 compatibility tests + verification
3. Phase 5: Polish + docs update

---

## Notes

- `[P]` = different files, no task dependency — can parallelize
- `[USN]` = traceability to user story N in spec.md
- Constitution requires: test FAIL before production code ADD
- Parser `_cell_value()` must return `None` (not `""` or `"---"`) for missing cells — `RegistroDiaPonto.to_dict()` outputs `null`
- `ResultWriter` change is backward-compatible: `getattr(result, "output_subdir", None)` returns `None` for all existing result types
- `_slug("CELIO PROLICIANO MAIOLI")` → `"celio-proliciano-maioli"` — verify with T012 before using in prod
