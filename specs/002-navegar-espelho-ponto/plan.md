# Implementation Plan: Navegacao ate Espelho do Ponto

**Branch**: `002-navegar-espelho-ponto` | **Date**: 2026-05-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-navegar-espelho-ponto/spec.md`

## Summary

Extend the existing Python SIGRH CLI/library so that, after a successful login,
it can navigate the authenticated browser session through the menu path
"Chefia de Unidade" -> "Homologacao de Ponto Eletronico" -> "Relatorio" ->
"Espelho do Ponto". The feature stops when visible title, heading, or
breadcrumb text confirms "Espelho do Ponto"; it does not generate, filter,
download, or extract report contents. Each execution writes a local JSON
navigation result recording success or the exact failure stage.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: Existing `playwright` browser automation,
`python-dotenv` for credentials, `pytest`, `pytest-playwright`, `pytest-mock`,
and `jsonschema` for tests/contracts  
**Storage**: Local JSON file per navigation execution, using the existing
output directory pattern and no credential persistence  
**Testing**: pytest with unit tests, route-mocked Playwright integration tests,
and JSON/CLI contract tests written before implementation  
**Target Platform**: Local command-line execution on developer/user workstation
with installed Playwright Chromium browser binaries  
**Project Type**: Single Python CLI/library project  
**Performance Goals**: Complete login plus menu navigation in up to 60 seconds
for normal SIGRH responses, with each menu/submenu wait capped at 15 seconds  
**Constraints**: Python-only implementation; no CAPTCHA/MFA/anti-bot bypass; no
automatic reauthentication after session expiration; minimum 2 seconds between
SIGRH Playwright navigations/actions; maximum 20 SIGRH pages/actions per run;
no raw HTML, screenshots, cookies, or credentials persisted by default  
**Scale/Scope**: One authenticated browser context per process; one navigation
path and one navigation result per execution; report generation, filtering,
download, and data extraction remain out of scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Test-first delivery: PASS. Plan defines unit, integration, and contract tests
  for success, missing menu, timeout, session expiration, blocked automation,
  JSON write failure, and CLI output before production changes.
- Python runtime: PASS. No non-Python runtime or tooling is introduced; existing
  Python 3.12+ package and test stack are reused.
- Object-oriented design: PASS. Domain behavior is modeled with
  `NavigationPath`, `NavigationStep`, `NavigationResult`,
  `MenuNavigationService`, and SIGRH browser adapter methods.
- Design patterns: PASS. Adapter isolates Playwright/SIGRH menu interaction,
  Strategy/Policy keeps label matching and destination verification explicit,
  and Factory wiring remains in the application assembly.
- Quality gates: PASS. Planned gates are `pytest`, contract validation for the
  navigation result JSON schema, and mocked Playwright journey validation for
  each user story.

## Project Structure

### Documentation (this feature)

```text
specs/002-navegar-espelho-ponto/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   └── navigation-result.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── homologacao_ponto/
│   ├── cli.py
│   ├── app.py
│   ├── models/
│   │   ├── navigation_path.py
│   │   ├── navigation_step.py
│   │   ├── navigation_result.py
│   │   └── browser_session.py
│   ├── services/
│   │   ├── menu_navigation_service.py
│   │   └── result_writer.py
│   └── infrastructure/
│       ├── sigrh_browser.py
│       ├── rate_limiter.py
│       └── logging.py
tests/
├── contract/
├── integration/
├── unit/
└── fixtures/
```

**Structure Decision**: Reuse the existing single Python package under
`src/homologacao_ponto`. Add navigation-specific domain models and a
`MenuNavigationService`; extend the existing `SigrhBrowser` adapter for visible
menu interactions and destination verification. Reuse `ResultWriter`, logging,
rate limiting, application orchestration, and CLI structure to avoid a second
persistence or browser stack.

## Complexity Tracking

No constitution violations are required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0: Research Summary

Research decisions are recorded in [research.md](./research.md). The feature
reuses Playwright route-mocked testing, conservative SIGRH interaction limits,
local JSON result persistence, visible-content success checks, and existing
blocked/partial/failed result vocabulary.

## Phase 1: Design Summary

Design artifacts:

- [data-model.md](./data-model.md)
- [contracts/cli.md](./contracts/cli.md)
- [contracts/navigation-result.schema.json](./contracts/navigation-result.schema.json)
- [quickstart.md](./quickstart.md)

## Post-Design Constitution Check

- Test-first delivery: PASS. Contracts, data model, and quickstart identify the
  observable tests required before implementation.
- Python runtime: PASS. All planned code and tests remain Python 3.12+.
- Object-oriented design: PASS. Responsibilities are separated between domain
  result models, navigation service, browser adapter, result writer, and app/CLI
  orchestration.
- Design patterns: PASS. Adapter, Strategy/Policy, and Factory usage are scoped
  to concrete variation in SIGRH UI interaction, label matching, destination
  checks, and application wiring.
- Quality gates: PASS. The quickstart documents contract, unit, integration,
  and full test commands; no unresolved constitution exceptions remain.
