# Data Model: Selecionar Servidor no Espelho de Ponto

## ServidorConsulta

Represents the server the user wants to select from the Espelho de Ponto result
list.

Fields:

- `requested_name`: non-empty server name provided by the user.
- `requested_identifier`: optional visible identifier such as SIAPE when the
  user supplies one.

Validation rules:

- `requested_name` must not be empty.
- Matching may normalize accents, capitalization, and repeated spaces.
- A partial name can only select automatically when it produces exactly one
  compatible result.

## ServidorResultado

Represents one row in the SIGRH server result list.

Fields:

- `display_name`: visible server name in the result row.
- `identifier`: optional visible identifier extracted from the row.
- `row_text`: normalized visible row text used for matching.
- `selection_available`: boolean indicating whether the row has a
  "Selecionar Servidor" control.

Validation rules:

- `display_name` must be present for a selectable result.
- A row is selectable only when `selection_available == true`.
- Result matching must not use global menu links or controls outside the row.

## SelecaoServidorResult

Represents the local JSON result for one server-selection attempt.

Fields:

- `run_id`: non-empty unique identifier for the execution.
- `completed_at`: date-time when the selection attempt ended.
- `username_ref`: username reference supplied for login; must not include
  passwords, cookies, tokens, or raw credential file contents.
- `requested_server`: server name requested by the user.
- `selected_server`: visible selected server name when selection succeeds.
- `selected_identifier`: optional visible identifier for the selected server.
- `status`: one of `completed`, `failed`, `partial`, `blocked`.
- `success`: boolean derived from `status == "completed"`.
- `final_step`: canonical label of the last reached or attempted step.
- `message`: optional user-facing success or failure summary.
- `output_path`: optional path filled after JSON persistence succeeds.

Validation rules:

- `status == "completed"` requires `success == true`,
  `selected_server` present, and final page confirmation for that server.
- `status == "failed"` requires `success == false` and a non-empty `message`.
- `status == "partial"` is used when the authenticated session expires during
  selection.
- `status == "blocked"` is used when CAPTCHA, MFA, or anti-automation
  protection prevents automation.
- `requested_server` must always be present.

## AuthenticatedUserSession

Represents the existing authenticated browser session reused for server
selection.

Fields:

- `context_id`: existing browser-context identifier.
- `state`: existing session state; must be `authenticated` before selection
  starts.
- `landing_url`: current SIGRH URL, when available.

Validation rules:

- Selection cannot start unless the session is authenticated.
- Session expiration during selection must stop the flow without automatic
  reauthentication.

## State Transitions

SelecaoServidorResult:

- `pending` -> `completed` when exactly one matching result is selected and the
  final page visibly identifies that server.
- `pending` -> `failed` when no result matches, multiple results match without
  unique identifier, the selection control is missing, the final page lacks
  selected-server confirmation, or JSON persistence fails.
- `pending` -> `partial` when the authenticated session expires during
  selection.
- `pending` -> `blocked` when CAPTCHA, MFA, or anti-automation protection is
  detected.
