# Tasks: Navegacao ate Espelho do Ponto

**Input**: Design documents from `/specs/002-navegar-espelho-ponto/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are MANDATORY. This project constitution requires test-first delivery for every behavioral change, with negative-path coverage for external HTTP, persistence, security-sensitive flows, and error handling.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or does not depend on incomplete tasks.
- **[Story]**: User story label for story phases only.
- Every task includes an exact file path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the existing Python project and add test fixtures needed by the navigation feature.

- [X] T001 Verify existing Python 3.12 package metadata and test dependencies support the navigation feature in pyproject.toml
- [X] T002 [P] Add route-mocked SIGRH menu HTML fixtures for complete, missing-menu, timeout, expired-session, blocked, and destination-mismatch pages in tests/fixtures/sigrh_navigation_pages.py
- [X] T003 [P] Add JSON sample fixtures for completed, failed, partial, and blocked navigation results in tests/fixtures/navigation_result_samples.py
- [X] T004 [P] Add navigation contract schema loader helper for tests in tests/contract/test_navigation_result_schema.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create shared domain and persistence primitives required by all user stories.

**CRITICAL**: No user story work can begin until this phase is complete.

### Tests for Foundation

- [X] T005 [P] Write failing unit tests for NavigationPath canonical labels, accent-insensitive matching, and 15-second step wait in tests/unit/test_navigation_path.py
- [X] T006 [P] Write failing unit tests for NavigationStep valid statuses and terminal failure message validation in tests/unit/test_navigation_step.py
- [X] T007 [P] Write failing unit tests for NavigationResult completed, failed, partial, blocked, output filename, and output path behavior in tests/unit/test_navigation_result.py
- [X] T008 [P] Write failing contract tests validating sample navigation JSON files against contracts/navigation-result.schema.json in tests/contract/test_navigation_result_schema.py
- [X] T009 [P] Write failing unit tests for writing navigation results and write failures in tests/unit/test_navigation_result_writer.py

### Implementation for Foundation

- [X] T010 [P] Implement NavigationPath model and label normalization in src/homologacao_ponto/models/navigation_path.py
- [X] T011 [P] Implement NavigationStep model and status enum in src/homologacao_ponto/models/navigation_step.py
- [X] T012 [P] Implement NavigationResult model and status enum in src/homologacao_ponto/models/navigation_result.py
- [X] T013 Export NavigationPath, NavigationStep, NavigationResult, and navigation status enums from src/homologacao_ponto/models/__init__.py
- [X] T014 Extend ResultWriter to write NavigationResult files named navigation-result-{run_id}.json without breaking CrawlResult writes in src/homologacao_ponto/services/result_writer.py
- [X] T015 Add safe navigation-event logging helpers or messages without raw HTML, cookies, or credentials in src/homologacao_ponto/infrastructure/logging.py

**Checkpoint**: Foundation ready. Navigation models, schema tests, and JSON persistence primitives are available for all stories.

---

## Phase 3: User Story 1 - Acessar espelho do ponto apos login (Priority: P1) MVP

**Goal**: Navigate an authenticated SIGRH session through the requested menu path and stop when the visible page confirms "Espelho do Ponto".

**Independent Test**: With route-mocked SIGRH pages containing the full menu path, the command/service reaches the destination, confirms visible title/heading/breadcrumb "Espelho do Ponto", and does not generate or extract the report.

### Tests for User Story 1

- [X] T016 [P] [US1] Write failing unit tests for successful MenuNavigationService step sequencing and completed NavigationResult in tests/unit/test_menu_navigation_service_success.py
- [X] T017 [P] [US1] Write failing unit tests for SigrhBrowser menu label matching and visible destination confirmation in tests/unit/test_sigrh_browser_navigation.py
- [X] T018 [P] [US1] Write failing Playwright route-mocked integration test for complete menu navigation to "Espelho do Ponto" in tests/integration/test_playwright_espelho_navigation_success.py
- [X] T019 [P] [US1] Write failing contract test for `homologacao-ponto espelho-ponto` success stdout and exit code 0 in tests/contract/test_cli_espelho_success.py

### Implementation for User Story 1

- [X] T020 [P] [US1] Implement MenuNavigationRequest and MenuNavigationService success flow in src/homologacao_ponto/services/menu_navigation_service.py
- [X] T021 [US1] Extend SigrhBrowser with click_menu_path, wait_for_menu_label, and destination-visible confirmation methods in src/homologacao_ponto/infrastructure/sigrh_browser.py
- [X] T022 [US1] Apply RateLimiter before each SIGRH menu action in MenuNavigationService in src/homologacao_ponto/services/menu_navigation_service.py
- [X] T023 [US1] Add run_espelho_ponto orchestration using existing login flow, MenuNavigationService, ResultWriter, and browser close handling in src/homologacao_ponto/app.py
- [X] T024 [US1] Add `espelho-ponto` subcommand with --output-dir, --env-file, and --headed options in src/homologacao_ponto/cli.py
- [X] T025 [US1] Ensure the success path stops after visible "Espelho do Ponto" confirmation and does not invoke attendance extraction in src/homologacao_ponto/app.py

**Checkpoint**: User Story 1 is independently functional as the MVP.

---

## Phase 4: User Story 2 - Informar bloqueios de permissao ou menu ausente (Priority: P2)

**Goal**: Provide clear, stage-specific failures when required menu items are absent, permission is insufficient, the session expires, automation is blocked, a step times out, or the destination is unexpected.

**Independent Test**: With route-mocked pages that remove or alter each required menu stage, the service stops at the correct stage, returns a clear message, preserves the no-reauthentication rule, and avoids out-of-scope navigation.

### Tests for User Story 2

- [X] T026 [P] [US2] Write failing unit tests for missing "Chefia de Unidade" and missing "Homologacao de Ponto Eletronico" failures in tests/unit/test_menu_navigation_service_failures.py
- [X] T027 [P] [US2] Write failing unit tests for 15-second step timeout and destination mismatch failures in tests/unit/test_menu_navigation_service_timeouts.py
- [X] T028 [P] [US2] Write failing unit tests for session expiration and anti-automation blocked handling during navigation in tests/unit/test_menu_navigation_service_security.py
- [X] T029 [P] [US2] Write failing Playwright route-mocked integration tests for missing menu, expired session, blocked automation, and destination mismatch in tests/integration/test_playwright_espelho_navigation_failures.py
- [X] T030 [P] [US2] Write failing contract tests for CLI exit codes 3, 4, and 6 for blocked, navigation failure, and session expiration in tests/contract/test_cli_espelho_failures.py

### Implementation for User Story 2

- [X] T031 [US2] Add MenuNavigationService failure mapping for missing labels, permission/menu absence, timeout, destination mismatch, blocked automation, and expired session in src/homologacao_ponto/services/menu_navigation_service.py
- [X] T032 [US2] Extend SigrhBrowser navigation methods to detect login redirect/session expiration and anti-automation pages during menu navigation in src/homologacao_ponto/infrastructure/sigrh_browser.py
- [X] T033 [US2] Enforce 15-second per-step wait and stage-specific error messages in src/homologacao_ponto/infrastructure/sigrh_browser.py
- [X] T034 [US2] Map navigation failure statuses to app exit codes 3, 4, and 6 without automatic reauthentication in src/homologacao_ponto/app.py
- [X] T035 [US2] Extend CLI stderr/stdout handling for espelho-ponto failure messages in src/homologacao_ponto/cli.py
- [X] T036 [US2] Add local logging for step outcome, timeout, missing menu, destination mismatch, blocked automation, and session expiration in src/homologacao_ponto/services/menu_navigation_service.py

**Checkpoint**: User Stories 1 and 2 work independently and report actionable failures.

---

## Phase 5: User Story 3 - Registrar resultado da navegacao (Priority: P3)

**Goal**: Persist a local JSON navigation result for success and handled failures, and report JSON write failures as unsuccessful executions.

**Independent Test**: Success and failure flows produce navigation JSON with status, final step, message, steps, and completion time; write failure returns exit code 5 and does not report success.

### Tests for User Story 3

- [X] T037 [P] [US3] Write failing unit tests for NavigationResult.to_dict fields, status consistency, and username_ref redaction in tests/unit/test_navigation_result.py
- [X] T038 [P] [US3] Write failing unit tests for ResultWriter navigation output filename and write failure behavior in tests/unit/test_navigation_result_writer.py
- [X] T039 [P] [US3] Write failing contract tests for navigation JSON output path, schema validity, and exit code 5 on write failure in tests/contract/test_cli_espelho_json_output.py
- [X] T040 [P] [US3] Write failing integration test that success and missing-menu flows both persist navigation JSON when writing succeeds in tests/integration/test_espelho_navigation_result_persistence.py

### Implementation for User Story 3

- [X] T041 [US3] Complete NavigationResult serialization, success derivation, final_step validation, and sensitive-data exclusion in src/homologacao_ponto/models/navigation_result.py
- [X] T042 [US3] Ensure ResultWriter writes NavigationResult output_path and raises ResultWriteError on local write failure in src/homologacao_ponto/services/result_writer.py
- [X] T043 [US3] Persist completed, failed, partial, and blocked NavigationResult values from run_espelho_ponto in src/homologacao_ponto/app.py
- [X] T044 [US3] Print generated navigation JSON path on successful and handled failure espelho-ponto executions in src/homologacao_ponto/cli.py
- [X] T045 [US3] Add logging assertions support for no password, cookie, raw HTML, or credential-file leakage during navigation result persistence in src/homologacao_ponto/infrastructure/logging.py

**Checkpoint**: All user stories are independently functional and navigation attempts are auditable through local JSON.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, cleanup, and regression safety across all stories.

- [X] T046 [P] Update README usage examples for `homologacao-ponto espelho-ponto` in README.md
- [X] T047 [P] Update .env.example comments only if a new documented variable is needed for espelho-ponto in .env.example
- [X] T048 [P] Add or refine quickstart validation notes after implementation in specs/002-navegar-espelho-ponto/quickstart.md
- [X] T049 Run focused navigation tests under tests/unit/, tests/integration/, and tests/contract/ with `.venv/bin/python -m pytest tests/unit/test_navigation_path.py tests/unit/test_navigation_step.py tests/unit/test_navigation_result.py tests/unit/test_menu_navigation_service_success.py tests/unit/test_menu_navigation_service_failures.py tests/unit/test_menu_navigation_service_timeouts.py tests/unit/test_menu_navigation_service_security.py tests/integration/test_playwright_espelho_navigation_success.py tests/integration/test_playwright_espelho_navigation_failures.py tests/integration/test_espelho_navigation_result_persistence.py tests/contract/test_navigation_result_schema.py tests/contract/test_cli_espelho_success.py tests/contract/test_cli_espelho_failures.py tests/contract/test_cli_espelho_json_output.py`
- [X] T050 Run full regression suite for tests/ with `.venv/bin/python -m pytest`
- [X] T051 Review generated navigation JSON files in data/runs/ and logs in logs/ to confirm no password, cookie, raw HTML, screenshot, trace, or token persistence

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

- **US1 - Acessar espelho do ponto apos login**: Start after Phase 2; no dependency on US2 or US3.
- **US2 - Informar bloqueios de permissao ou menu ausente**: Start after Phase 2; uses the same service/adapter boundaries as US1.
- **US3 - Registrar resultado da navegacao**: Start after Phase 2; validates persistence for US1 and US2 outcomes.

### Within Each User Story

- Write tests first and verify they fail for the expected reason.
- Implement or extend models before services.
- Implement services before app/CLI orchestration.
- Extend app orchestration before CLI contract output.
- Complete each story checkpoint before moving to the next priority when working sequentially.

### Parallel Opportunities

- T002, T003, and T004 can run in parallel after T001.
- T005 through T009 can run in parallel because they are separate test files.
- T010 through T012 can run in parallel because they create separate model files.
- US1 tests T016 through T019 can run in parallel.
- US2 tests T026 through T030 can run in parallel.
- US3 tests T037 through T040 can run in parallel.
- Documentation tasks T046 through T048 can run in parallel after implementation.

---

## Parallel Example: User Story 1

```bash
# Launch tests for User Story 1 together:
Task: "T016 [US1] Write unit tests in tests/unit/test_menu_navigation_service_success.py"
Task: "T017 [US1] Write unit tests in tests/unit/test_sigrh_browser_navigation.py"
Task: "T018 [US1] Write integration test in tests/integration/test_playwright_espelho_navigation_success.py"
Task: "T019 [US1] Write contract test in tests/contract/test_cli_espelho_success.py"

# Launch implementation slices after tests are red:
Task: "T020 [US1] Implement service in src/homologacao_ponto/services/menu_navigation_service.py"
Task: "T021 [US1] Extend adapter in src/homologacao_ponto/infrastructure/sigrh_browser.py"
```

## Parallel Example: User Story 2

```bash
# Launch negative-path tests together:
Task: "T026 [US2] Write missing-menu tests in tests/unit/test_menu_navigation_service_failures.py"
Task: "T027 [US2] Write timeout tests in tests/unit/test_menu_navigation_service_timeouts.py"
Task: "T028 [US2] Write security-state tests in tests/unit/test_menu_navigation_service_security.py"
Task: "T029 [US2] Write integration failure tests in tests/integration/test_playwright_espelho_navigation_failures.py"
Task: "T030 [US2] Write CLI failure tests in tests/contract/test_cli_espelho_failures.py"
```

## Parallel Example: User Story 3

```bash
# Launch persistence tests together:
Task: "T037 [US3] Write model serialization tests in tests/unit/test_navigation_result.py"
Task: "T038 [US3] Write writer tests in tests/unit/test_navigation_result_writer.py"
Task: "T039 [US3] Write CLI JSON tests in tests/contract/test_cli_espelho_json_output.py"
Task: "T040 [US3] Write persistence integration tests in tests/integration/test_espelho_navigation_result_persistence.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup fixtures.
2. Complete Phase 2 foundational tests and domain/persistence primitives.
3. Complete Phase 3 User Story 1 tests and implementation.
4. Stop and validate: `homologacao-ponto espelho-ponto` reaches the mocked "Espelho do Ponto" screen and exits 0.

### Incremental Delivery

1. Setup + Foundation: navigation model, schema, writer support.
2. US1: happy-path navigation to visible "Espelho do Ponto".
3. US2: missing menu, permission, timeout, blocked, expired, and destination mismatch failures.
4. US3: local JSON persistence for all handled outcomes and write-failure exit behavior.
5. Polish: docs, full regression, sensitive-data review.

### Validation Gates

1. Run focused navigation tests listed in T049.
2. Run full regression suite listed in T050.
3. Confirm quickstart behavior against mocked tests before any live SIGRH attempt.
4. Do not persist screenshots, traces, raw HTML, cookies, or credentials by default.

## Notes

- [P] tasks touch separate files or can be done without waiting on another incomplete task in the same phase.
- [US1], [US2], and [US3] map directly to the prioritized user stories in spec.md.
- Existing crawl behavior must remain compatible while adding `espelho-ponto`.
- Routine automated tests must use mocked SIGRH pages and must not contact the live SIGRH.
