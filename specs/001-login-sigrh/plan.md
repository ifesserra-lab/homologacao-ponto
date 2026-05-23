# Implementation Plan: Aplicativo de Crawler com Login SIGRH

**Branch**: `001-login-sigrh` | **Date**: 2026-05-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-login-sigrh/spec.md`

## Summary

Build a Python 3.12+ CLI/library crawler that uses Playwright for browser
automation against the SIGRH login page, maintains an authenticated
`BrowserSession`, collects only the authenticated user's attendance records,
and writes one local JSON result file per run. The crawler must preserve a
stable output contract for completed, empty, partial, failed, and blocked
outcomes: empty attendance pages still produce JSON with `record_count: 0`,
session expiration during crawl produces a `partial` JSON, and output write
failure is a terminal unsuccessful execution.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: `playwright` for browser automation, `pytest-playwright` for browser fixtures, `python-dotenv` for optional `.env` loading, `pytest` and `pytest-mock` for tests  
**Storage**: Local JSON file per crawler execution when persistence succeeds; credentials are not persisted by default  
**Testing**: pytest with TDD red/green/refactor evidence and Playwright page/context fixtures  
**Target Platform**: Local command-line execution on developer/user workstation with installed Playwright browser binaries  
**Project Type**: Single Python CLI/library project  
**Performance Goals**: Complete login + scoped crawl in up to 60 seconds for the MVP scope when no more than 20 pages are visited and the SIGRH responds normally  
**Constraints**: Minimum 2 seconds between SIGRH Playwright navigations/actions, maximum 20 pages per run, no CAPTCHA/MFA/anti-bot bypass, no automatic reauthentication after session expiration, no password logging, no credential persistence without explicit consent  
**Scale/Scope**: One authenticated browser context per process; attendance-record pages only; no scheduling, background service, multi-user storage, or database in this feature

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Test-first delivery: PASS. Each user story has failing-test targets and the
  tasks template requires tests before implementation.
- Python runtime: PASS. Plan uses Playwright's Python package with Python 3.12+.
- Object-oriented design: PASS. Domain model separates `Credential`,
  `BrowserSession`, `CrawlScope`, `AttendanceRecord`, `CrawlResult`, and
  services/adapters.
- Design patterns: PASS. Adapter isolates Playwright/SIGRH browser automation
  and local persistence, Strategy isolates parsing/rate-limiting variation if
  SIGRH markup changes, Factory constructs the CLI application from
  environment/configuration.
- Quality gates: PASS. Planned commands are `pytest`, Playwright fixture tests,
  formatter/linter command selected during setup, and quickstart validation
  with mocked SIGRH pages.

## Project Structure

### Documentation (this feature)

```text
specs/001-login-sigrh/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   └── crawl-result.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── homologacao_ponto/
│   ├── __init__.py
│   ├── cli.py
│   ├── app.py
│   ├── models/
│   │   ├── credential.py
│   │   ├── browser_session.py
│   │   ├── crawl_scope.py
│   │   ├── attendance_record.py
│   │   └── crawl_result.py
│   ├── services/
│   │   ├── authentication_service.py
│   │   ├── crawler_service.py
│   │   └── result_writer.py
│   └── infrastructure/
│       ├── credential_provider.py
│       ├── sigrh_browser.py
│       ├── attendance_parser.py
│       ├── rate_limiter.py
│       └── logging.py
tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Use a single Python package under `src/homologacao_ponto`
with unit, integration, and contract tests under `tests/`. The CLI is a thin
entry point; behavior lives in services, domain models, and infrastructure
adapters. Playwright access is isolated in `SigrhBrowser` so domain tests can
use fakes while integration tests use Playwright page/context fixtures.

## Complexity Tracking

No constitution violations are required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0: Research Summary

Research decisions are recorded in [research.md](./research.md). The updated
decisions include Playwright browser automation, no-bypass security posture,
empty-result JSON, partial JSON on session expiration, and terminal output
write failures.

## Phase 1: Design Summary

Design artifacts:

- [data-model.md](./data-model.md)
- [contracts/cli.md](./contracts/cli.md)
- [contracts/crawl-result.schema.json](./contracts/crawl-result.schema.json)
- [quickstart.md](./quickstart.md)

## Post-Design Constitution Check

- Test-first delivery: PASS. Contracts and quickstart define observable outputs
  and failure modes that can be tested before implementation.
- Python runtime: PASS. All artifacts target Python 3.12+ and Playwright's
  Python APIs.
- Object-oriented design: PASS. Data model and source layout define class
  responsibilities and adapter boundaries.
- Design patterns: PASS. Adapter, Strategy, and Factory usage is justified and
  scoped to browser automation, parsing, rate limiting, persistence, and CLI
  assembly.
- Quality gates: PASS. Quickstart defines Playwright browser installation,
  unit/integration/contract test commands, and validation commands; no
  unresolved constitution exceptions remain.
