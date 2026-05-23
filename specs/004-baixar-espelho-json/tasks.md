# Tasks: Baixar Espelho de Ponto em JSON

**Input**: Design documents from `/specs/004-baixar-espelho-json/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Mandatory by spec and constitution. Write each test first and verify it fails before implementing the matching production task.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on another incomplete task.
- **[Story]**: User story label for traceability.
- Every task includes exact file paths.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify project setup and prepare shared fixtures/contracts for implementation.

- [X] T001 Verify Python/git ignore patterns for generated artifacts in .gitignore
- [X] T002 [P] Add Espelho export schema fixture loader helpers in tests/fixtures/espelho_export_samples.py
- [X] T003 [P] Add route-backed Espelho page fixture HTML builders in tests/fixtures/sigrh_espelho_export_pages.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared contracts and model surfaces required before user-story implementation.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Add failing schema contract tests for report JSON in tests/contract/test_espelho_ponto_export_schema.py
- [X] T005 [P] Add failing schema contract tests for operational result JSON in tests/contract/test_export_result_schema.py
- [X] T006 [P] Add failing domain model tests for EspelhoPontoExport and RegistroDiaPonto in tests/unit/test_espelho_ponto_export.py
- [X] T007 [P] Add failing domain model tests for ExportacaoEspelhoResult in tests/unit/test_espelho_export_result.py
- [X] T008 Implement RegistroDiaPonto and EspelhoPontoExport classes in src/homologacao_ponto/models/espelho_ponto_export.py
- [X] T009 Implement ExportacaoEspelhoResult class in src/homologacao_ponto/models/espelho_export_result.py
- [X] T010 Export new model classes from src/homologacao_ponto/models/__init__.py
- [X] T011 Extend ResultWriter naming and JSON write support for espelho-ponto and export-result outputs in src/homologacao_ponto/services/result_writer.py

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Gerar JSON do espelho selecionado (Priority: P1) MVP

**Goal**: After successful "Selecionar Servidor", automatically extract visible Espelho de Ponto records and write a dedicated JSON report file.

**Independent Test**: A simulated selected-server espelho page with server identity, period, messages, and daily records produces `espelho-ponto-{run_id}.json` without raw HTML or sensitive artifacts.

### Tests for User Story 1 (MANDATORY)

- [X] T012 [P] [US1] Add failing parser unit tests for valid daily records in tests/unit/test_espelho_ponto_parser.py
- [X] T013 [P] [US1] Add failing service unit test for successful export orchestration in tests/unit/test_espelho_export_service.py
- [X] T014 [P] [US1] Add failing CLI contract test for automatic export after server selection in tests/contract/test_cli_espelho_export.py
- [X] T015 [P] [US1] Add failing Playwright integration test for successful selected-server export in tests/integration/test_playwright_espelho_export_success.py

### Implementation for User Story 1

- [X] T016 [P] [US1] Implement EspelhoPontoParser valid-page extraction in src/homologacao_ponto/infrastructure/espelho_ponto_parser.py
- [X] T017 [US1] Add selected espelho snapshot/extraction methods to SigrhBrowser in src/homologacao_ponto/infrastructure/sigrh_browser.py
- [X] T018 [US1] Implement EspelhoExportService successful export flow in src/homologacao_ponto/services/espelho_export_service.py
- [X] T019 [US1] Integrate EspelhoExportService after server selection in src/homologacao_ponto/app.py
- [X] T020 [US1] Update CLI success output to print report and result paths in src/homologacao_ponto/cli.py

**Checkpoint**: User Story 1 is independently functional and testable as the MVP.

---

## Phase 4: User Story 2 - Tratar espelho vazio ou incompleto (Priority: P2)

**Goal**: Distinguish empty espelho from invalid or unsafe pages, preserving available visible data without inventing missing fields.

**Independent Test**: Simulated empty, incomplete, invalid, wrong-server, expired-session, and anti-automation pages produce clear status without associating records to the wrong server.

### Tests for User Story 2 (MANDATORY)

- [X] T021 [P] [US2] Add failing parser unit tests for empty and incomplete espelho pages in tests/unit/test_espelho_ponto_parser.py
- [X] T022 [P] [US2] Add failing service unit tests for wrong-server, invalid-page, expired-session, and anti-automation failures in tests/unit/test_espelho_export_service.py
- [X] T023 [P] [US2] Add failing CLI contract tests for empty and failure export outcomes in tests/contract/test_cli_espelho_export.py
- [X] T024 [P] [US2] Add failing Playwright integration tests for export failure paths in tests/integration/test_playwright_espelho_export_failures.py

### Implementation for User Story 2

- [X] T025 [US2] Extend EspelhoPontoParser empty/incomplete/wrong-page detection in src/homologacao_ponto/infrastructure/espelho_ponto_parser.py
- [X] T026 [US2] Extend SigrhBrowser export-state detection for session expiry and anti-automation pages in src/homologacao_ponto/infrastructure/sigrh_browser.py
- [X] T027 [US2] Extend EspelhoExportService failure and empty-result handling in src/homologacao_ponto/services/espelho_export_service.py
- [X] T028 [US2] Update app flow to stop without reauthentication on export session failures in src/homologacao_ponto/app.py
- [X] T029 [US2] Update CLI messages and exit codes for empty, invalid, wrong-server, expired-session, and blocked exports in src/homologacao_ponto/cli.py

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Registrar resultado da exportacao (Priority: P3)

**Goal**: Persist an operational result for every export attempt, with status, message, final step, server, period, and export path when present.

**Independent Test**: Success, empty, invalid page, anti-automation, expired session, and write failure flows each write or attempt the expected result JSON and never declare a failed report as successful.

### Tests for User Story 3 (MANDATORY)

- [X] T030 [P] [US3] Add failing result writer unit tests for export-result and report path handling in tests/unit/test_result_writer_success.py
- [X] T031 [P] [US3] Add failing write-failure unit tests for export report/result persistence in tests/unit/test_result_writer_failure.py
- [X] T032 [P] [US3] Add failing service unit tests for operational result status mapping in tests/unit/test_espelho_export_service.py
- [X] T033 [P] [US3] Add failing integration test for persisted export result JSON in tests/integration/test_espelho_export_result_persistence.py

### Implementation for User Story 3

- [X] T034 [US3] Complete ExportacaoEspelhoResult serialization and status helpers in src/homologacao_ponto/models/espelho_export_result.py
- [X] T035 [US3] Persist export-result JSON for success, empty, blocked, and failed attempts in src/homologacao_ponto/services/espelho_export_service.py
- [X] T036 [US3] Ensure write failures return unsuccessful export results without declaring report paths in src/homologacao_ponto/services/result_writer.py
- [X] T037 [US3] Surface export-result path and final-step diagnostics through application results in src/homologacao_ponto/app.py

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, docs, and security checks across all stories.

- [X] T038 [P] Update README usage for automatic Espelho JSON export in README.md
- [X] T039 [P] Update quickstart evidence notes after implementation in specs/004-baixar-espelho-json/quickstart.md
- [X] T040 Run focused unit tests for export models, parser, service, and result writer with .venv/bin/python -m pytest tests/unit/test_espelho_ponto_export.py tests/unit/test_espelho_export_result.py tests/unit/test_espelho_ponto_parser.py tests/unit/test_espelho_export_service.py tests/unit/test_result_writer_success.py tests/unit/test_result_writer_failure.py
- [X] T041 Run contract and integration tests for export JSON flow with .venv/bin/python -m pytest tests/contract/test_espelho_ponto_export_schema.py tests/contract/test_export_result_schema.py tests/contract/test_cli_espelho_export.py tests/integration/test_playwright_espelho_export_success.py tests/integration/test_playwright_espelho_export_failures.py tests/integration/test_espelho_export_result_persistence.py
- [X] T042 Run full regression suite with .venv/bin/python -m pytest

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational and is the MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational; can use US1 parser/service surfaces but remains independently testable with fixtures.
- **User Story 3 (Phase 5)**: Depends on Foundational; integrates operational persistence for US1 and US2 outcomes.
- **Polish (Phase 6)**: Depends on desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Start after Phase 2; delivers the primary export file.
- **US2 (P2)**: Start after Phase 2; may be implemented after US1 for smoother integration.
- **US3 (P3)**: Start after Phase 2; best implemented after US1/US2 status outcomes are known.

### Within Each User Story

- Tests must be written and observed failing before implementation.
- Parser/model tasks precede service tasks.
- Service tasks precede app and CLI integration tasks.
- Story checkpoint validation must pass before moving to the next priority when working sequentially.

### Parallel Opportunities

- T002 and T003 can run in parallel after T001.
- T004, T005, T006, and T007 can run in parallel in Phase 2.
- T012, T013, T014, and T015 can run in parallel for US1 test creation.
- T021, T022, T023, and T024 can run in parallel for US2 test creation.
- T030, T031, T032, and T033 can run in parallel for US3 test creation.
- T038 and T039 can run in parallel during polish.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Add failing parser unit tests for valid daily records in tests/unit/test_espelho_ponto_parser.py"
Task: "Add failing service unit test for successful export orchestration in tests/unit/test_espelho_export_service.py"
Task: "Add failing CLI contract test for automatic export after server selection in tests/contract/test_cli_espelho_export.py"
Task: "Add failing Playwright integration test for successful selected-server export in tests/integration/test_playwright_espelho_export_success.py"
```

## Parallel Example: User Story 2

```bash
# Launch all tests for User Story 2 together:
Task: "Add failing parser unit tests for empty and incomplete espelho pages in tests/unit/test_espelho_ponto_parser.py"
Task: "Add failing service unit tests for wrong-server, invalid-page, expired-session, and anti-automation failures in tests/unit/test_espelho_export_service.py"
Task: "Add failing CLI contract tests for empty and failure export outcomes in tests/contract/test_cli_espelho_export.py"
Task: "Add failing Playwright integration tests for export failure paths in tests/integration/test_playwright_espelho_export_failures.py"
```

## Parallel Example: User Story 3

```bash
# Launch all tests for User Story 3 together:
Task: "Add failing result writer unit tests for export-result and report path handling in tests/unit/test_result_writer_success.py"
Task: "Add failing write-failure unit tests for export report/result persistence in tests/unit/test_result_writer_failure.py"
Task: "Add failing service unit tests for operational result status mapping in tests/unit/test_espelho_export_service.py"
Task: "Add failing integration test for persisted export result JSON in tests/integration/test_espelho_export_result_persistence.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate US1 with focused unit, contract, and integration tests.
5. Run the quickstart command against an authorized environment when ready.

### Incremental Delivery

1. Setup + Foundational -> schema/model/report writer foundation.
2. US1 -> valid selected-server report JSON.
3. US2 -> empty/incomplete/unsafe page handling.
4. US3 -> durable operational result records.
5. Polish -> docs and regression suite.

### Validation Commands

```bash
.venv/bin/python -m pytest tests/unit/test_espelho_ponto_export.py tests/unit/test_espelho_export_result.py tests/unit/test_espelho_ponto_parser.py tests/unit/test_espelho_export_service.py
```

```bash
.venv/bin/python -m pytest tests/contract/test_espelho_ponto_export_schema.py tests/contract/test_export_result_schema.py tests/contract/test_cli_espelho_export.py
```

```bash
.venv/bin/python -m pytest
```
