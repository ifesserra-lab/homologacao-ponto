# Tasks: Selecionar Servidor no Espelho de Ponto

**Input**: Design documents from `/specs/003-selecionar-servidor/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are MANDATORY. This project constitution requires test-first delivery for every behavioral change, with negative-path coverage for external HTTP, persistence, security-sensitive flows, and error handling.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or does not depend on incomplete tasks.
- **[Story]**: User story label for story phases only.
- Every task includes an exact file path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add route-mocked fixtures and contract samples needed by the server-selection feature.

- [X] T001 Verify existing Python 3.12 package metadata and test dependencies support server-selection tests in pyproject.toml
- [X] T002 [P] Add route-mocked SIGRH server-selection HTML fixtures for unique, missing, ambiguous, missing-control, expired-session, blocked, and destination-mismatch pages in tests/fixtures/sigrh_server_selection_pages.py
- [X] T003 [P] Add completed, failed, partial, and blocked selection-result sample dictionaries in tests/fixtures/server_selection_samples.py
- [X] T004 [P] Add selection-result JSON schema contract file reference tests scaffold in tests/contract/test_selection_result_schema.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create shared domain and persistence primitives required by all server-selection stories.

**CRITICAL**: No user story work can begin until this phase is complete.

### Tests for Foundation

- [X] T005 [P] Write failing unit tests for ServidorConsulta normalization, identifier handling, and empty-name validation in tests/unit/test_server_selection.py
- [X] T006 [P] Write failing unit tests for ServidorResultado matching and selection availability rules in tests/unit/test_server_selection.py
- [X] T007 [P] Write failing unit tests for SelecaoServidorResult completed, failed, partial, blocked, output filename, and output path behavior in tests/unit/test_server_selection_result.py
- [X] T008 [P] Write failing contract tests validating selection-result samples against specs/003-selecionar-servidor/contracts/selection-result.schema.json in tests/contract/test_selection_result_schema.py
- [X] T009 [P] Write failing unit tests for ResultWriter selection-result output filename and write-failure behavior in tests/unit/test_server_selection_result_writer.py

### Implementation for Foundation

- [X] T010 [P] Implement ServidorConsulta, ServidorResultado, and server-name normalization in src/homologacao_ponto/models/server_selection.py
- [X] T011 [P] Implement SelecaoServidorResult model and selection status enum in src/homologacao_ponto/models/server_selection_result.py
- [X] T012 Export ServidorConsulta, ServidorResultado, SelecaoServidorResult, and selection status enum from src/homologacao_ponto/models/__init__.py
- [X] T013 Extend ResultWriter to write SelecaoServidorResult files named selection-result-{run_id}.json without breaking CrawlResult or NavigationResult writes in src/homologacao_ponto/services/result_writer.py
- [X] T014 Add safe server-selection logging helpers or messages without raw HTML, cookies, or credentials in src/homologacao_ponto/infrastructure/logging.py

**Checkpoint**: Foundation ready. Selection models, schema tests, and JSON persistence primitives are available for all stories.

---

## Phase 3: User Story 1 - Abrir espelho do servidor encontrado (Priority: P1) MVP

**Goal**: Select the row-level "Selecionar Servidor" control for a unique matching server and stop when the daily point page identifies that server.

**Independent Test**: With route-mocked SIGRH pages containing one matching server result and a row-level selection control, the command/service selects that row, confirms the selected server on the final page, and does not extract point records.

### Tests for User Story 1

- [X] T015 [P] [US1] Write failing unit tests for successful ServerSelectionService unique-result selection and completed SelecaoServidorResult in tests/unit/test_server_selection_service.py
- [X] T016 [P] [US1] Write failing unit tests for SigrhBrowser result-row extraction, row-level selection-control detection, and selected-server confirmation in tests/unit/test_sigrh_browser_server_selection.py
- [X] T017 [P] [US1] Write failing Playwright route-mocked integration test for unique server selection to the daily point page in tests/integration/test_playwright_server_selection_success.py
- [X] T018 [P] [US1] Write failing contract test for `homologacao-ponto espelho-ponto --servidor` success stdout and exit code 0 in tests/contract/test_cli_server_selection.py

### Implementation for User Story 1

- [X] T019 [P] [US1] Implement ServerSelectionRequest and ServerSelectionService success flow in src/homologacao_ponto/services/server_selection_service.py
- [X] T020 [US1] Extend SigrhBrowser with server result discovery, row-scoped "Selecionar Servidor" click, and selected-server confirmation methods in src/homologacao_ponto/infrastructure/sigrh_browser.py
- [X] T021 [US1] Apply RateLimiter before SIGRH search and selection actions in ServerSelectionService in src/homologacao_ponto/services/server_selection_service.py
- [X] T022 [US1] Extend run_espelho_ponto orchestration to optionally search and select a requested server after reaching the Espelho de Ponto form in src/homologacao_ponto/app.py
- [X] T023 [US1] Add `--servidor` option to the existing `espelho-ponto` subcommand in src/homologacao_ponto/cli.py
- [X] T024 [US1] Ensure successful selection stops after selected-server page confirmation and does not invoke point-record extraction in src/homologacao_ponto/app.py

**Checkpoint**: User Story 1 is independently functional as the MVP.

---

## Phase 4: User Story 2 - Informar quando o servidor nao pode ser selecionado (Priority: P2)

**Goal**: Provide clear failures when the server is missing, results are ambiguous, selection control is absent, session expires, automation is blocked, or final page confirmation is unexpected.

**Independent Test**: With route-mocked pages for missing, ambiguous, missing-control, expired, blocked, and destination-mismatch states, the service stops at the correct stage, returns a clear message, and never selects the wrong server.

### Tests for User Story 2

- [X] T025 [P] [US2] Write failing unit tests for missing server result and ambiguous result failures in tests/unit/test_server_selection_service_failures.py
- [X] T026 [P] [US2] Write failing unit tests for missing selection control and destination mismatch failures in tests/unit/test_server_selection_service_failures.py
- [X] T027 [P] [US2] Write failing unit tests for session expiration and anti-automation blocked handling during selection in tests/unit/test_server_selection_service_security.py
- [X] T028 [P] [US2] Write failing Playwright route-mocked integration tests for missing, ambiguous, missing-control, expired, blocked, and destination-mismatch server-selection flows in tests/integration/test_playwright_server_selection_failures.py
- [X] T029 [P] [US2] Write failing contract tests for CLI exit codes 3, 4, and 6 for blocked, selection failure, and session expiration in tests/contract/test_cli_server_selection_failures.py

### Implementation for User Story 2

- [X] T030 [US2] Add ServerSelectionService failure mapping for missing result, ambiguous result, missing selection control, destination mismatch, blocked automation, and expired session in src/homologacao_ponto/services/server_selection_service.py
- [X] T031 [US2] Extend SigrhBrowser selection methods to detect login redirect/session expiration and anti-automation pages during server selection in src/homologacao_ponto/infrastructure/sigrh_browser.py
- [X] T032 [US2] Enforce no-click behavior for ambiguous results and global menu links in src/homologacao_ponto/infrastructure/sigrh_browser.py
- [X] T033 [US2] Map selection failure statuses to app exit codes 3, 4, and 6 without automatic reauthentication in src/homologacao_ponto/app.py
- [X] T034 [US2] Extend CLI stderr/stdout handling for `espelho-ponto --servidor` failure messages in src/homologacao_ponto/cli.py
- [X] T035 [US2] Add local logging for selection outcome, missing result, ambiguity, missing control, destination mismatch, blocked automation, and session expiration in src/homologacao_ponto/services/server_selection_service.py

**Checkpoint**: User Stories 1 and 2 work independently and report actionable failures without unsafe selection.

---

## Phase 5: User Story 3 - Registrar resultado da selecao (Priority: P3)

**Goal**: Persist a local JSON selection result for success and handled failures, and report JSON write failures as unsuccessful executions.

**Independent Test**: Success and failure flows produce selection JSON with status, requested server, selected server when present, message, and completion time; write failure returns exit code 5 and does not report success.

### Tests for User Story 3

- [X] T036 [P] [US3] Write failing unit tests for SelecaoServidorResult.to_dict fields, status consistency, and username_ref redaction in tests/unit/test_server_selection_result.py
- [X] T037 [P] [US3] Write failing unit tests for ResultWriter selection output filename and write failure behavior in tests/unit/test_server_selection_result_writer.py
- [X] T038 [P] [US3] Write failing contract tests for selection JSON output path, schema validity, and exit code 5 on write failure in tests/contract/test_cli_server_selection_json_output.py
- [X] T039 [P] [US3] Write failing integration test that success and missing-result flows both persist selection JSON when writing succeeds in tests/integration/test_server_selection_result_persistence.py

### Implementation for User Story 3

- [X] T040 [US3] Complete SelecaoServidorResult serialization, success derivation, final_step validation, and sensitive-data exclusion in src/homologacao_ponto/models/server_selection_result.py
- [X] T041 [US3] Ensure ResultWriter writes SelecaoServidorResult output_path and raises ResultWriteError on local write failure in src/homologacao_ponto/services/result_writer.py
- [X] T042 [US3] Persist completed, failed, partial, and blocked SelecaoServidorResult values from run_espelho_ponto with `--servidor` in src/homologacao_ponto/app.py
- [X] T043 [US3] Print generated selection JSON path on successful and handled failure `espelho-ponto --servidor` executions in src/homologacao_ponto/cli.py
- [X] T044 [US3] Add logging assertions support for no password, cookie, raw HTML, or credential-file leakage during selection result persistence in tests/unit/test_sensitive_data_redaction.py

**Checkpoint**: All user stories are independently functional and server-selection attempts are auditable through local JSON.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, cleanup, and regression safety across all stories.

- [X] T045 [P] Update README usage examples for `homologacao-ponto espelho-ponto --servidor "Nome"` in README.md
- [X] T046 [P] Update .env.example comments only if a new documented variable is needed for server selection in .env.example
- [X] T047 [P] Add or refine quickstart validation notes after implementation in specs/003-selecionar-servidor/quickstart.md
- [X] T048 Run focused server-selection tests under tests/unit/, tests/integration/, and tests/contract/ with `.venv/bin/python -m pytest tests/unit/test_server_selection.py tests/unit/test_server_selection_result.py tests/unit/test_server_selection_service.py tests/unit/test_server_selection_service_failures.py tests/unit/test_server_selection_service_security.py tests/unit/test_sigrh_browser_server_selection.py tests/integration/test_playwright_server_selection_success.py tests/integration/test_playwright_server_selection_failures.py tests/integration/test_server_selection_result_persistence.py tests/contract/test_selection_result_schema.py tests/contract/test_cli_server_selection.py tests/contract/test_cli_server_selection_failures.py tests/contract/test_cli_server_selection_json_output.py`
- [X] T049 Run full regression suite for tests/ with `.venv/bin/python -m pytest`
- [X] T050 Review generated selection JSON files in data/runs/ and logs in logs/ to confirm no password, cookie, raw HTML, screenshot, trace, or token persistence

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; delivers MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational; can be developed after or alongside US1, but app/CLI integration is simpler after US1.
- **User Story 3 (Phase 5)**: Depends on Foundational and benefits from US1/US2 result-producing flows.
- **Polish (Phase 6)**: Depends on selected user stories being complete.

### User Story Dependencies

- **US1 - Abrir espelho do servidor encontrado**: Start after Phase 2; no dependency on US2 or US3.
- **US2 - Informar quando o servidor nao pode ser selecionado**: Start after Phase 2; uses the same service/adapter boundaries as US1.
- **US3 - Registrar resultado da selecao**: Start after Phase 2; validates persistence for US1 and US2 outcomes.

### Within Each User Story

- Write tests first and verify they fail for the expected reason.
- Implement or extend models before services.
- Implement services before app/CLI orchestration.
- Extend app orchestration before CLI contract output.
- Complete each story checkpoint before moving to the next priority when working sequentially.

### Parallel Opportunities

- T002, T003, and T004 can run in parallel after T001.
- T005 through T009 can run in parallel because they are separate test files.
- T010 and T011 can run in parallel because they create separate model files.
- US1 tests T015 through T018 can run in parallel.
- US2 tests T025 through T029 can run in parallel.
- US3 tests T036 through T039 can run in parallel.
- Documentation tasks T045 through T047 can run in parallel after implementation.

---

## Parallel Example: User Story 1

```bash
# Launch tests for User Story 1 together:
Task: "T015 [US1] Write unit tests in tests/unit/test_server_selection_service.py"
Task: "T016 [US1] Write unit tests in tests/unit/test_sigrh_browser_server_selection.py"
Task: "T017 [US1] Write integration test in tests/integration/test_playwright_server_selection_success.py"
Task: "T018 [US1] Write contract test in tests/contract/test_cli_server_selection.py"

# Launch implementation slices after tests are red:
Task: "T019 [US1] Implement service in src/homologacao_ponto/services/server_selection_service.py"
Task: "T020 [US1] Extend adapter in src/homologacao_ponto/infrastructure/sigrh_browser.py"
```

## Parallel Example: User Story 2

```bash
# Launch negative-path tests together:
Task: "T025 [US2] Write missing and ambiguous tests in tests/unit/test_server_selection_service_failures.py"
Task: "T027 [US2] Write security-state tests in tests/unit/test_server_selection_service_security.py"
Task: "T028 [US2] Write integration failure tests in tests/integration/test_playwright_server_selection_failures.py"
Task: "T029 [US2] Write CLI failure tests in tests/contract/test_cli_server_selection_failures.py"
```

## Parallel Example: User Story 3

```bash
# Launch persistence tests together:
Task: "T036 [US3] Write model serialization tests in tests/unit/test_server_selection_result.py"
Task: "T037 [US3] Write writer tests in tests/unit/test_server_selection_result_writer.py"
Task: "T038 [US3] Write CLI JSON tests in tests/contract/test_cli_server_selection_json_output.py"
Task: "T039 [US3] Write persistence integration tests in tests/integration/test_server_selection_result_persistence.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup fixtures.
2. Complete Phase 2 foundational tests and domain/persistence primitives.
3. Complete Phase 3 User Story 1 tests and implementation.
4. Stop and validate: `homologacao-ponto espelho-ponto --servidor "Celio Proliciano Maioli"` reaches a mocked selected-server point page and exits 0.

### Incremental Delivery

1. Setup + Foundation: selection model, schema, writer support.
2. US1: happy-path unique-result selection to selected-server point page.
3. US2: missing result, ambiguity, missing control, blocked, expired, and destination mismatch failures.
4. US3: local JSON persistence for all handled outcomes and write-failure exit behavior.
5. Polish: docs, full regression, sensitive-data review.

### Validation Gates

1. Run focused server-selection tests listed in T048.
2. Run full regression suite listed in T049.
3. Confirm quickstart behavior against mocked tests before any live SIGRH attempt.
4. Do not persist screenshots, traces, raw HTML, cookies, or credentials by default.

## Notes

- [P] tasks touch separate files or can be done without waiting on another incomplete task in the same phase.
- [US1], [US2], and [US3] map directly to the prioritized user stories in spec.md.
- Existing crawl and espelho navigation behavior must remain compatible while adding `--servidor`.
- Routine automated tests must use mocked SIGRH pages and must not contact the live SIGRH.
