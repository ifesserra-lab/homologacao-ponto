# Implementation Plan: Dashboard de Espelhos de Ponto

**Branch**: `008-dashboard-espelho-ponto` | **Date**: 2026-05-23 | **Spec**: [spec.md](./spec.md)
**Input**: Dashboard para visualizar de forma resumida os espelhos de cada servidor

## Summary

Astro.build static site dashboard that reads JSON files from
`data/runs/servidores/` at build time and renders two pages: server list (US1)
and monthly-detail per server (US2). Served locally via `astro dev` (lightweight
embedded dev server — satisfies FR-009). Python CLI adds a `dashboard` command
that delegates to `npm run dev` in the `dashboard/` directory.

## Technical Context

**Language/Version**: Python 3.12+ (CLI entry); Node.js 18+ + Astro 4.x (dashboard)  
**Primary Dependencies**: `astro` (Astro framework), `@astrojs/check`, `typescript` — all in `dashboard/package.json`  
**Storage**: read-only JSON files at `data/runs/servidores/<slug>/espelho-*.json`  
**Testing**: pytest (Python layer); Vitest (Astro aggregation utilities); manual smoke test for rendered pages  
**Target Platform**: macOS / Linux (local use, `localhost`)  
**Project Type**: CLI + Astro static site (single repo, two layers)  
**Performance Goals**: page load < 3 s (SC-001)  
**Constraints**: no external server — `astro dev` binds to localhost only (FR-009)  
**Scale/Scope**: tens of servers, up to 12 months each

## Constitution Check

**Test-first delivery**  
- Aggregation utilities (`parseHHMM`, `formatMin`, `aggregateMonth`) are pure
  TypeScript functions with Vitest tests written before implementation.
- Python `dashboard` CLI handler tested with `subprocess` integration test
  (starts server, checks it binds, kills it).

**Python runtime exception**: Astro/TypeScript dashboard layer recorded below in
Complexity Tracking. Python layer (CLI, data pipeline, batch) unchanged.

**OO design (Python CLI layer)**:
- No new Python classes needed — `dashboard` subcommand delegates via
  `subprocess` to `npm run dev`.

**OO design (Astro layer)**:
- `EspelhoRepository` (TypeScript module): reads and deduplicates JSON files
- `ServidorResume`, `EspelhoMesResume` (TypeScript types): domain aggregates
- Astro pages (`index.astro`, `servidor/[slug].astro`): render domain objects

**Design patterns**:
- Repository (`espelhoRepository.ts`): isolates `fs.readFileSync` calls so
  tests can inject fixture data

**Quality gates**:
```bash
cd dashboard && npm run test          # Vitest unit tests
cd dashboard && npm run build         # Astro build (catches TS errors)
cd dashboard && npm run dev           # manual smoke test
pytest tests/ -x                      # Python tests (CLI layer)
```

## Project Structure

### Documentation (this feature)

```text
specs/008-dashboard-espelho-ponto/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   ├── cli-dashboard.md   ← CLI contract (Python)
│   └── http-routes.md     ← Astro pages contract
└── tasks.md             ← Phase 2 output (speckit-tasks)
```

### Source Code

```text
dashboard/                             ← Astro project root
├── package.json
├── astro.config.mjs
├── tsconfig.json
├── src/
│   ├── pages/
│   │   ├── index.astro                ← US1: server list
│   │   └── servidor/
│   │       └── [slug].astro           ← US2: monthly detail
│   ├── lib/
│   │   ├── espelhoRepository.ts       ← reads JSON from data/runs/servidores/
│   │   └── aggregation.ts             ← parseHHMM, formatMin, aggregateMonth
│   ├── types/
│   │   └── dashboard.ts               ← ServidorResume, EspelhoMesResume
│   └── components/
│       ├── ServerCard.astro           ← US1 server list item
│       └── MonthTable.astro           ← US2 monthly rows
└── src/tests/
    ├── aggregation.test.ts
    └── espelhoRepository.test.ts

src/homologacao_ponto/
└── cli.py                             ← add `dashboard` subcommand (modify)

tests/
└── integration/
    └── test_dashboard_cli.py          ← Python: CLI starts server, returns 0
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Non-Python component (Astro/TypeScript/Node) | User directed use of Astro.build for dashboard | Python stdlib http.server with inline HTML generates acceptable but less maintainable UI; Astro provides component model, TypeScript safety, and fast iteration for HTML/CSS without a backend framework |
