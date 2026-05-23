# Quickstart: Baixar Espelho de Ponto em JSON

## Prerequisites

- Python environment installed with project dependencies.
- `.env` configured with authorized SIGRH credentials.
- Browser dependencies installed for Playwright.

## Run the Export Flow

```bash
.venv/bin/homologacao-ponto espelho-ponto \
  --servidor "Celio Proliciano Maioli" \
  --output-dir ./data/runs
```

Expected behavior:

- Login uses the existing credential provider.
- The existing Espelho de Ponto navigation runs.
- The server search and "Selecionar Servidor" flow runs.
- After selection succeeds, the visible espelho is exported automatically.
- The CLI prints the report JSON path and the operational result path.

Expected files:

```text
data/runs/
+-- selection-result-{run_id}.json
+-- espelho-ponto-{run_id}.json
+-- export-result-{run_id}.json
```

The generated files must not contain raw HTML, screenshots, cookies, passwords, tokens, or browser traces.

Implementation evidence:

- Focused export tests passed with 22 tests covering models, parser, service, CLI contracts, schemas, and route-backed integration.
- Full regression passed with 138 tests.

## Focused Test Commands

Create tests before implementation, then run focused suites while developing:

```bash
.venv/bin/python -m pytest \
  tests/unit/test_espelho_ponto_export.py \
  tests/unit/test_espelho_ponto_parser.py \
  tests/unit/test_espelho_export_service.py
```

```bash
.venv/bin/python -m pytest \
  tests/contract/test_espelho_ponto_export_schema.py \
  tests/contract/test_export_result_schema.py \
  tests/contract/test_cli_espelho_export.py
```

```bash
.venv/bin/python -m pytest \
  tests/integration/test_playwright_espelho_export_success.py \
  tests/integration/test_playwright_espelho_export_failures.py
```

Full quality gate:

```bash
.venv/bin/python -m pytest
```

## Manual Validation Checklist

- Valid selected server writes report JSON and result JSON.
- Empty espelho writes report JSON with `status: "empty"` and `registros: []`.
- Wrong-server page fails and does not claim exported records.
- Expired session fails without automatic reauthentication.
- CAPTCHA/MFA/anti-automation page returns blocked status.
- Output write failure returns a clear failure message.
