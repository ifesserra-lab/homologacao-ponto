# CLI Contract: login-sigrh-crawler

## Command

```bash
homologacao-ponto crawl [--output-dir PATH] [--env-file PATH] [--headed]
```

## Inputs

- `--output-dir PATH`: optional output directory for local JSON result files.
  Defaults to `./data/runs`. Files are named `crawl-result-{run_id}.json`.
- `--env-file PATH`: optional `.env` file path. Defaults to `.env`.
- `--headed`: optional flag to show the Playwright browser window for local
  debugging. Default execution is headless.
- Environment variables:
  - `SIGRH_USERNAME`
  - `SIGRH_PASSWORD`

If credentials are missing after `.env` loading, the command prompts
interactively.

## Successful Output

Exit code: `0`

Stdout must include:

- Login success message.
- Number of visited pages.
- Number of attendance records collected.
- Path to generated JSON file.

The command writes one JSON file matching
[crawl-result.schema.json](./crawl-result.schema.json).

## Authentication Failure

Exit code: `2`

Stdout or stderr must include a clear authentication failure message. The
crawler must not visit attendance pages and must not create a success result
file.

## Anti-Automation Block

Exit code: `3`

Stdout or stderr must explain that CAPTCHA, MFA, or anti-automation protection
prevents automation. The crawler must not try to bypass the protection and must
not continue crawling.

## Browser Automation Contract

- The command must create one isolated Playwright browser context per run.
- The default browser mode must be headless unless `--headed` is supplied.
- The browser context must be closed before the command exits.
- Browser traces, screenshots, or raw HTML must not be persisted by default
  because they can contain sensitive data.

## Scope Or Rate-Limit Failure

Exit code: `4`

Used for internal policy failures such as attempted out-of-scope URL access or
page-cap violation. These failures must be logged locally. If the page cap is
reached after collecting records and before all in-scope pagination is
exhausted, the command must write a partial JSON result with status `partial`
and a page-cap message.

## Output Write Failure

Exit code: `5`

Stdout or stderr must include a clear message that the local JSON file could
not be written. The command must not report the run as successful.

## Session Expired During Crawl

Exit code: `6`

Stdout or stderr must explain that the `BrowserSession` expired during crawl.
The command must write a partial JSON result with status `partial`, preserve
already collected records, and must not attempt automatic reauthentication.

## Browser Setup Failure

Exit code: `7`

Stdout or stderr must explain that the browser automation dependency could not
start and should suggest installing the Playwright browser binaries before any
login attempt.

## Empty Result

Exit code: `0`

When no attendance records are found, the command must still write a JSON file
matching [crawl-result.schema.json](./crawl-result.schema.json) with
`status: "completed"`, `record_count: 0`, an empty `records` list, and a clear
no-records message.

## Logging Contract

Logs must include:

- Login attempt outcome.
- Crawl start and end.
- Visited page count and browser-context close outcome.
- Rejected out-of-scope URLs.
- CAPTCHA/MFA/anti-automation detection.
- Session expiration during crawl.
- Page cap reached before all in-scope pagination is exhausted.
- Browser setup failure.
- Local JSON write failure.

Logs must not include:

- Passwords.
- Raw credential files.
- Sensitive cookie values.
