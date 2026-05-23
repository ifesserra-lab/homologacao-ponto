# Quickstart: Navegacao ate Espelho do Ponto

## Prerequisites

- Python 3.12+.
- Project dependencies installed.
- Playwright Chromium browser installed.
- Authorized SIGRH credentials for a user with access to "Chefia de Unidade".
- No CAPTCHA/MFA requirement for the target account; if SIGRH requires it, the
  command must abort without bypass attempts.

## Setup

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m playwright install chromium
```

Create or update `.env`:

```bash
SIGRH_USERNAME=<usuario>
SIGRH_PASSWORD=<senha>
```

Do not commit `.env` files with real credentials.

## Test-First Validation

Before implementation, create failing tests for:

- Complete route-mocked menu path to "Espelho do Ponto".
- Missing "Chefia de Unidade" and missing "Homologacao de Ponto Eletronico".
- Step timeout after 15 seconds.
- Destination page without visible title, heading, or breadcrumb
  "Espelho do Ponto".
- Session expiration during navigation.
- CAPTCHA/MFA/anti-automation block.
- JSON result write success and write failure.
- CLI exit codes and JSON schema validation.

Run focused tests:

```bash
.venv/bin/python -m pytest tests/unit tests/integration tests/contract
```

Run all tests:

```bash
.venv/bin/python -m pytest
```

Focused validation after implementation:

```bash
.venv/bin/python -m pytest tests/unit/test_navigation_path.py tests/unit/test_navigation_step.py tests/unit/test_navigation_result.py tests/unit/test_menu_navigation_service_success.py tests/unit/test_menu_navigation_service_failures.py tests/unit/test_menu_navigation_service_timeouts.py tests/unit/test_menu_navigation_service_security.py tests/integration/test_playwright_espelho_navigation_success.py tests/integration/test_playwright_espelho_navigation_failures.py tests/integration/test_espelho_navigation_result_persistence.py tests/contract/test_navigation_result_schema.py tests/contract/test_cli_espelho_success.py tests/contract/test_cli_espelho_failures.py tests/contract/test_cli_espelho_json_output.py
```

## Expected Command

```bash
homologacao-ponto espelho-ponto --output-dir ./data/runs
```

Expected success behavior:

- Authenticates with SIGRH using existing credential flow.
- Navigates menu path:
  1. Chefia de Unidade
  2. Homologacao de Ponto Eletronico
  3. Relatorio
  4. Espelho do Ponto
- Waits up to 15 seconds for each menu/submenu step.
- Confirms success only when the destination page visibly shows
  "Espelho do Ponto" in a title, heading, or breadcrumb.
- Writes `navigation-result-{run_id}.json` in the configured output directory.
- Does not generate, filter, download, or extract the report contents.

## Debug Browser

For local diagnosis only:

```bash
homologacao-ponto espelho-ponto --headed --output-dir ./data/runs
```

The normal command remains headless. Raw HTML, screenshots, traces, cookies, and
credentials must not be persisted by default.

## Failure Expectations

- Missing menu or insufficient permission: JSON status `failed`, message names
  the stage where navigation stopped, exit code `4`.
- Step timeout: JSON status `failed`, message names the timed-out stage, exit
  code `4`.
- Destination mismatch: JSON status `failed`, message explains that visible
  "Espelho do Ponto" confirmation was not found, exit code `4`.
- CAPTCHA/MFA/anti-automation: JSON status `blocked` when persistence succeeds,
  exit code `3`.
- Session expiration: JSON status `partial`, no automatic reauthentication, exit
  code `6`.
- JSON write failure: clear user-facing message, no success report, exit code
  `5`.
