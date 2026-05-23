# Research: Selecionar Servidor no Espelho de Ponto

## Result Selection Approach

Decision: Select the server from the visible Espelho de Ponto result list by
matching the requested server against row text and clicking the
"Selecionar Servidor" control associated with that row.

Rationale: The live SIGRH page exposes the target action as a row-level link or
icon with title "Selecionar Servidor". Matching the row first prevents clicking
global menu links or unrelated controls that contain similar words.

Alternatives considered:
- Click the first "Selecionar Servidor" control blindly: rejected because it can
  choose the wrong server when multiple results appear.
- Navigate directly to a generated URL: rejected because SIGRH URLs may depend
  on server-side view state and session context.
- Require manual user click after search: rejected because the feature request
  is specifically to automate the button click.

## Name Matching And Ambiguity

Decision: Normalize accents, capitalization, and repeated whitespace when
matching server names, but require exactly one compatible result unless a visible
identifier also disambiguates the row.

Rationale: SIGRH often renders names in uppercase and can include a visible
identifier such as SIAPE in parentheses. Normalization handles harmless display
differences while the single-match rule prevents unsafe selection.

Alternatives considered:
- Exact text only: rejected because display capitalization and accents vary.
- Fuzzy partial matching across all rows: rejected because similar names can
  produce unsafe matches.
- Always pick the first compatible row: rejected because support diagnostics are
  better than selecting an ambiguous person.

## Success Detection

Decision: Treat selection as successful only when the final page visibly
identifies the selected server in the daily point page title, heading, breadcrumb
area, or main content.

Rationale: Click completion alone does not prove that SIGRH opened the intended
server. Visible confirmation matches the user-observable outcome and supports
deterministic route-mocked tests.

Alternatives considered:
- URL-only confirmation: rejected because URL and JSF view state are not stable
  enough as the user-facing source of truth.
- Presence of any point table: rejected because it may belong to another server.
- Row-click completion only: rejected because warnings, redirects, or session
  expiration can occur after the click.

## Result Persistence

Decision: Save one local JSON selection result per execution, following the same
output-directory and write-failure posture as existing crawl and navigation
results.

Rationale: Local JSON is already the project contract for auditable run output.
A dedicated result object keeps selected-server fields explicit without
overloading the navigation result.

Alternatives considered:
- Terminal-only status: rejected because it is not durable for diagnostics.
- Reusing navigation result fields only: rejected because selection needs server
  requested/selected fields.
- Persisting raw result HTML: rejected by the project's sensitive-artifact
  policy.

## Failure Handling

Decision: Return failed for missing result, ambiguous result, missing selection
control, destination mismatch, and JSON write failure; blocked for CAPTCHA/MFA
or anti-automation detection; partial for session expiration during selection.

Rationale: This mirrors the existing result vocabulary while preserving action
specific diagnostics. The user can tell whether to change the search, request
permission, retry login, or stop due to automation protection.

Alternatives considered:
- Collapse all failures into a generic error: rejected because each failure
  requires a different correction.
- Automatic reauthentication: rejected by the existing security posture.
- Selecting despite ambiguity and warning later: rejected because it can expose
  the wrong employee's point page.

## Testing Strategy

Decision: Use TDD with unit tests for name matching, result-state construction,
and service decisions; contract tests for CLI/output JSON; and Playwright
route-mocked integration tests for unique, missing, ambiguous, blocked, expired,
and destination-mismatch flows.

Rationale: Routine tests must not contact live SIGRH or rely on real personnel
data. Route mocks preserve browser-level confidence while keeping credentials
and page state out of the test suite.

Alternatives considered:
- Live SIGRH tests: rejected for routine automation because they depend on
  credentials, permissions, external availability, and mutable records.
- Manual validation only: rejected by the constitution's test-first and quality
  gate requirements.
