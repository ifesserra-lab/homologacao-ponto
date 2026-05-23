# CLI Contract: selecionar-servidor-espelho-ponto

## Command

```bash
homologacao-ponto espelho-ponto --servidor "NOME DO SERVIDOR" [--output-dir PATH] [--env-file PATH] [--headed]
```

## Inputs

- `--servidor TEXT`: optional server name to search and select after reaching
  the Espelho de Ponto form. When omitted, the command keeps the existing
  behavior and stops at the Espelho de Ponto form.
- `--output-dir PATH`: optional output directory for local JSON result files.
  Defaults to `./data/runs`. Selection files are named
  `selection-result-{run_id}.json`.
- `--env-file PATH`: optional `.env` file path. Defaults to `.env`.
- `--headed`: optional flag to show the browser window for local debugging.
  Default execution is headless.
- Environment variables:
  - `SIGRH_USERNAME`
  - `SIGRH_PASSWORD`

## Successful Output

Exit code: `0`

Stdout must include:

- Login success message.
- Navigation success message for "Espelho do Ponto".
- Server selection success message with selected server name.
- Path to generated JSON file.

The command writes one JSON file matching
[selection-result.schema.json](./selection-result.schema.json). The feature
stops after the selected server's daily point page is visibly confirmed; it does
not extract, parse, download, or summarize point records.

## Authentication Failure

Exit code: `2`

Stdout or stderr must include a clear authentication failure message. Server
selection must not start.

## Anti-Automation Block

Exit code: `3`

Stdout or stderr must explain that CAPTCHA, MFA, or anti-automation protection
prevents automation. The command must not try to bypass the protection.

## Selection Failure

Exit code: `4`

Used when the server is not found, results are ambiguous, the selection control
is unavailable, the destination is unexpected, a required SIGRH page is missing,
or the flow would leave the Espelho de Ponto scope. The command must write a
JSON result with `status: "failed"` unless JSON persistence itself fails.

## Output Write Failure

Exit code: `5`

Stdout or stderr must include a clear message that the local JSON file could not
be written. The command must not report the execution as successful.

## Session Expired During Selection

Exit code: `6`

Stdout or stderr must explain that the authenticated session expired during
server selection. The command must write a JSON result with `status: "partial"`
and must not attempt automatic reauthentication.

## Browser Setup Failure

Exit code: `7`

Stdout or stderr must explain that browser automation could not start and should
suggest installing Playwright browser binaries before any login attempt.

## Browser Automation Contract

- The command must create one isolated browser context per run.
- The default browser mode must be headless unless `--headed` is supplied.
- The browser context must be closed before the command exits.
- Browser traces, screenshots, raw HTML, cookies, and credentials must not be
  persisted by default.
- Each SIGRH navigation/action must respect the existing conservative
  interaction interval.
- The selection must only click the control associated with the matching server
  result row.

## Logging Contract

Logs must include:

- Login attempt outcome.
- Navigation to Espelho de Ponto outcome.
- Server search/selection start and end.
- Missing result, ambiguous result, missing selection control, destination
  mismatch, anti-automation detection, session expiration, browser setup
  failure, and local JSON write failure.

Logs must not include:

- Passwords.
- Raw credential files.
- Sensitive cookie values.
- Raw HTML from SIGRH pages.
