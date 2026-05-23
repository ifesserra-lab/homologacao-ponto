# Implementation Plan: Exportar Tabela Completa do Espelho de Ponto por Servidor

**Branch**: `005-exportar-espelho-json` | **Date**: 2026-05-23 | **Spec**: [spec.md](spec.md)

## Summary

Extend the espelho de ponto JSON export to capture all visible table columns (HR, HC, HE, HA, HH, Crédito, Débito, Saldo No Mês, Crédito Acumulado, DNC) from the SIGRH page, and reorganize output files into per-server subdirectories (`data/servidores/{servidor-slug}/espelho-{periodo}.json`) while preserving the existing JSON schema fields.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: `html.parser` (stdlib), `pathlib` (stdlib), `unicodedata` (stdlib for slug normalization)
**Storage**: Local filesystem — `data/servidores/{servidor-slug}/espelho-{periodo}.json`
**Testing**: pytest, TDD red/green/refactor
**Target Platform**: macOS/Linux CLI
**Project Type**: CLI tool
**Performance Goals**: File write < 1s after HTML capture
**Constraints**: Zero schema field removals; backward-compatible model changes only
**Scale/Scope**: Single-user CLI; one server/month per invocation

## Constitution Check

### Test-First Delivery ✓
Each task below lists a failing test before the corresponding production change. Parser column extraction, slug generation, per-server path routing, and backward compatibility all have independent failing tests first.

### Python Runtime ✓
All changes are pure Python 3.12+, stdlib only (no new dependencies).

### Object-Oriented Domain Design ✓
- `RegistroDiaPonto` — domain model; new optional column fields added
- `EspelhoPontoExport` — aggregate root; `output_subdir` property added
- `EspelhoPontoParser._sigrh_extract_row()` — parser; extended column mapping
- `ResultWriter` — infrastructure; path routing updated

### Design Patterns ✓
- **Value Object** (`RegistroDiaPonto`, `EspelhoPontoExport`): frozen dataclasses, already in use
- No new patterns introduced; existing patterns extended

### Quality Gates ✓
- `pytest -q` — all 143 existing tests continue to pass
- `ruff check src tests` — linting clean
- Independent story validation: each user story testable in isolation with fake HTML fixtures

## Project Structure

### Documentation (this feature)

```text
specs/005-exportar-espelho-json/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── contracts/
│   └── registro_dia_ponto.json   ← JSON schema for updated record
└── tasks.md             ← Phase 2 output (/speckit-tasks)
```

### Source Code Changes

```text
src/homologacao_ponto/
├── models/
│   └── espelho_ponto_export.py   ← RegistroDiaPonto + EspelhoPontoExport changes
├── infrastructure/
│   └── espelho_ponto_parser.py   ← _sigrh_extract_row extended column mapping
└── services/
    └── result_writer.py          ← output_subdir routing

tests/
├── unit/
│   ├── test_espelho_ponto_parser_columns.py   ← NEW: column extraction tests
│   └── test_result_writer_servidor_path.py   ← NEW: per-server path tests
├── contract/
│   └── test_espelho_ponto_export_schema.py   ← updated: new fields in schema
└── fixtures/
    └── sigrh_espelho_export_pages.py         ← updated: richer HTML fixtures
```

## Phase 0: Research

*Resolved from codebase inspection and saved SIGRH HTML analysis.*

### R-001: SIGRH table cell order

**Decision**: Cells in each `frequenciaForm:listagemPontos:N:*` row follow this positional order:
```
[0] Data cell (contains date DD/MM/YYYY, "Dia da Semana: X", "Observação: ...")
[1] Horários Registrados (time punches, e.g. "07:00 12:00 13:00 18:00" or "---")
[2] HR  — Horas Regulares
[3] HC  — Horas Complementares
[4] HE  — Horas Extras
[5] HA  — Horas de Abono
[6] HH  — Horas de Homologação
[7] Crédito
[8] Débito
[9] Saldo No Mês
[10] Crédito Acumulado
[11] DNC — Dias Não Computados
```
**Rationale**: Confirmed by inspection of `data/debug_espelho_live.html` (saved during previous session debugging) and cross-referenced against screenshot showing column headers in that exact order.

**Validation task**: Unit test with real-structure HTML fixture verifying each field lands in the correct slot. If column count differs in future SIGRH versions, missing cells map to `None` rather than raising an exception.

**Alternatives considered**: Header-based detection (find `<th>` text, map position dynamically). Rejected because SIGRH renders headers in a separate `<tr>` not inside the data rows; positional mapping is simpler and consistent with the existing parser approach.

### R-002: Servidor slug normalization for folder name

**Decision**: Normalize via `unicodedata.normalize("NFD") → strip combining chars → lower() → replace spaces/special with "-" → collapse repeated hyphens`.

Example: `"CELIO PROLICIANO MAIOLI"` → `"celio-proliciano-maioli"`.

**Rationale**: macOS/Linux allow most Unicode in paths but a normalized ASCII slug is portable, readable, and collision-resistant for names that differ only in accents. stdlib `unicodedata` requires no dependency.

**Alternatives considered**: `unidecode` library — rejected (extra dependency for trivial normalization). Raw lower() only — rejected (leaves accents, fails on Windows FAT paths).

### R-003: Storage path routing in ResultWriter

**Decision**: Add `output_subdir: str | None` property to `EspelhoPontoExport` returning `servidores/{servidor-slug}`. Update `ResultWriter.write()` to resolve `output_dir / result.output_subdir / result.output_filename` when `output_subdir` is non-None, else keep existing `output_dir / result.output_filename` behavior.

**Rationale**: Keeps `ResultWriter` as the single write gateway for all result types. No new classes. Other result types (`ExportacaoEspelhoResult`, `CrawlResult`) return `output_subdir = None` implicitly via the protocol — they are unaffected. `EspelhoPontoExport.output_filename` changes to `espelho-{periodo-slug}.json`; the `run_id`-based name moves to `ExportacaoEspelhoResult` only, where it already lives.

**Alternatives considered**: Separate `EspelhoWriter` class — rejected (duplicates `ResultWriter` logic). Encode full relative path in `output_filename` — rejected (breaks `with_output_path` contract and mixes concerns).

### R-004: Period slug for filename

**Decision**: Convert `periodo_referencia` (e.g. `"Dezembro/2025"`) to `espelho-dezembro-2025.json`.
Normalization: `periodo.lower().replace("/", "-")`. Fallback when `None`: `espelho-{run_id}.json` (preserves uniqueness).

**Rationale**: Human-readable filename; one file per period per server; deterministic so re-runs overwrite stale data.

---

*Output*: [research.md](research.md)

## Phase 1: Design

### Data Model

See [data-model.md](data-model.md).

**`RegistroDiaPonto`** — add 10 optional fields, all `str | None = None`:

| Field | Maps to column |
|-------|----------------|
| `hr` | HR |
| `hc` | HC |
| `he` | HE |
| `ha` | HA |
| `hh` | HH |
| `credito` | Crédito |
| `debito` | Débito |
| `saldo_no_mes` | Saldo No Mês |
| `credito_acumulado` | Crédito Acumulado |
| `dnc` | DNC |

All new fields are optional (`None` = not present in HTML). `to_dict()` always includes them (no omission). `__post_init__` unchanged — existing non-null check covers current fields only.

**`EspelhoPontoExport`** — add:
- `output_subdir` property → `f"servidores/{_slug(self.servidor.nome)}"`
- `output_filename` property → `f"espelho-{_periodo_slug(self.periodo_referencia, self.run_id)}.json"`

**`_slug(name: str) -> str`** — module-level helper in `espelho_ponto_export.py`.
**`_periodo_slug(periodo: str | None, run_id: str) -> str`** — module-level helper.

### Parser Contract

`_sigrh_extract_row()` maps `self._sigrh_cells` by fixed offset from `date_idx`:

```python
def _cell(cells, date_idx, offset):
    idx = date_idx + offset
    val = cells[idx].strip() if idx < len(cells) else None
    return val if val and val != "---" else None
```

Returns extended row dict with all 10 new fields.

### ResultWriter Contract

```python
def write(self, result):
    subdir = getattr(result, "output_subdir", None)
    output_path = (
        self.output_dir / subdir / result.output_filename
        if subdir
        else self.output_dir / result.output_filename
    )
    ...
```

`mkdir(parents=True, exist_ok=True)` already handles nested dirs.

### Interface Contracts

See [contracts/registro_dia_ponto.json](contracts/registro_dia_ponto.json).

### Agent Context Update

AGENTS.md `<!-- SPECKIT START -->` block updated to reference `specs/005-exportar-espelho-json/plan.md`.

## Constitution Check (Post-Design)

| Principle | Status |
|-----------|--------|
| Test-first | ✓ — test tasks precede all implementation tasks |
| Python 3.12+ | ✓ — stdlib only |
| OO design | ✓ — changes isolated to `RegistroDiaPonto`, `EspelhoPontoExport`, `_sigrh_extract_row`, `ResultWriter.write` |
| Intentional patterns | ✓ — Value Object pattern extended, no new patterns |
| Quality gates | ✓ — `pytest -q`, `ruff check src tests`, per-story fixture tests |

## Complexity Tracking

*No constitution violations.*
