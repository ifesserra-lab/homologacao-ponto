# Data Model: Aplicativo de Crawler com Login SIGRH

## Credential

Represents user-provided SIGRH credentials during one run.

Fields:
- `username`: string, required, non-empty.
- `password`: secret string, required, non-empty, never logged.
- `source`: enum string, one of `env` or `interactive`.
- `consent_to_persist`: boolean, default `false`.

Validation rules:
- `username` and `password` must be present before login.
- `password` must not be serialized to logs or crawl-result JSON.
- Credentials must not be persisted unless explicit consent exists.

## BrowserSession

Represents the authenticated SIGRH browser context state.

Fields:
- `state`: enum string, one of `anonymous`, `authenticated`, `failed`, `blocked`, `expired`.
- `context_id`: opaque identifier for the per-run Playwright browser context.
- `current_url`: string URL or null.
- `started_at`: ISO-8601 datetime.
- `last_navigation_at`: ISO-8601 datetime or null.
- `failure_reason`: string or null.

State transitions:
- `anonymous` -> `authenticated` after successful login detection.
- `anonymous` -> `failed` after invalid credentials or login rejection.
- `anonymous` or `authenticated` -> `blocked` after CAPTCHA, MFA, or
  anti-automation detection.
- `authenticated` -> `expired` when SIGRH redirects or displays a session
  expiration signal during crawl.

Validation rules:
- Crawling can start only from `authenticated`.
- `blocked` is terminal for the current execution.
- `expired` is terminal for the current execution and must not trigger
  automatic reauthentication.
- Browser context state must be closed at the end of a run.

## CrawlScope

Defines the allowed SIGRH pages for the MVP crawl.

Fields:
- `allowed_paths`: list of SIGRH path patterns for attendance-record pages.
- `max_pages`: integer, fixed at 20 for this feature.
- `min_navigation_interval_seconds`: integer, fixed at 2 for this feature.

Validation rules:
- A URL is eligible only when it belongs to SIGRH and matches attendance-record
  scope rules.
- Non-attendance pages must be rejected before browser navigation when possible.
- The crawler must stop at 20 visited pages.

## AttendanceRecord

Represents one extracted attendance record.

Fields:
- `point_date`: ISO-8601 date or original display date when parsing cannot
  normalize safely.
- `entry_times`: list of time strings for available entries.
- `exit_times`: list of time strings for available exits.
- `source_url`: string URL where the record was extracted.
- `collected_at`: ISO-8601 datetime.

Validation rules:
- `point_date`, `source_url`, and `collected_at` are required.
- Entry/exit lists may be empty only if the SIGRH page has no visible value for
  that side of the record.
- `source_url` must be within `CrawlScope`.
- Records parsed from malformed HTML must be discarded when any required field
  is missing; raw malformed HTML must not be persisted.

## CrawlResult

Represents the persisted output of one crawler execution.

Fields:
- `run_id`: string unique identifier for the execution.
- `collected_at`: ISO-8601 datetime for the result file creation.
- `username_ref`: string username reference without password.
- `record_count`: integer count of `records`.
- `visited_page_count`: integer, max 20.
- `records`: list of `AttendanceRecord`.
- `output_path`: local filesystem path to the JSON file.
- `status`: enum string, one of `completed`, `partial`, `failed`, `blocked`.
- `message`: string or null.

Validation rules:
- `record_count` must equal the number of records.
- `visited_page_count` must not exceed 20.
- `records` must not contain credentials or raw passwords.
- `output_path` must point to the configured output directory and use the
  `crawl-result-{run_id}.json` naming pattern when persistence succeeds.
- `username_ref` must be the provided username only, with no password, cookies,
  inferred extra identifier, raw HTML, or session token.
- `blocked` status must contain a message explaining that protection prevents
  automation.
- `completed` may contain zero records when no attendance records are found;
  in that case `record_count` must be `0`, `records` must be empty, and
  `message` must explain that no records were found.
- `partial` status is used when the `BrowserSession` expires during crawl or
  when the 20-page cap is reached before all in-scope pagination is exhausted;
  it must preserve already collected records and include the specific reason.
- `failed` status is used for unsuccessful execution paths such as local JSON
  write failure when no valid output artifact can be persisted.

## SigrhLoginResult

Represents the outcome of the login attempt.

Fields:
- `success`: boolean.
- `state`: enum string, one of `authenticated`, `failed`, `blocked`, `expired`.
- `message`: string safe for display.
- `landing_url`: string or null.
- `browser_session`: `BrowserSession` reference or null.

Validation rules:
- A blocked result must not trigger crawling.
- Messages must not include passwords or sensitive cookie values.

## SigrhPageSnapshot

Represents sanitized page content captured from Playwright for parsing.

Fields:
- `url`: source URL.
- `title`: page title or null.
- `html`: sanitized HTML string or structured text extracted from the page.
- `captured_at`: ISO-8601 datetime.

Validation rules:
- Snapshot content must not include passwords.
- Snapshots are transient parser inputs and are not persisted in the result JSON
  unless a future feature explicitly adds raw HTML storage.

## Relationships

- `Credential` is consumed by the authentication service.
- `BrowserSession` is produced by authentication and consumed by crawling.
- `CrawlScope` constrains every URL visited by the crawler.
- `SigrhPageSnapshot` objects are captured through Playwright and parsed into
  `AttendanceRecord` objects.
- `CrawlResult` aggregates `AttendanceRecord` objects and persistence metadata.
- `SigrhLoginResult` drives user-facing success, failure, and blocked messages.
