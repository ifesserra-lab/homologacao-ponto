# Research: Dashboard de Espelhos de Ponto

**Feature**: 008-dashboard-espelho-ponto | **Phase**: 0

## Technology Decision

**Selected**: Astro.build 4.x — directed by user.

Astro is a web framework that runs fully at build/dev time on Node.js. It reads
files from disk using `fs` (Node built-in) and generates pages at build time or
serves them via its dev server.

| FR | How Astro satisfies it |
|----|------------------------|
| FR-009 (no external server) | `astro dev` binds to localhost; no cloud, no daemon |
| FR-001 (reads JSONs from `data/runs/servidores/`) | `fs.readdirSync` + `JSON.parse` in `espelhoRepository.ts` |
| FR-007 (corrupted JSON skip) | try/catch in `_loadEspelho`, skip + `console.warn` |
| FR-008 (most recent file per period) | sort by `captured_at` desc, keep first per `periodo_referencia` |
| FR-006 (null → `—`) | `formatMin(null) === "—"` in `aggregation.ts` |

## Data Path

```
data/runs/servidores/<slug>/espelho-<periodo>.json
```

Astro project is at `dashboard/`. Relative path from there to data:
`../data/runs/servidores/`. Repository accepts a configurable base path
(default: `path.resolve(__dirname, '../../data/runs/servidores')`).

## Aggregation Logic (TypeScript)

```typescript
export function parseHHMM(s: string | null | undefined): number | null {
  if (!s) return null;
  const [h, m] = s.split(":");
  const hours = parseInt(h, 10);
  const mins = parseInt(m, 10);
  if (isNaN(hours) || isNaN(mins)) return null;
  return hours * 60 + mins;
}

export function formatMin(minutes: number | null): string {
  if (minutes === null) return "—";
  const h = Math.floor(minutes / 60).toString().padStart(2, "0");
  const m = (minutes % 60).toString().padStart(2, "0");
  return `${h}:${m}`;
}
```

Aggregation per `EspelhoMesResume`:
- `daysWithMarcacoes`: `registros.filter(r => r.marcacoes?.length > 0).length`
- `somaCreditoMin`: `sum of parseHHMM(r.credito) for non-null results`
- `somaDebitoMin`: same for `debito`
- `somaHhMin`: same for `hh`
- `dncFinalMin`: `parseHHMM(registros.at(-1)?.dnc ?? null)`

## HTTP Routes (Astro pages)

| Route | File | Renders |
|-------|------|---------|
| `GET /` | `src/pages/index.astro` | US1: server list |
| `GET /servidor/[slug]` | `src/pages/servidor/[slug].astro` | US2: monthly detail |

Astro generates static HTML for all server slugs at build time via `getStaticPaths`.

## Python CLI Integration

Add `dashboard` subcommand to `cli.py`:

```
homologacao-ponto dashboard [--data-dir ./data/runs] [--port 4321]
```

Implementation: `subprocess.run(["npm", "run", "dev", "--", "--port", port], cwd=dashboard_dir)`.

## Testing Strategy

| Layer | Tool | What to test |
|-------|------|-------------|
| `aggregation.ts` | Vitest | `parseHHMM`, `formatMin`, `aggregateMonth` — pure functions |
| `espelhoRepository.ts` | Vitest | list servers, monthly summaries, deduplication, corrupted-JSON skip |
| Python CLI `dashboard` | pytest | subcommand exists, delegates correctly |
