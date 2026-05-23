# Data Model: Dashboard de Espelhos de Ponto

**Feature**: 008-dashboard-espelho-ponto | **Phase**: 1

## TypeScript Types (`src/types/dashboard.ts`)

```typescript
export interface EspelhoMesResume {
  periodoReferencia: string | null;   // "Março/2026" — raw from JSON
  status: "completed" | "empty";
  capturedAt: string;                  // ISO 8601 — used for deduplication sort
  daysWithMarcacoes: number;           // count of days where marcacoes.length > 0
  somaCreditoMin: number;              // total credito in minutes (0 if none)
  somaDebitoMin: number;               // total debito in minutes
  somaHhMin: number;                   // total HH homologadas in minutes
  dncFinalMin: number | null;          // dnc of last record, null if empty espelho
}

export interface ServidorResume {
  slug: string;                        // "celio-proliciano-maioli"
  nome: string;                        // "CELIO PROLICIANO MAIOLI"
  siape: string | null;                // "1534589" or null
  meses: EspelhoMesResume[];           // sorted ascending by periodoReferencia
  totalMeses: number;                  // meses.length
  periodoRange: string;                // "Março/2026" | "Janeiro/2026 – Maio/2026"
  statusIndicator: "completo" | "com-vazios";
}
```

## Mapping: JSON → TypeScript

| JSON field | TypeScript field | Notes |
|-----------|-----------------|-------|
| `periodo_referencia` | `periodoReferencia` | raw string |
| `status` | `status` | `"completed"` \| `"empty"` |
| `captured_at` | `capturedAt` | ISO 8601 string |
| `registros[*].marcacoes` | `daysWithMarcacoes` | count non-empty arrays |
| `registros[*].credito` | `somaCreditoMin` | sum `parseHHMM`, skip nulls |
| `registros[*].debito` | `somaDebitoMin` | same |
| `registros[*].hh` | `somaHhMin` | same |
| `registros.at(-1).dnc` | `dncFinalMin` | last record's DNC |
| `servidor.nome` | `nome` | |
| `servidor.identificador` | `siape` | |

## Null Handling (FR-006)

| Scenario | Behaviour |
|----------|-----------|
| `credito: null` in JSON | `parseHHMM(null) === null` → not added to sum |
| Empty `registros` (status=empty) | sums are `0`, `dncFinalMin` is `null` |
| `dncFinalMin === null` in renderer | `formatMin(null) === "—"` |
| Field missing from JSON entirely | treated same as `null` via optional chaining |

## Repository Contract (`espelhoRepository.ts`)

```typescript
export function listServers(dataDir?: string): ServidorResume[]
export function serverDetail(slug: string, dataDir?: string): ServidorResume | undefined
```

Internal:
- `_loadEspelho(filePath: string): RawEspelho | null` — try/catch, returns null on error
- `_deduplicate(raws: RawEspelho[]): RawEspelho[]` — keep max `capturedAt` per `periodoReferencia`
- `_aggregate(raw: RawEspelho): EspelhoMesResume`
- `_buildServidorResume(slug: string, meses: EspelhoMesResume[], raw: RawEspelho): ServidorResume`

## Period Range Display

```typescript
function periodoRange(meses: EspelhoMesResume[]): string {
  const periods = meses
    .map(m => m.periodoReferencia)
    .filter((p): p is string => p !== null);
  if (periods.length === 0) return "—";
  if (periods.length === 1) return periods[0];
  return `${periods[0]} – ${periods[periods.length - 1]}`;
}
```

Assumes `meses` sorted ascending by `periodoReferencia` (repository responsibility).

## Status Indicator Derivation

```typescript
function statusIndicator(meses: EspelhoMesResume[]): "completo" | "com-vazios" {
  return meses.some(m => m.status === "empty") ? "com-vazios" : "completo";
}
```
