# CLI Contract: Espelho de Ponto JSON Export

## Command

```bash
homologacao-ponto espelho-ponto --servidor "<nome do servidor>" --output-dir ./data/runs
```

When `--servidor` is provided and selection succeeds, the command automatically exports the visible Espelho de Ponto to JSON.

## Inputs

- `--servidor`: required for automatic export; visible server name to search and select.
- `--output-dir`: optional; directory for local JSON outputs. Defaults to the existing command default.

## Successful Output

The command exits with code `0`, prints a concise success message, and writes:

- `espelho-ponto-{run_id}.json`: report data matching `espelho-ponto-export.schema.json`.
- `export-result-{run_id}.json`: operational result matching `export-result.schema.json`.

The stdout message includes the selected server, visible period when found, and the report JSON path.

Example:

```text
Espelho de Ponto exportado com sucesso para Celio Proliciano Maioli.
Periodo: Maio/2026
JSON: data/runs/espelho-ponto-3fdd430aa0e542fa9853b2a832d64041.json
Resultado: data/runs/export-result-3fdd430aa0e542fa9853b2a832d64041.json
```

## Empty Espelho Output

The command exits with code `0`, writes both JSON files, and uses:

- report `status`: `empty`
- report `registros`: `[]`
- result `success`: `true`
- result `status`: `empty`

## Failure Output

The command exits non-zero, writes an operational result JSON when possible, and does not declare a successful report path.

Failure classes:

- `invalid_page`: page is not a valid selected-server Espelho de Ponto.
- `wrong_server`: visible server does not match the requested server.
- `session_expired`: session expired after selection and before export.
- `anti_automation`: CAPTCHA, MFA, or automation block detected.
- `write_failed`: report or result JSON could not be written.

Recommended exit codes:

- `0`: export completed or valid empty espelho.
- `2`: authentication/session failure.
- `3`: navigation or page validation failure.
- `4`: server selection or server mismatch failure.
- `5`: anti-automation/CAPTCHA/MFA block.
- `6`: output write failure.
- `7`: unexpected export/parsing failure.

## Security Contract

Default outputs must not contain:

- Raw HTML.
- Screenshots.
- Browser traces.
- Cookies.
- Passwords.
- Tokens.
- Full credential values.
