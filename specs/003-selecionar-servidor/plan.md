# Implementation Plan: Selecionar Servidor no Espelho de Ponto

**Branch**: `002-navegar-espelho-ponto` | **Date**: 2026-05-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-selecionar-servidor/spec.md`

## Summary

Extend the existing SIGRH Espelho de Ponto flow so that, after a server search
result list is visible, the system selects the correct "Selecionar Servidor"
control for the requested server and stops only when the daily point page
identifies that selected server. The feature preserves the existing security
posture, avoids ambiguous selections, and writes a local JSON result for
successful and handled failed selection attempts.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: Existing `playwright` browser automation,
`python-dotenv` for credentials, `pytest`, `pytest-playwright`, `pytest-mock`,
and `jsonschema` for tests/contracts  
**Storage**: Local JSON file per server-selection execution, using the existing
output directory pattern and no credential, cookie, screenshot, trace, or raw
HTML persistence  
**Testing**: pytest with unit tests, route-mocked Playwright integration tests,
and JSON/CLI contract tests written before implementation  
**Target Platform**: Local command-line execution on developer/user workstation
with installed Playwright Chromium browser binaries  
**Project Type**: Single Python CLI/library project  
**Performance Goals**: Complete selection after visible search results in up to
30 seconds for normal SIGRH responses; full login, navigation, search, and
selection remains bounded by the existing conservative interaction limits  
**Constraints**: Python-only implementation; no CAPTCHA/MFA/anti-bot bypass; no
automatic reauthentication after session expiration; minimum 2 seconds between
SIGRH Playwright navigations/actions; no selection when results are ambiguous;
no report extraction or download in this feature  
**Scale/Scope**: One authenticated browser context per process; one requested
server and one selection result per execution; point-record parsing remains out
of scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Test-first delivery: PASS. Plan defines unit, integration, and contract tests
  for unique-result selection, missing result, ambiguous result, missing control,
  session expiration, anti-automation block, JSON persistence, and CLI output.
- Python runtime: PASS. No non-Python runtime or tooling is introduced; existing
  Python 3.12+ package and test stack are reused.
- Object-oriented design: PASS. Domain behavior will be modeled with
  `ServidorConsulta`, `ServidorResultado`, `SelecaoServidorResult`, a selection
  service, and SIGRH browser adapter methods.
- Design patterns: PASS. Adapter isolates Playwright/SIGRH result-row
  interaction, Strategy/Policy keeps name matching and ambiguity rules explicit,
  and Factory wiring remains in application assembly.
- Quality gates: PASS. Planned gates are focused pytest suites, JSON schema
  contract validation, route-mocked browser journeys, and full regression.

## Project Structure

### Documentation (this feature)

```text
specs/003-selecionar-servidor/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   └── selection-result.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── homologacao_ponto/
│   ├── cli.py
│   ├── app.py
│   ├── models/
│   │   ├── server_selection.py
│   │   ├── server_selection_result.py
│   │   └── browser_session.py
│   ├── services/
│   │   ├── server_selection_service.py
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
`src/homologacao_ponto`. Add selection-specific domain models and a
`ServerSelectionService`; extend `SigrhBrowser` with result-list inspection,
server-row matching, selection-control clicking, and final page verification.
Reuse `ResultWriter`, logging, rate limiting, app orchestration, and CLI wiring.

## Complexity Tracking

No constitution violations are required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0: Research Summary

Research decisions are recorded in [research.md](./research.md). The feature
uses visible result-row matching, strict ambiguity prevention, Playwright
route-mocked tests, existing SIGRH safety limits, and a dedicated local JSON
selection result contract.

## Phase 1: Design Summary

Design artifacts:

- [data-model.md](./data-model.md)
- [contracts/cli.md](./contracts/cli.md)
- [contracts/selection-result.schema.json](./contracts/selection-result.schema.json)
- [quickstart.md](./quickstart.md)

## Post-Design Constitution Check

- Test-first delivery: PASS. Design artifacts identify failing tests before
  implementation for all user stories and negative paths.
- Python runtime: PASS. All planned code and tests remain Python 3.12+.
- Object-oriented design: PASS. Responsibilities are separated between domain
  result models, selection service, browser adapter, result writer, and app/CLI
  orchestration.
- Design patterns: PASS. Adapter, Strategy/Policy, and Factory usage are scoped
  to concrete variation in SIGRH row interaction, name matching, destination
  checks, and application wiring.
- Quality gates: PASS. Quickstart documents focused and full pytest commands;
  no unresolved constitution exceptions remain.
