# Tasks: Dashboard de Espelhos de Ponto

**Input**: Design documents from `/specs/008-dashboard-espelho-ponto/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: MANDATORY. Failing test tasks precede implementation for every story and
for aggregation, repository, and error-handling behavior (Constitution I).

**Tech stack**: Astro 4.x + TypeScript + Vitest (`dashboard/`); Python CLI (`src/homologacao_ponto/cli.py`)

---

## Phase 1: Setup

**Purpose**: Initialize Astro project and Vitest test runner.

- [x] T001 Create Astro 4.x project at `dashboard/` with `npm create astro@latest -- --template minimal --no-install --typescript strict`
- [x] T002 Add Vitest to `dashboard/package.json` devDependencies; create `dashboard/vitest.config.ts` with test glob `src/tests/**/*.test.ts`
- [x] T003 [P] Create TypeScript types in `dashboard/src/types/dashboard.ts` — `EspelhoMesResume`, `ServidorResume` interfaces per data-model.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Aggregation utilities and repository that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Tests (write first — MUST FAIL before implementation)

- [x] T004 [P] Write failing unit tests for `aggregation.ts` in `dashboard/src/tests/aggregation.test.ts`:
  - `parseHHMM(null) === null`
  - `parseHHMM("08:30") === 510`
  - `parseHHMM("invalid") === null`
  - `formatMin(null) === "—"`
  - `formatMin(510) === "08:30"`
  - `aggregateMonth([])` returns zeros and null for `dncFinalMin`
  - `aggregateMonth(registros)` sums `credito`, `debito`, `hh`, counts `daysWithMarcacoes`, reads last `dnc`

- [x] T005 [P] Write failing unit tests for `EspelhoRepository` in `dashboard/src/tests/espelhoRepository.test.ts`:
  - `listServers(emptyDir)` returns `[]`
  - `listServers(dir)` returns one `ServidorResume` per server subfolder
  - `serverDetail(slug, dir)` returns correct `ServidorResume` with sorted months
  - `serverDetail("not-found", dir)` returns `undefined`
  - Deduplication: two files for same `periodo_referencia` — keeps higher `captured_at`
  - Corrupted JSON file — skipped silently, other servers still returned

- [x] T008 [P] Write failing integration test for CLI `dashboard` subcommand in `tests/integration/test_dashboard_cli.py`:
  - `homologacao-ponto dashboard --help` exits 0 and includes `--data-dir` and `--port`
  - `homologacao-ponto dashboard --data-dir /nonexistent` exits 1 with error message

### Implementation

- [x] T006 Implement `dashboard/src/lib/aggregation.ts` — `parseHHMM`, `formatMin`, `aggregateMonth` (after T004 tests fail)
- [x] T007 Implement `dashboard/src/lib/espelhoRepository.ts` — `listServers`, `serverDetail`, `_loadEspelho` (try/catch), `_deduplicate` (after T005 tests fail; depends on T006)
- [x] T009 Add `dashboard` subcommand to `src/homologacao_ponto/cli.py` — args: `--data-dir ./data/runs`, `--port 4321`; delegates to `npm run dev` in `dashboard/` directory (after T008 tests fail)

**Checkpoint**: `npm test` passes all aggregation and repository tests; `pytest tests/integration/test_dashboard_cli.py` passes.

---

## Phase 3: User Story 1 — Visão consolidada por servidor (Priority: P1) 🎯 MVP

**Goal**: User opens dashboard and sees all servers with month count, period range, and status indicator.

**Independent Test**: With JSONs in `data/runs/servidores/celio-proliciano-maioli/`, open `http://localhost:4321` and verify: card for "CELIO PROLICIANO MAIOLI", shows 5 months, shows period range, shows status. With empty `data/runs/servidores/`, shows "Nenhum espelho encontrado".

### Tests (write first — MUST FAIL before implementation)

- [x] T010 [P] [US1] Write failing Vitest test for `index.astro` rendering in `dashboard/src/tests/index.test.ts`:
  - Rendered HTML contains `data-slug="celio-proliciano-maioli"`
  - Contains `data-total-meses="5"`
  - Contains `data-status="com-vazios"` when server has empty months
  - Contains `data-status="completo"` when all months completed
  - Contains `data-empty-state="true"` when `listServers()` returns `[]`

### Implementation

- [x] T011 [P] [US1] Create `ServerCard.astro` component in `dashboard/src/components/ServerCard.astro` — props: `servidor: ServidorResume`; renders `data-slug`, `data-total-meses`, `data-status`, `periodoRange`, `nome`, link to `/servidor/<slug>`
- [x] T012 [US1] Create `dashboard/src/pages/index.astro` — calls `listServers(DATA_DIR)`, renders `<ServerCard>` per server, shows empty state with `data-empty-state="true"` when list is empty (depends on T011, T007)

**Checkpoint**: `npm run build` succeeds; `npm run dev` shows server list at `http://localhost:4321`.

---

## Phase 4: User Story 2 — Detalhamento mensal de um servidor (Priority: P1)

**Goal**: User selects a server and sees monthly summaries: period, status, days worked, HH sum, credit sum, debit sum, final DNC.

**Independent Test**: Navigate to `/servidor/celio-proliciano-maioli`; verify 5 rows, one per month; `espelho-fevereiro-2026.json` row shows "Sem registros"; `espelho-março-2026.json` row shows numeric metrics matching JSON.

### Tests (write first — MUST FAIL before implementation)

- [x] T013 [P] [US2] Write failing Vitest test for `[slug].astro` rendering in `dashboard/src/tests/servidor.test.ts`:
  - Rendered HTML contains `data-periodo="Março/2026"`
  - `data-status="completed"` row shows days, credito, debito, hh, dnc (not "Sem registros")
  - `data-status="empty"` row shows "Sem registros" label, no numeric metrics
  - `null` fields render as `"—"` not `"null"` (FR-006)
  - Page contains `<h1>` with server `nome`
  - Page contains back link to `/`

### Implementation

- [x] T014 [P] [US2] Create `MonthTable.astro` component in `dashboard/src/components/MonthTable.astro` — props: `meses: EspelhoMesResume[]`; renders table with `data-periodo`, `data-status`; uses `formatMin` for null→`"—"`
- [x] T015 [US2] Create `dashboard/src/pages/servidor/[slug].astro` — `getStaticPaths` from `listServers(DATA_DIR)`, renders `<MonthTable>`, back link to `/`, 404 for unknown slug (depends on T014, T007)

**Checkpoint**: `npm run build` succeeds; `/servidor/celio-proliciano-maioli` shows 5 monthly rows with correct metrics.

---

## Phase 5: User Story 3 — Detalhamento diário de um mês (Priority: P2)

**Goal**: User selects a month and sees complete daily records table with all fields.

**Independent Test**: Navigate to `/servidor/celio-proliciano-maioli/marco-2026`; verify 31 rows matching `espelho-março-2026.json` registros exactly; `null` fields show as `"—"`.

### Tests (write first — MUST FAIL before implementation)

- [x] T016 [P] [US3] Write failing Vitest test for daily detail page in `dashboard/src/tests/dia.test.ts`:
  - Rendered HTML has exactly N rows matching `registros.length`
  - Row for 2026-03-10 shows `marcacoes` formatted as "07:58 12:00 13:00 17:03"
  - `dnc: "00:00"` renders as `"00:00"` not empty (US3 acceptance scenario 3)
  - `ha: null` renders as `"—"` not "null" (US3 acceptance scenario 4)

### Implementation

- [x] T017 [P] [US3] Extend `EspelhoRepository` with `monthDetail(slug, periodo, dataDir)` returning raw `registros` array in `dashboard/src/lib/espelhoRepository.ts`
- [x] T018 [P] [US3] Create `DayTable.astro` component in `dashboard/src/components/DayTable.astro` — renders `registros` as table; all 14 fields from schema; `null`→`"—"` via `formatMin`
- [x] T019 [US3] Create `dashboard/src/pages/servidor/[slug]/[periodo].astro` — `getStaticPaths` from all server+month combinations; renders `<DayTable>`; back link to `/servidor/<slug>` (depends on T017, T018)
- [x] T020 [US3] Add link from each month row in `MonthTable.astro` to `/servidor/<slug>/<periodo>` (depends on T019)

**Checkpoint**: `/servidor/celio-proliciano-maioli/marco-2026` shows 31 daily rows; all fields visible.

---

## Phase 6: User Story 4 — Filtros e busca (Priority: P3)

**Goal**: User can filter server list by name (case-insensitive text search).

**Independent Test**: With 3 servers, type "celio" in filter input; list reduces to matching server only.

### Tests (write first — MUST FAIL before implementation)

- [ ] T021 [P] [US4] Write failing Vitest test for filter behavior in `dashboard/src/tests/filter.test.ts`:
  - Input "celio" hides non-matching servers (case-insensitive)
  - Input "" (cleared) shows all servers
  - Input "zzz" shows no servers and no empty-state message (different from zero-data empty state)

### Implementation

- [ ] T022 [US4] Add client-side filter `<script>` to `dashboard/src/pages/index.astro` — listens to `#filter-input` keyup; toggles `hidden` on `[data-slug]` cards where `nome` does not include input value (case-insensitive) (depends on T021)
- [ ] T023 [US4] Add `<input id="filter-input">` element to `index.astro` above server list

**Checkpoint**: Filter input on `/` reduces visible cards in real time.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T024 Run `cd dashboard && npm run build` — verify TypeScript compiles with zero errors
- [ ] T025 Run `.venv/bin/pytest tests/ -x` — verify all Python tests pass (255+)
- [ ] T026 [P] Add `dashboard/` and `node_modules` to `.gitignore` if not already present
- [ ] T027 [P] Update `docs/architecture/backlog.md` — mark feature 008 status as `Implemented`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 (T007 listServers, T006 aggregation)
- **US2 (Phase 4)**: Depends on Phase 2 (T007 serverDetail); builds on US1 components
- **US3 (Phase 5)**: Depends on Phase 4 (navigates from month rows in US2)
- **US4 (Phase 6)**: Depends on Phase 3 (adds filter to US1 page)
- **Polish (Phase 7)**: Depends on all desired stories complete

### User Story Dependencies

| Story | Depends on | Note |
|-------|-----------|------|
| US1 | Phase 2 | No story dependencies |
| US2 | Phase 2 + US1 (shared components) | Back link needs US1 page |
| US3 | US2 (navigates from month rows) | Adds link to MonthTable |
| US4 | US1 (modifies index.astro) | Client-side only |

### Parallel Opportunities

- T004 + T005 + T008: parallel (different files, no deps)
- T010 + T011 parallel (different files within US1)
- T013 + T014 parallel (different files within US2)
- T016 + T017 + T018 parallel (different files within US3)
- T021 + T022 parallel within US4

---

## Parallel Example: Phase 2 Foundational

```bash
# Start in parallel — all different files, no deps:
Task T004: Write aggregation.test.ts
Task T005: Write espelhoRepository.test.ts
Task T008: Write test_dashboard_cli.py

# After T004 passes (fails at this point — TDD):
Task T006: Implement aggregation.ts

# After T005 + T006:
Task T007: Implement espelhoRepository.ts

# After T008:
Task T009: Add dashboard subcommand to cli.py
```

---

## Implementation Strategy

### MVP (US1 + US2 only — confirmed scope)

1. Phase 1: Setup
2. Phase 2: Foundational → `npm test` green on aggregation + repository
3. Phase 3: US1 → `http://localhost:4321` shows server list
4. Phase 4: US2 → `/servidor/<slug>` shows monthly summaries
5. **STOP and VALIDATE**: Manual smoke test with real data in `data/runs/servidores/`

### Full Delivery (all stories)

1. MVP above
2. Phase 5: US3 (daily detail)
3. Phase 6: US4 (filters)
4. Phase 7: Polish

### Notes

- TDD: verify each test FAILS before writing implementation
- `DATA_DIR` env var: Astro reads from `import.meta.env.DATA_DIR` or process.cwd fallback (research.md)
- Astro `getStaticPaths` generates all server/month pages at build time; `npm run dev` serves them dynamically
- `formatMin(null) === "—"` is the single control point for FR-006 null display
