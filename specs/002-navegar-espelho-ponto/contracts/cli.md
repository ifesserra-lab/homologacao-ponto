# CLI Contract: navegar-espelho-ponto

## Command

```bash
homologacao-ponto espelho-ponto [--output-dir PATH] [--env-file PATH] [--headed]
```

## Inputs

- `--output-dir PATH`: optional output directory for local JSON navigation
  result files. Defaults to `./data/runs`. Files are named
  `navigation-result-{run_id}.json`.
- `--env-file PATH`: optional `.env` file path. Defaults to `.env`.
- `--headed`: optional flag to show the browser window for local debugging.
  Default execution is headless.
- Environment variables:
  - `SIGRH_USERNAME`
  - `SIGRH_PASSWORD`

If credentials are missing after `.env` loading, the command prompts
interactively using the existing credential behavior.

## Successful Output

Exit code: `0`

Stdout must include:

- Login success message.
- Navigation success message for "Espelho do Ponto".
- Final step reached.
- Path to generated JSON file.

The command writes one JSON file matching
[navigation-result.schema.json](./navigation-result.schema.json). The feature
stops after the "Espelho do Ponto" screen is visibly confirmed; it does not
generate, download, filter, or extract the report.

## Authentication Failure

Exit code: `2`

Stdout or stderr must include a clear authentication failure message. The
navigation must not start and no success navigation result may be reported.

## Anti-Automation Block

Exit code: `3`

Stdout or stderr must explain that CAPTCHA, MFA, or anti-automation protection
prevents automation. The command must not try to bypass the protection.

## Navigation Failure

Exit code: `4`

Used when a required menu item is missing, the user lacks the required profile,
the step wait exceeds 15 seconds, the destination is unexpected, or the flow
would leave the requested "Espelho do Ponto" path. The command must write a
JSON result with `status: "failed"` unless JSON persistence itself fails.

## Output Write Failure

Exit code: `5`

Stdout or stderr must include a clear message that the local JSON file could not
be written. The command must not report the execution as successful.

## Session Expired During Navigation

Exit code: `6`

Stdout or stderr must explain that the authenticated session expired during menu
navigation. The command must write a JSON result with `status: "partial"` and
must not attempt automatic reauthentication.

## Browser Setup Failure

Exit code: `7`

Stdout or stderr must explain that the browser automation dependency could not
start and should suggest installing the Playwright browser binaries before any
login attempt.

## Browser Automation Contract

- The command must create one isolated Playwright browser context per run.
- The default browser mode must be headless unless `--headed` is supplied.
- The browser context must be closed before the command exits.
- Browser traces, screenshots, raw HTML, cookies, and credentials must not be
  persisted by default.
- Each SIGRH navigation/action must respect the existing conservative
  interaction interval.
- Each required menu/submenu may wait up to 15 seconds before failing.

## Logging Contract

Logs must include:

- Login attempt outcome.
- Navigation start and end.
- Each required navigation step outcome.
- Missing menu or permission-related failure.
- Step timeout.
- Destination mismatch.
- CAPTCHA/MFA/anti-automation detection.
- Session expiration during navigation.
- Browser setup failure.
- Local JSON write failure.

Logs must not include:

- Passwords.
- Raw credential files.
- Sensitive cookie values.
- Raw HTML from SIGRH pages.
