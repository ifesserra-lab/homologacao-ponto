# Data Model: Navegacao ate Espelho do Ponto

## NavigationPath

Represents the fixed SIGRH menu sequence required to reach the "Espelho do
Ponto" report screen.

Fields:

- `steps`: ordered list of `NavigationStep` definitions.
- `destination_label`: canonical destination label, `Espelho do Ponto`.
- `max_step_wait_seconds`: integer, fixed at 15.

Validation rules:

- The ordered labels must be exactly: `Chefia de Unidade`,
  `Homologacao de Ponto Eletronico`, `Relatorio`, `Espelho do Ponto`.
- Label matching may normalize accents, capitalization, and repeated spaces.
- The path must not include other report or administrative destinations.

## NavigationStep

Represents one menu or submenu interaction in the path.

Fields:

- `label`: canonical label for the step.
- `position`: one-based integer order in the path.
- `status`: one of `pending`, `found`, `clicked`, `missing`, `timed_out`,
  `blocked`, `expired`, `destination_mismatch`.
- `message`: optional user-facing diagnostic for failure states.
- `completed_at`: optional date-time when the step reached a terminal state.

Validation rules:

- `position` must be unique within a `NavigationPath`.
- Terminal failure statuses require a non-empty `message`.
- A step can be marked `clicked` only after the matching visible menu element is
  found.

## NavigationResult

Represents the local JSON result written for one navigation execution.

Fields:

- `run_id`: non-empty unique identifier for the execution.
- `completed_at`: date-time when the navigation attempt ended.
- `username_ref`: username supplied for login; must not include password,
  cookies, matrícula inferred from pages, or tokens.
- `status`: one of `completed`, `failed`, `partial`, `blocked`.
- `success`: boolean derived from `status == "completed"`.
- `final_step`: canonical label of the last reached or attempted step.
- `message`: optional user-facing success or failure summary.
- `steps`: ordered list of `NavigationStep` outcomes.
- `output_path`: optional path filled after JSON persistence succeeds.

Validation rules:

- `status == "completed"` requires `success == true` and
  `final_step == "Espelho do Ponto"`.
- `status == "failed"` requires `success == false` and a non-empty `message`.
- `status == "partial"` is used when the authenticated `BrowserSession` expires
  during the navigation path.
- `status == "blocked"` is used when CAPTCHA, MFA, or anti-automation protection
  prevents automation.
- `steps` must preserve the canonical path order.

## AuthenticatedUserSession

Represents the browser session produced by the existing login feature and reused
for menu navigation.

Fields:

- `context_id`: existing browser-context identifier.
- `state`: existing session state; must be `authenticated` before navigation
  starts.
- `landing_url`: current SIGRH URL, when available.

Validation rules:

- Navigation cannot start unless the session is authenticated.
- Session expiration during navigation must stop the flow without automatic
  reauthentication.

## State Transitions

NavigationResult:

- `pending` -> `completed` when all steps are clicked and the final page visibly
  confirms "Espelho do Ponto".
- `pending` -> `failed` when a menu item is missing, a step exceeds 15 seconds,
  the final page lacks visible destination confirmation, or JSON persistence
  fails.
- `pending` -> `partial` when the authenticated session expires during the
  navigation path.
- `pending` -> `blocked` when CAPTCHA, MFA, or anti-automation protection is
  detected.
