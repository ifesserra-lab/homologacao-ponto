# Research: Aplicativo de Crawler com Login SIGRH

## Browser Automation

Decision: Use Playwright for Python behind a `SigrhBrowser` adapter.

Rationale: The user explicitly requested Playwright. Playwright's Python
library supports browser automation through sync and async APIs, and its pytest
plugin provides browser/page fixtures that fit the project's TDD workflow. A
browser adapter keeps Playwright-specific page, context, locator, and navigation
details away from domain services.

Alternatives considered:
- `requests.Session`: rejected because the user wants Playwright and SIGRH may
  depend on browser behavior beyond simple form POSTs.
- Selenium: rejected because Playwright is the selected browser automation
  dependency and has first-class Python/pytest support.

## Playwright API Style

Decision: Use Playwright's synchronous Python API for the first implementation.

Rationale: The CLI flow is single-user and sequential, and the synchronous API
keeps service code and tests simpler. The adapter boundary allows moving to the
async API later if there is a concrete need.

Alternatives considered:
- Async Playwright API: deferred because the feature has no concurrency
  requirement and only one browser context per run.

## Browser Context And Session State

Decision: Create one isolated browser context per crawler run and close it at
the end of the execution.

Rationale: A per-run context keeps cookies/session state isolated, maps cleanly
to the `BrowserSession` model, and prevents accidental credential/session reuse.

Alternatives considered:
- Persistent browser profile: rejected for MVP because credential/session
  persistence is not required and may create privacy risk.
- Shared context across runs: rejected because each execution should have a
  clean, testable boundary.

## Playwright Testing Strategy

Decision: Use `pytest`, `pytest-playwright`, Playwright page/context fixtures,
and route mocking for SIGRH HTML responses.

Rationale: Route mocking lets tests simulate login success, invalid
credentials, attendance pages, CAPTCHA/MFA blocks, out-of-scope navigation, and
page-cap behavior without contacting SIGRH. This supports TDD and keeps tests
deterministic.

Alternatives considered:
- Live SIGRH tests: rejected for routine automation because they depend on
  credentials, network, and third-party availability.
- Parser-only fixture tests: retained for unit tests but insufficient for
  browser navigation and session behavior.

## Credential Loading

Decision: Load `SIGRH_USERNAME` and `SIGRH_PASSWORD` from environment after
optional `.env` loading, then fall back to interactive prompts when missing.

Rationale: This matches the spec, avoids default credential persistence, and is
straightforward to test by patching environment variables and prompt providers.

Alternatives considered:
- Required `.env`: rejected because the spec requires interactive fallback.
- Local keyring persistence: deferred because persistence requires explicit
  consent and is outside the MVP path.

## Result Persistence

Decision: Write one JSON file per execution through a `ResultWriter` adapter.

Rationale: Local JSON gives a deterministic contract for tests and user access
without introducing database migrations or multi-user storage.

Empty result pages still produce a successful JSON artifact with
`record_count: 0`, an empty `records` list, and a clear no-records message. If
the local JSON file cannot be written, the execution is unsuccessful and must
surface a clear write-failure message instead of falling back silently.

Alternatives considered:
- Terminal-only output: rejected because the clarified spec requires local JSON.
- SQLite: rejected for MVP because the feature only needs one output artifact
  per run and no query model yet.
- Automatic fallback to terminal or temporary directory: rejected because it can
  hide persistence failures from the user.

## Session Expiration During Crawl

Decision: If the `BrowserSession` expires during crawl, stop crawling and write
a partial JSON result with status `partial`, already collected records, and a
session-expired message.

Rationale: This preserves useful collected data without attempting automatic
reauthentication during a sensitive authenticated flow.

Alternatives considered:
- Automatic reauthentication: rejected because it changes the user's active
  session without explicit consent and can mask SIGRH session policy.
- Dropping partial data: rejected because it loses traceable results already
  collected within the authorized session.

## Rate Limiting And Page Cap

Decision: Enforce a minimum 2-second interval between Playwright navigations or
SIGRH-triggering actions and stop after 20 visited pages per execution.

Rationale: The spec requires conservative traffic behavior. A dedicated
`RateLimiter` is easy to unit test with a fake clock and keeps crawl policy
visible even though Playwright controls the browser.

Alternatives considered:
- No limit: rejected because it weakens safety and testability.
- Fully configurable policy: deferred until there is a user need for different
  crawl profiles.

## Anti-Automation Handling

Decision: Detect CAPTCHA, MFA, or anti-automation signals in the page and abort
the run with a clear user-facing message.

Rationale: The spec explicitly forbids bypassing protections. Treating these as
terminal states avoids unsafe retry loops and prevents Playwright from being
used to work around SIGRH controls.

Alternatives considered:
- Manual browser handoff: rejected for MVP because it complicates UX and can
  blur the no-bypass boundary.
- Automatic retry: rejected because it may increase load and still cannot solve
  MFA/CAPTCHA safely.

## Design Patterns

Decision: Use Adapter for Playwright/browser automation and persistence,
Strategy for HTML extraction/rate limiting policies, and Factory for CLI
assembly.

Rationale: These patterns address real variation points while keeping the code
testable and aligned with the project constitution.

Alternatives considered:
- Flat procedural Playwright script: rejected because it would mix browser I/O,
  parsing, policy, and persistence, making TDD and mocking harder.
- Repository pattern: not used for MVP because there is no database or query
  storage model.
