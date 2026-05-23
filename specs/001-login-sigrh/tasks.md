# Tasks: Aplicativo de Crawler com Login SIGRH

**Input**: Design documents from `/specs/001-login-sigrh/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Mandatory by project constitution and feature spec. Write each test task first and verify it fails before the matching implementation task.

**Organization**: Tasks are grouped by independently testable user story, with shared setup/foundation first and operational policy after the story slices.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: User story label used only inside user-story phases.
- Every task includes concrete file paths.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the Python package, development tooling, and baseline project structure.

- [X] T001 Create Python package and test directory structure from the implementation plan in src/homologacao_ponto/ and tests/
- [X] T002 Create pyproject.toml with Python 3.12+, package metadata, console script homologacao-ponto, and dependencies playwright, python-dotenv, pytest, pytest-playwright, pytest-mock, and jsonschema
- [X] T003 [P] Create README.md with feature overview, Playwright setup, credential warning, no-bypass policy, and link to specs/001-login-sigrh/quickstart.md
- [X] T004 [P] Create .env.example with SIGRH_USERNAME and SIGRH_PASSWORD placeholders
- [X] T005 [P] Configure pytest markers and default test paths in pyproject.toml for unit, integration, and contract tests
- [X] T006 [P] Create tests/fixtures/sigrh_pages.py with route-mocked HTML fixtures for login success, login failure, attendance records, empty attendance, session expired, and anti-automation pages
- [X] T007 [P] Create tests/fixtures/clock.py with fake clock and sleeper helpers for rate-limit tests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared domain models, adapters, and test utilities required by every story.

**CRITICAL**: No user story implementation can begin until this phase is complete.

### Tests First

- [X] T008 [P] Write unit tests for Credential validation and secret-safe representation in tests/unit/test_credential.py
- [X] T009 [P] Write unit tests for BrowserSession states anonymous, authenticated, failed, blocked, and expired in tests/unit/test_browser_session.py
- [X] T010 [P] Write unit tests for CrawlScope allowed URL checks, 2-second interval value, and 20-page cap in tests/unit/test_crawl_scope.py
- [X] T011 [P] Write unit tests for AttendanceRecord required fields and source URL validation in tests/unit/test_attendance_record.py
- [X] T012 [P] Write unit tests for CrawlResult statuses completed, partial, failed, and blocked in tests/unit/test_crawl_result.py
- [X] T013 [P] Write unit tests for RateLimiter with fake clock and sleeper in tests/unit/test_rate_limiter.py
- [X] T014 [P] Write unit tests for redacting passwords and cookie values from logs in tests/unit/test_logging_redaction.py

### Implementation

- [X] T015 [P] Implement Credential model in src/homologacao_ponto/models/credential.py
- [X] T016 [P] Implement BrowserSession model with terminal blocked and expired states in src/homologacao_ponto/models/browser_session.py
- [X] T017 [P] Implement CrawlScope model with SIGRH attendance URL rules in src/homologacao_ponto/models/crawl_scope.py
- [X] T018 [P] Implement AttendanceRecord model in src/homologacao_ponto/models/attendance_record.py
- [X] T019 [P] Implement CrawlResult model with record_count consistency and status validation in src/homologacao_ponto/models/crawl_result.py
- [X] T020 [P] Implement RateLimiter with injectable clock and sleeper in src/homologacao_ponto/infrastructure/rate_limiter.py
- [X] T021 [P] Implement local logging configuration with credential redaction in src/homologacao_ponto/infrastructure/logging.py
- [X] T022 Create package exports in src/homologacao_ponto/__init__.py, src/homologacao_ponto/models/__init__.py, src/homologacao_ponto/services/__init__.py, and src/homologacao_ponto/infrastructure/__init__.py

**Checkpoint**: Shared models and utilities are tested and ready for story work.

---

## Phase 3: User Story 1 - Login básico (Priority: P1) MVP

**Goal**: Authenticate with valid credentials and mark the browser session as authenticated.

**Independent Test**: With route-mocked SIGRH login success HTML, the CLI/service loads credentials, submits the login form through Playwright, and returns authenticated state without logging the password.

### Tests for User Story 1

- [X] T023 [P] [US1] Write unit tests for environment and interactive credential loading in tests/unit/test_credential_provider.py
- [X] T024 [P] [US1] Write unit tests for successful login result mapping in AuthenticationService using fake SigrhBrowser in tests/unit/test_authentication_service_success.py
- [X] T025 [P] [US1] Write integration test for Playwright route-mocked successful login in tests/integration/test_playwright_login_success.py
- [X] T026 [P] [US1] Write CLI contract test for successful command output and exit code 0 with fake application flow in tests/contract/test_cli_success.py
- [X] T027 [P] [US1] Write unit test proving no credential file is persisted without explicit consent in tests/unit/test_credential_persistence_policy.py

### Implementation for User Story 1

- [X] T028 [P] [US1] Implement CredentialProvider for .env loading and interactive fallback in src/homologacao_ponto/infrastructure/credential_provider.py
- [X] T029 [P] [US1] Implement SigrhBrowser adapter for Playwright launch, isolated browser context creation, login navigation, and context closing in src/homologacao_ponto/infrastructure/sigrh_browser.py
- [X] T030 [US1] Implement AuthenticationService success flow and safe display messages in src/homologacao_ponto/services/authentication_service.py
- [X] T031 [US1] Implement application factory and run orchestration shell in src/homologacao_ponto/app.py
- [X] T032 [US1] Implement CLI crawl command with --output-dir, --env-file, and --headed options in src/homologacao_ponto/cli.py
- [X] T033 [US1] Add login success logging without passwords in src/homologacao_ponto/services/authentication_service.py

**Checkpoint**: User Story 1 is independently functional and testable as the MVP login slice.

---

## Phase 4: User Story 2 - Falha de autenticação (Priority: P2)

**Goal**: Reject invalid credentials with a clear message and do not start crawling.

**Independent Test**: With route-mocked SIGRH login failure HTML, the service returns failed state, CLI exits with code 2, no crawl pages are visited, and no success JSON is created.

### Tests for User Story 2

- [X] T034 [P] [US2] Write unit tests for login failure detection in AuthenticationService using fake SigrhBrowser in tests/unit/test_authentication_service_failure.py
- [X] T035 [P] [US2] Write integration test for Playwright route-mocked invalid credential response in tests/integration/test_playwright_login_failure.py
- [X] T036 [P] [US2] Write CLI contract test for authentication failure exit code 2 and no output JSON in tests/contract/test_cli_auth_failure.py
- [X] T037 [P] [US2] Write unit test proving CrawlerService is not called after failed authentication in tests/unit/test_app_auth_failure_flow.py

### Implementation for User Story 2

- [X] T038 [US2] Extend SigrhBrowser login result parsing for invalid credential page signals in src/homologacao_ponto/infrastructure/sigrh_browser.py
- [X] T039 [US2] Extend AuthenticationService failure flow and safe message handling in src/homologacao_ponto/services/authentication_service.py
- [X] T040 [US2] Extend application orchestration to stop before crawl on failed login in src/homologacao_ponto/app.py
- [X] T041 [US2] Extend CLI failure handling to return exit code 2 and skip result writing in src/homologacao_ponto/cli.py

**Checkpoint**: User Stories 1 and 2 work independently without starting crawl on failed login.

---

## Phase 5: User Story 3 - Crawl após login (Priority: P3)

**Goal**: Crawl only authenticated attendance-record pages and write one local JSON result file per execution.

**Independent Test**: With route-mocked authenticated attendance pages, the crawler visits only in-scope URLs, extracts attendance records, writes one schema-valid JSON file, and handles empty results and write failures as specified.

### Tests for User Story 3

- [X] T042 [P] [US3] Write unit tests for AttendanceParser extracting point date, entry_times, exit_times, source_url, and collected_at from page snapshots in tests/unit/test_attendance_parser.py
- [X] T043 [P] [US3] Write unit tests for ResultWriter successful JSON output and record_count validation in tests/unit/test_result_writer_success.py
- [X] T044 [P] [US3] Write unit tests for ResultWriter local JSON write failure in tests/unit/test_result_writer_failure.py
- [X] T045 [P] [US3] Write contract tests validating completed and empty JSON against specs/001-login-sigrh/contracts/crawl-result.schema.json in tests/contract/test_crawl_result_schema.py
- [X] T046 [P] [US3] Write integration test for scoped Playwright crawl with route-mocked attendance pages in tests/integration/test_playwright_attendance_crawl.py
- [X] T047 [P] [US3] Write integration test for empty attendance result producing record_count 0 and message "nenhum registro encontrado" in tests/integration/test_playwright_empty_attendance.py
- [X] T048 [P] [US3] Write unit test for rejecting out-of-scope URLs before navigation in tests/unit/test_crawler_scope_enforcement.py
- [X] T049 [P] [US3] Write CLI contract test for output write failure exit code 5 and clear error in tests/contract/test_cli_output_write_failure.py

### Implementation for User Story 3

- [X] T050 [P] [US3] Implement SigrhPageSnapshot capture helper in src/homologacao_ponto/infrastructure/sigrh_browser.py
- [X] T051 [P] [US3] Implement AttendanceParser strategy in src/homologacao_ponto/infrastructure/attendance_parser.py
- [X] T052 [P] [US3] Implement ResultWriter JSON persistence and write-failure exception in src/homologacao_ponto/services/result_writer.py
- [X] T053 [US3] Implement CrawlerService scoped navigation, page counting, parsing, empty-result handling, and result aggregation in src/homologacao_ponto/services/crawler_service.py
- [X] T054 [US3] Wire authenticated crawl and JSON output into application orchestration in src/homologacao_ponto/app.py
- [X] T055 [US3] Extend CLI success output to include visited page count, record count, and JSON path in src/homologacao_ponto/cli.py
- [X] T056 [US3] Extend CLI output write failure handling to return exit code 5 in src/homologacao_ponto/cli.py

**Checkpoint**: Login plus scoped attendance crawl produces a contract-valid JSON file for records and empty-result runs.

---

## Phase 6: Cross-Cutting Security, Session, Rate Limit, and Browser Policy

**Goal**: Enforce anti-automation abort behavior, session-expired partial output, 2-second navigation spacing, 20-page cap, browser context closure, and sensitive-data safety across all stories.

**Independent Test**: Mocked CAPTCHA/MFA pages abort with exit code 3, mocked session expiration writes partial JSON and exits 6, mocked page-cap overflow stops before page 21, and browser context closes on success and failure.

### Tests

- [X] T057 [P] Write unit tests for CAPTCHA/MFA/anti-automation detection in tests/unit/test_anti_automation_detection.py
- [X] T058 [P] Write integration test for Playwright route-mocked anti-automation page aborting without bypass attempts in tests/integration/test_playwright_anti_automation_abort.py
- [X] T059 [P] Write unit test for session expiration during crawl producing partial CrawlResult in tests/unit/test_crawler_session_expired.py
- [X] T060 [P] Write contract test validating session-expired and page-cap partial JSON against specs/001-login-sigrh/contracts/crawl-result.schema.json in tests/contract/test_crawl_result_partial_schema.py
- [X] T061 [P] Write CLI contract test for session expired exit code 6 and partial JSON path in tests/contract/test_cli_session_expired.py
- [X] T062 [P] Write unit test for 20-page cap enforcement and partial result behavior in CrawlerService in tests/unit/test_crawler_page_cap.py
- [X] T063 [P] Write unit test for 2-second RateLimiter use before each SIGRH navigation/action in tests/unit/test_crawler_rate_limit.py
- [X] T064 [P] Write integration test that browser context closes after success, auth failure, blocked, write failure, and expired runs in tests/integration/test_playwright_context_closure.py
- [X] T065 [P] Write unit test that logs and result JSON never include SIGRH_PASSWORD in tests/unit/test_sensitive_data_redaction.py

### Implementation

- [X] T066 Implement anti-automation signal detection in src/homologacao_ponto/infrastructure/sigrh_browser.py
- [X] T067 Extend AuthenticationService and CrawlerService blocked-state handling in src/homologacao_ponto/services/authentication_service.py and src/homologacao_ponto/services/crawler_service.py
- [X] T068 Extend CrawlerService to stop on BrowserSession expiration, preserve collected records, and produce partial result in src/homologacao_ponto/services/crawler_service.py
- [X] T069 Enforce RateLimiter before each SIGRH navigation/action in src/homologacao_ponto/services/crawler_service.py
- [X] T070 Enforce 20-page cap, page-cap partial result, and out-of-scope failure logging in src/homologacao_ponto/services/crawler_service.py
- [X] T071 Ensure browser context closure through application try/finally orchestration in src/homologacao_ponto/app.py
- [X] T072 Extend CLI exit codes 3, 4, 6, and 7 for blocked, scope/rate-limit/page-cap, session-expired, and browser setup failures in src/homologacao_ponto/cli.py

**Checkpoint**: Security, session, and operational policy are enforced across success and failure paths.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and project hygiene.

- [X] T073 [P] Add .gitignore entries for Python, Playwright artifacts, .env files, data/runs/, logs/, and test caches in .gitignore
- [X] T074 [P] Add Makefile commands for pytest, Playwright browser install, and quickstart validation in Makefile
- [X] T075 [P] Update README.md with command examples, exit codes, failure behavior, and no-bypass policy
- [X] T076 [P] Add sample sanitized completed crawl result fixture in tests/fixtures/crawl_result_completed_sample.json
- [X] T077 [P] Add sample sanitized empty crawl result fixture in tests/fixtures/crawl_result_empty_sample.json
- [X] T078 [P] Add sample sanitized partial crawl result fixture in tests/fixtures/crawl_result_partial_sample.json
- [X] T079 Run pytest test suite and record any remaining failures in specs/001-login-sigrh/quickstart.md
- [X] T080 Run JSON schema validation for tests/fixtures/crawl_result_completed_sample.json, tests/fixtures/crawl_result_empty_sample.json, and tests/fixtures/crawl_result_partial_sample.json against specs/001-login-sigrh/contracts/crawl-result.schema.json
- [X] T081 Review implementation against specs/001-login-sigrh/plan.md constitution checks and remove any unused abstraction

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 Setup has no dependencies.
- Phase 2 Foundational depends on Phase 1 and blocks every user story.
- Phase 3 User Story 1 depends on Phase 2 and is the MVP.
- Phase 4 User Story 2 depends on Phase 3 authentication interfaces.
- Phase 5 User Story 3 depends on Phase 3 authenticated session behavior and Phase 2 models.
- Phase 6 Cross-Cutting Security depends on the relevant service/browser/result paths from Phases 3-5.
- Phase 7 Polish depends on all intended implementation phases.

### User Story Dependencies

- US1 Login básico: independent MVP after foundation.
- US2 Falha de autenticação: depends on US1 authentication service and CLI skeleton.
- US3 Crawl após login: depends on US1 authenticated BrowserSession and shared models.

### Within Each Story

- Tests must be written and fail before implementation.
- Models and adapters precede services.
- Services precede CLI/application wiring.
- Each checkpoint must be validated before moving to the next phase.

## Parallel Opportunities

- T003-T007 can run in parallel after T001-T002 decisions are stable.
- T008-T014 can run in parallel because they touch separate unit test files.
- T015-T021 can run in parallel after their corresponding tests are written.
- T023-T027 can run in parallel before US1 implementation.
- T034-T037 can run in parallel before US2 implementation.
- T042-T049 can run in parallel before US3 implementation.
- T057-T065 can run in parallel before cross-cutting policy implementation.
- T073-T078 can run in parallel during polish.

## Parallel Example: User Story 1

```bash
Task: "T023 [US1] Write unit tests for environment and interactive credential loading in tests/unit/test_credential_provider.py"
Task: "T024 [US1] Write unit tests for successful login result mapping in tests/unit/test_authentication_service_success.py"
Task: "T025 [US1] Write integration test for Playwright route-mocked successful login in tests/integration/test_playwright_login_success.py"
Task: "T026 [US1] Write CLI contract test for successful command output and exit code 0 in tests/contract/test_cli_success.py"
Task: "T027 [US1] Write unit test proving no credential file is persisted in tests/unit/test_credential_persistence_policy.py"
```

## Parallel Example: User Story 3

```bash
Task: "T042 [US3] Write unit tests for AttendanceParser in tests/unit/test_attendance_parser.py"
Task: "T043 [US3] Write unit tests for ResultWriter success in tests/unit/test_result_writer_success.py"
Task: "T044 [US3] Write unit tests for ResultWriter write failure in tests/unit/test_result_writer_failure.py"
Task: "T045 [US3] Write contract tests for completed and empty JSON schema in tests/contract/test_crawl_result_schema.py"
Task: "T046 [US3] Write integration test for route-mocked attendance crawl in tests/integration/test_playwright_attendance_crawl.py"
Task: "T047 [US3] Write integration test for empty attendance JSON in tests/integration/test_playwright_empty_attendance.py"
Task: "T048 [US3] Write unit test for rejecting out-of-scope URLs in tests/unit/test_crawler_scope_enforcement.py"
Task: "T049 [US3] Write CLI contract test for output write failure in tests/contract/test_cli_output_write_failure.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate login success independently with unit, integration, and CLI contract tests.

### Incremental Delivery

1. Setup plus foundation creates the OO domain and Playwright adapter boundaries.
2. US1 delivers authenticated BrowserSession creation.
3. US2 adds safe failed-login behavior without crawling.
4. US3 adds scoped attendance crawl and JSON persistence.
5. Phase 6 hardens security, rate limits, session expiration, and browser lifecycle.
6. Phase 7 validates the full quickstart path and documentation.

### Parallel Team Strategy

With multiple developers:

1. Complete Phase 1 and Phase 2 together.
2. After foundation, one developer can own US1 authentication, another can prepare US2 negative-path tests, and another can prepare US3 parser/result-writer tests.
3. Keep shared files coordinated: src/homologacao_ponto/app.py, src/homologacao_ponto/cli.py, src/homologacao_ponto/infrastructure/sigrh_browser.py, and src/homologacao_ponto/services/crawler_service.py.

---

## Notes

- [P] tasks touch separate files or can be completed without blocking another task in the same phase.
- Tests are intentionally first because the constitution requires TDD.
- Use Playwright route mocking; routine automated tests must not contact the live SIGRH.
- Do not persist credentials, browser traces, screenshots, cookies, or raw HTML by default.
- Commit after each task or small logical group if using the optional git hook workflow.
