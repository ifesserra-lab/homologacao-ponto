# Implementation Plan: Baixar Espelho de Ponto em JSON

**Branch**: `002-navegar-espelho-ponto` | **Date**: 2026-05-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-baixar-espelho-json/spec.md`

## Summary

Extend the existing `homologacao-ponto espelho-ponto --servidor "<nome>"` flow so that, after a successful "Selecionar Servidor" action, the CLI automatically extracts the visible Espelho de Ponto data and writes it to a dedicated JSON file. The operational run result remains separate and records status, selected server, visible period, final step, message, and the exported JSON path.

The implementation will add object-oriented export models, a parser dedicated to the selected espelho page, an export service that coordinates page validation and persistence, and JSON contracts that prevent raw HTML, screenshots, cookies, passwords, or tokens from being stored by default.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: Existing `playwright` for browser automation, `python-dotenv` for credentials, `pytest`/`pytest-playwright`/`jsonschema` for tests and contract validation.  
**Storage**: Local JSON files under the configured `--output-dir`; one `espelho-ponto-{run_id}.json` report file plus one operational `export-result-{run_id}.json` result file when export is attempted.  
**Testing**: pytest with TDD red/green/refactor evidence; unit tests for models/parser/service, contract tests for CLI and schemas, integration tests using Playwright route fixtures.  
**Target Platform**: Local CLI on macOS/Linux-like environments with browser automation available.  
**Project Type**: Python CLI application with domain models, services, and infrastructure adapters.  
**Performance Goals**: Generate the report JSON within 30 seconds after successful server selection in at least 95% of controlled valid test runs.  
**Constraints**: Do not reauthenticate automatically after session expiry; abort on CAPTCHA/MFA/anti-automation; do not persist raw HTML, screenshots, cookies, passwords, tokens, or traces by default; preserve visible text without calculating official balances.  
**Scale/Scope**: One authenticated browser session, one selected server, one currently visible Espelho de Ponto period per CLI run.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Test-first delivery: PASS. Tasks will start with failing unit, contract, and integration tests for each user story before production changes.
- Python runtime: PASS. The feature uses Python 3.12+ and existing Python tooling only.
- Object-oriented design: PASS. New behavior is assigned to `EspelhoPontoExport`, `RegistroDiaPonto`, `ExportacaoEspelhoResult`, `EspelhoPontoParser`, and `EspelhoExportService`.
- Design patterns: PASS. Adapter keeps Playwright page access inside `SigrhBrowser`; Facade keeps CLI orchestration in the application service; Factory-style constructors/from-page helpers normalize parsed domain objects.
- Quality gates: PASS. Validation commands are `.venv/bin/python -m pytest`, focused pytest selections for story-level tests, and JSON schema validation through contract tests.

## Project Structure

### Documentation (this feature)

```text
specs/004-baixar-espelho-json/
+-- plan.md
+-- research.md
+-- data-model.md
+-- quickstart.md
+-- contracts/
|   +-- cli.md
|   +-- espelho-ponto-export.schema.json
|   +-- export-result.schema.json
+-- tasks.md
```

### Source Code (repository root)

```text
src/homologacao_ponto/
+-- app.py
+-- cli.py
+-- infrastructure/
|   +-- espelho_ponto_parser.py
|   +-- sigrh_browser.py
+-- models/
|   +-- espelho_ponto_export.py
|   +-- espelho_ponto_record.py
|   +-- espelho_export_result.py
+-- services/
    +-- espelho_export_service.py
    +-- result_writer.py
    +-- server_selection_service.py

tests/
+-- contract/
|   +-- test_cli_espelho_export.py
|   +-- test_espelho_ponto_export_schema.py
|   +-- test_export_result_schema.py
+-- integration/
|   +-- test_playwright_espelho_export_failures.py
|   +-- test_playwright_espelho_export_success.py
+-- unit/
    +-- test_espelho_export_service.py
    +-- test_espelho_ponto_export.py
    +-- test_espelho_ponto_parser.py
```

**Structure Decision**: Keep the existing single Python package layout. Domain report objects live in `models`, browser/DOM extraction lives in `infrastructure`, orchestration lives in `services` and `app.py`, and the CLI contract remains exposed through `cli.py`.

## Complexity Tracking

No constitution violations or exceptions are required.

## Phase 0: Research Summary

See [research.md](./research.md).

Resolved decisions:

- Export data file and operational result are separate files.
- Parser extracts visible structured fields plus `textos_visiveis`, without persisting raw page markup.
- Scope is the currently visible selected-server period only.
- Failure handling distinguishes empty espelho, invalid page, wrong server, expired session, anti-automation, and write failure.
- Tests cover model contracts, parser behavior, service orchestration, CLI output, and Playwright route-backed flows.

## Phase 1: Design Summary

See [data-model.md](./data-model.md), [quickstart.md](./quickstart.md), and [contracts](./contracts/).

Post-design Constitution Check:

- Test-first delivery: PASS. Quickstart and contracts identify failing tests before implementation tasks.
- Python runtime: PASS. No non-Python component introduced.
- Object-oriented design: PASS. Responsibilities remain separated across models, service, parser adapter, and CLI orchestration.
- Design patterns: PASS. Adapter, Facade, and Factory-style construction reduce browser coupling and parsing/persistence ambiguity.
- Quality gates: PASS. Full and focused pytest commands are documented, with JSON schema validation in contract tests.
