# Research: Navegacao ate Espelho do Ponto

## Menu Navigation Approach

Decision: Reuse the existing Playwright-backed `SigrhBrowser` adapter and add
menu navigation methods that click visible menu labels in the specified order:
"Chefia de Unidade", "Homologacao de Ponto Eletronico", "Relatorio", and
"Espelho do Ponto".

Rationale: The project already isolates browser automation behind
`SigrhBrowser`, keeps a single authenticated browser context, and tests SIGRH
pages with Playwright route mocks. Extending that adapter keeps external-system
behavior replaceable in tests while avoiding direct Playwright calls in domain
services.

Alternatives considered:
- Hard-coded destination URL: rejected because the user requested menu clicks
  and SIGRH URLs can include session-specific state.
- HTML-only parsing without browser clicks: rejected because dynamic menus may
  require user-like browser interaction.
- A new browser automation dependency: rejected because Playwright already
  satisfies the need and is covered by existing tests.

## Success Detection

Decision: Treat navigation as successful only when the final page visibly shows
"Espelho do Ponto" in a title, heading, or breadcrumb.

Rationale: Visible text validates the outcome the user actually sees and avoids
false positives where a click happened but SIGRH redirected to another page. It
also produces stable mocked-page integration tests.

Alternatives considered:
- URL-only confirmation: rejected because URLs may be opaque or reused.
- Any text containing "ponto": rejected because other pages can contain that
  word.
- Click completion alone: rejected because it does not verify the destination.

## Timing And Rate Limiting

Decision: Keep the existing minimum 2-second interval between SIGRH
navigations/actions and add a 15-second maximum wait for each menu/submenu step.
The whole login plus navigation flow remains bounded by the existing 60-second
success target under normal SIGRH responses.

Rationale: This keeps traffic conservative while turning delayed menus into a
testable failure mode. A per-step cap improves diagnostics because the result
can identify exactly which menu stage failed.

Alternatives considered:
- 5-second step cap: rejected as potentially too short for a slow SIGRH page.
- 30-second step cap: rejected because it weakens the 60-second user outcome.
- Only global timeout: rejected because it makes failure attribution less clear.

## Result Persistence

Decision: Save one local JSON navigation result per execution, using the same
output-directory and write-failure posture as the existing crawl result flow.

Rationale: The project already treats local JSON output as the observable run
artifact. Reusing that contract style makes CLI behavior, support diagnostics,
and contract tests consistent.

Alternatives considered:
- Terminal-only output: rejected because it is less useful for audit and
  downstream automation.
- Log-only output: rejected because logs are diagnostic, not a stable contract.
- No persisted result: rejected because the specification requires auditing the
  final status and stage.

## Failure Handling

Decision: Return a failed navigation result for missing menus, permission
absence, destination mismatch, step timeout, and local JSON write failure; return
blocked for CAPTCHA/MFA/anti-automation detection; return partial for session
expiration during the navigation path.

Rationale: The existing crawler already distinguishes blocked and partial
states. Applying the same state vocabulary keeps the CLI and JSON contracts
predictable while giving users specific messages about whether the problem is
permission, SIGRH UI change, session expiration, or automation protection.

Alternatives considered:
- Collapse all errors into `failed`: rejected because blocked and expired states
  need different user actions.
- Automatic reauthentication: rejected by the existing security posture and
  because it can hide SIGRH session policy.

## Testing Strategy

Decision: Use TDD with unit tests for path/result/state rules, contract tests
for CLI exit codes and JSON schema, and Playwright route-mocked integration
tests for the complete menu sequence. Routine automated tests must not contact
the live SIGRH.

Rationale: Route mocks preserve deterministic tests and protect user
credentials, while still validating browser-level interactions. Unit tests keep
label normalization, timeout decisions, and result construction fast.

Alternatives considered:
- Live SIGRH tests: rejected for routine automation because they depend on a
  third-party service, credentials, permissions, and mutable UI state.
- Manual-only validation: rejected by the constitution's test-first and quality
  gate requirements.
