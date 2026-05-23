# Data Model: Baixar Espelho de Ponto em JSON

## ServidorSelecionado

Represents the server whose Espelho de Ponto page is currently open.

Fields:

- `nome`: visible server name, required, non-empty string.
- `identificador`: visible identifier such as matricula/SIAPE when present, optional string.
- `texto_visivel`: full visible server label when useful for diagnostics, optional string.

Validation rules:

- `nome` must match the selected server requested by the flow after normalization for whitespace/case/accent-insensitive comparison where existing selection logic supports it.
- Absence of both `nome` and `texto_visivel` means the page is invalid for export.

## RegistroDiaPonto

Represents the visible data for one day in the espelho.

Fields:

- `data`: visible date in `YYYY-MM-DD` when parseable, otherwise the visible date text, required.
- `dia_semana`: visible weekday when present, optional string.
- `marcacoes`: ordered list of visible time markings, default empty list.
- `ocorrencias`: ordered list of visible occurrence/justification texts, default empty list.
- `observacoes`: ordered list of visible observation texts, default empty list.
- `situacao`: visible status/situation text when present, optional string.
- `textos_visiveis`: ordered list of remaining visible texts for the day, default empty list.

Validation rules:

- At least one of `data`, `marcacoes`, `ocorrencias`, `observacoes`, `situacao`, or `textos_visiveis` must come from visible page content.
- Missing optional page fields are represented as `null` or empty arrays; they are not invented.
- `marcacoes` are preserved in visible order and are not used to calculate official balances.

## EspelhoPontoExport

The reusable report JSON containing visible Espelho de Ponto data.

Fields:

- `schema_version`: contract version, required, currently `1`.
- `run_id`: unique execution identifier, required string.
- `captured_at`: ISO-8601 timestamp with timezone, required string.
- `status`: export data status, required enum `completed` or `empty`.
- `servidor`: `ServidorSelecionado`, required.
- `periodo_referencia`: visible reference period, optional string.
- `mensagens`: visible page messages/alerts, default empty list.
- `registros`: list of `RegistroDiaPonto`, default empty list.
- `fonte`: metadata about the source page without sensitive artifacts, required object.

Validation rules:

- `registros` may be empty only when `status` is `empty` or the visible page explicitly has no daily records.
- `fonte` may include page title, final URL path, and visible screen labels, but must not include raw HTML, cookies, credentials, screenshots, traces, or tokens.
- The file must be valid UTF-8 JSON.

## ExportacaoEspelhoResult

The operational result JSON for one export attempt.

Fields:

- `schema_version`: contract version, required, currently `1`.
- `run_id`: unique execution identifier, required string.
- `started_at`: ISO-8601 timestamp with timezone, required string.
- `completed_at`: ISO-8601 timestamp with timezone, required string.
- `success`: boolean, required.
- `status`: required enum `completed`, `empty`, `failed`, or `blocked`.
- `final_step`: last completed or failed step, required string.
- `requested_server`: server name supplied to the CLI, optional string.
- `selected_server`: `ServidorSelecionado` when identified, optional object.
- `periodo_referencia`: visible reference period when identified, optional string.
- `export_path`: path to the report JSON when written, optional string.
- `message`: human-readable result message, required string.
- `error_code`: stable failure code when applicable, optional string.

Validation rules:

- `success=true` requires `status` of `completed` or `empty` and a non-empty `export_path`.
- `success=false` must not claim an `export_path` unless a partial file was explicitly retained for diagnostics, which is out of scope for this feature.
- Write failure produces `success=false`, `status=failed`, and no successful report file declaration.

## AuthenticatedUserSession

Existing authenticated browser session used to reach and export the espelho.

Fields:

- `username_ref`: non-sensitive user/session reference, optional string.
- `authenticated`: boolean state from existing login flow.
- `session_state`: existing login/navigation state.

Validation rules:

- Session expiry during export stops the flow and does not trigger automatic reauthentication.
- CAPTCHA, MFA, or anti-automation states transition to `blocked`.

## State Transitions

```text
Authenticated session
  -> Espelho page navigated
  -> Server selected
  -> Espelho page validated for selected server
  -> Visible data parsed
  -> Report JSON written
  -> Operational result written
```

Failure transitions:

- `Server selected -> invalid_page`: no report JSON; result `failed`.
- `Server selected -> wrong_server`: no report JSON; result `failed`.
- `Server selected -> session_expired`: no report JSON; result `failed`.
- `Server selected -> anti_automation`: no report JSON; result `blocked`.
- `Visible data parsed -> write_failed`: no success declaration; result `failed`.
