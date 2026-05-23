# Contract: Astro Dashboard HTTP Routes

**Feature**: 008-dashboard-espelho-ponto

## Routes

### `GET /` — Server List (US1)

**File**: `dashboard/src/pages/index.astro`

**Renders**: HTML page listing all servers found in `DATA_DIR`.

**Required HTML elements** (used in tests):
- `<h1>` containing "Espelhos de Ponto"
- One element with `data-slug="<slug>"` per server
- Server name visible in each card
- `data-total-meses="<n>"` attribute on each card
- `data-status="completo|com-vazios"` attribute on each card
- Empty state: `data-empty-state="true"` when no servers found

**Empty state** (FR-007 / edge case):
- Shows message: "Nenhum espelho encontrado"
- Shows path hint: `data/runs/servidores/`

### `GET /servidor/[slug]` — Monthly Detail (US2)

**File**: `dashboard/src/pages/servidor/[slug].astro`

**Renders**: HTML page with monthly summary table for the given server.

**Required HTML elements**:
- `<h1>` containing the server's `nome`
- `<table>` or list with one row per `EspelhoMesResume`
- Each row has `data-periodo="<periodoReferencia>"` attribute
- Each row has `data-status="completed|empty"` attribute
- Metrics shown for `completed` rows: days, credito, debito, HH, DNC
- Empty months show "Sem registros" label (not numeric metrics)

**Navigation**:
- Back link to `/` (server list)

**404 behaviour**:
- Unknown slug → Astro returns 404

## Data Environment Variable

Astro reads the data directory from:

```
DATA_DIR=<absolute path to data/runs/servidores/>
```

Set by the Python CLI when invoking `npm run dev`.

Fallback (if not set): `path.resolve(process.cwd(), '../../data/runs/servidores')`.
This works when `npm run dev` is run directly from `dashboard/`.
