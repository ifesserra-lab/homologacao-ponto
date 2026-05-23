# Quickstart: Aplicativo de Crawler com Login SIGRH

## Prerequisites

- Python 3.12 or newer.
- Playwright browser binaries installed for the active virtual environment.
- Access to valid SIGRH credentials authorized for the user's own attendance
  data.
- No CAPTCHA/MFA requirement for the target account; if SIGRH requires it, the
  crawler must abort.

## Setup

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

## Configure Credentials

Preferred local setup:

```bash
cp .env.example .env
```

Then set:

```text
SIGRH_USERNAME=<usuario>
SIGRH_PASSWORD=<senha>
```

If `.env` is absent or incomplete, the CLI prompts for credentials at runtime.
Credential files must not be committed.

## Test-First Workflow

Write tests before implementation. Expected validation commands:

```bash
pytest
```

Focused examples:

```bash
pytest tests/unit
pytest tests/integration
pytest tests/contract
pytest --browser chromium
```

Tests must use Playwright fixtures and route-mocked SIGRH pages. They must
include:

- Successful login transition to authenticated state.
- Invalid credential failure.
- CAPTCHA/MFA/anti-automation blocked response.
- Scoped crawl that rejects out-of-scope URLs.
- JSON output contract with attendance-record fields.
- Empty attendance result producing JSON with `record_count: 0`.
- Session expiration during crawl producing partial JSON.
- Page cap reached before all in-scope pagination is exhausted producing
  partial JSON.
- Local JSON write failure producing an unsuccessful execution.
- Browser launch/setup failure before login.
- Rate limiting of at least 2 seconds and page cap of 20.
- Browser context closure after success and failure paths.

## Run The CLI

Default execution:

```bash
homologacao-ponto crawl --output-dir ./data/runs
```

Expected result:

- Authenticates with SIGRH.
- Uses a headless Playwright browser by default.
- Visits only attendance-record pages.
- Waits at least 2 seconds between SIGRH navigations/actions.
- Stops after at most 20 visited pages.
- Writes one local JSON file for the run.
- Produces a valid JSON file even when no attendance records are found.

Debug execution with a visible browser:

```bash
homologacao-ponto crawl --headed --output-dir ./data/runs
```

## Failure Behavior

- Invalid credentials: show a clear authentication error and do not crawl.
- CAPTCHA, MFA, or anti-automation: abort and explain that protection prevents
  automation.
- Session expiration during crawl: stop crawling and write partial JSON with
  already collected records.
- Page cap reached before all in-scope pagination is exhausted: stop before
  page 21 and write partial JSON with already collected records.
- JSON write failure: show a clear write error and do not treat the run as
  successful.
- Missing credentials: prompt interactively.
- Out-of-scope URL: reject before fetching when possible and log the event.
- Browser launch/setup failure: show a setup error and suggest running
  `python -m playwright install chromium`.

## Manual Validation

After implementation, run:

```bash
pytest
homologacao-ponto crawl --output-dir ./data/runs
```

Implementation validation recorded on 2026-05-20:

- `.venv/bin/pytest`: 44 passed.
- Sample completed, empty, and partial JSON fixtures validate against
  `contracts/crawl-result.schema.json`.

Verify the generated JSON contains:

- Run metadata.
- Username reference without password.
- Record count.
- Visited page count.
- Status value: `completed`, `partial`, `failed`, or `blocked`.
- Attendance records with point date, entry/exit times, source URL, and
  collected timestamp.
