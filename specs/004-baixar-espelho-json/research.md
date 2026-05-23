# Research: Baixar Espelho de Ponto em JSON

## Decision: Write the espelho data to a dedicated JSON report file and keep the operational result separate

**Rationale**: The espelho report is reusable domain data, while the operational result is execution metadata. Keeping them separate avoids bloating selection/navigation result files, makes downstream processing easier, and lets failures record diagnostics even when no report file exists.

**Alternatives considered**:

- Embed the full export inside the selection result: rejected because it mixes operational status with report data and makes prior result contracts harder to evolve.
- Write only the report JSON: rejected because failure cases still need a durable status, message, final step, and diagnostic context.

## Decision: Extract visible data through a parser that returns structured fields plus preserved visible text

**Rationale**: The spec requires common per-day fields such as `data`, `marcacoes`, `ocorrencias`, `observacoes`, and `textos_visiveis`, but the SIGRH layout can vary. A parser can normalize well-known fields while retaining visible text that does not fit cleanly, without inventing official calculations.

**Alternatives considered**:

- Store raw HTML for later parsing: rejected because the feature explicitly forbids raw HTML persistence by default.
- Parse only free text: rejected because users need predictable JSON fields for reuse.
- Calculate official balances from markings: rejected as out of scope and risky because the page is the source of truth.

## Decision: Export the currently visible selected-server period only

**Rationale**: The preceding features already authenticate, navigate, search, and select a server. This feature starts after that selection and should not add date navigation, period selection, PDF download, or batch export complexity.

**Alternatives considered**:

- Add period controls to the CLI: rejected because the current requirement only asks to download the visible Espelho de Ponto after selection.
- Download PDF or spreadsheet artifacts: rejected because the requested output is JSON from visible page data.

## Decision: Treat empty espelho as a successful export with an empty records list and explanatory message

**Rationale**: An empty period is valid user-observable data, not a parser failure. The generated JSON should still include server, captured timestamp, status, visible messages, and an empty `registros` array.

**Alternatives considered**:

- Fail when no records are found: rejected because it would confuse a valid "sem registros" page with a broken page.
- Invent placeholder day records: rejected because absent records must not be fabricated.

## Decision: Fail closed for wrong server, invalid page, expired session, anti-automation, and write failure

**Rationale**: Persisting records under the wrong server or after session/state uncertainty is more harmful than returning a clear failure. The result file records the stopped step and message; no report data file is declared successful unless it was written safely.

**Alternatives considered**:

- Attempt automatic re-login after expiry: rejected by the project security rule and existing assumptions.
- Continue with warning on server mismatch: rejected because it could produce misleading personnel records.

## Decision: Validate contracts with JSON Schema tests and route-backed Playwright integration tests

**Rationale**: The feature has a stable CLI/data contract plus browser-dependent page extraction. Schema tests protect downstream consumers; route-backed integration tests verify the end-to-end flow without depending on live SIGRH for every run.

**Alternatives considered**:

- Live-only verification: rejected because it is slow, brittle, and hard to run in CI/local loops.
- Unit tests only: rejected because selector/page-state failures are a key risk for this feature.
