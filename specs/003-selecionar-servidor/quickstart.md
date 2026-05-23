# Quickstart: Selecionar Servidor no Espelho de Ponto

## Prerequisites

- Python 3.12+.
- Project dependencies installed.
- Playwright Chromium browser installed.
- Authorized SIGRH credentials for a user with access to Espelho de Ponto and
  the target server result.
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

- Unique server result with a "Selecionar Servidor" control.
- Missing server result.
- Ambiguous matching server results.
- Server row without selection control.
- Final page that does not identify the selected server.
- Session expiration during selection.
- CAPTCHA/MFA/anti-automation block.
- JSON result write success and write failure.
- CLI exit codes and JSON schema validation.

Run focused tests:

```bash
.venv/bin/python -m pytest tests/unit tests/integration tests/contract
```

Focused validation after implementation:

```bash
.venv/bin/python -m pytest tests/unit/test_server_selection.py tests/unit/test_server_selection_result.py tests/unit/test_server_selection_service.py tests/unit/test_sigrh_browser_server_selection.py tests/integration/test_playwright_server_selection_success.py tests/integration/test_playwright_server_selection_failures.py tests/contract/test_selection_result_schema.py tests/contract/test_cli_server_selection.py
```

Run all tests:

```bash
.venv/bin/python -m pytest
```

After validation, review `data/runs/` and `logs/` to confirm selection results
do not persist passwords, cookies, raw HTML, screenshots, traces, or tokens.

## Expected Command

```bash
homologacao-ponto espelho-ponto --servidor "Celio Proliciano Maioli" --output-dir ./data/runs
```

Expected success behavior:

- Authenticates with SIGRH using existing credential flow.
- Navigates to Espelho de Ponto using the existing menu flow.
- Searches for the requested server in the Espelho de Ponto form.
- Selects the row-level "Selecionar Servidor" control for the unique matching
  server result.
- Confirms success only when the destination page visibly identifies the
  selected server.
- Writes `selection-result-{run_id}.json` in the configured output directory.
- Does not extract, parse, download, or summarize point records.

## Debug Browser

For local diagnosis only:

```bash
homologacao-ponto espelho-ponto --servidor "Celio Proliciano Maioli" --headed --output-dir ./data/runs
```

The normal command remains headless. Raw HTML, screenshots, traces, cookies, and
credentials must not be persisted by default.

## Failure Expectations

- Missing server: JSON status `failed`, message names the requested server,
  exit code `4`.
- Ambiguous result: JSON status `failed`, no server selected, exit code `4`.
- Missing selection control: JSON status `failed`, message explains that
  selection is unavailable, exit code `4`.
- Destination mismatch: JSON status `failed`, message explains that selected
  server confirmation was not found, exit code `4`.
- CAPTCHA/MFA/anti-automation: JSON status `blocked` when persistence succeeds,
  exit code `3`.
- Session expiration: JSON status `partial`, no automatic reauthentication, exit
  code `6`.
- JSON write failure: clear user-facing message, no success report, exit code
  `5`.
