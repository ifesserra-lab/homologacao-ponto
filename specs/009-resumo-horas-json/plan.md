# Implementation Plan: Resumo das Horas Apuradas no JSON do Mês

**Branch**: `009-resumo-horas-json` | **Date**: 2026-05-23 | **Spec**: [spec.md](spec.md)

## Summary

Adicionar captura dos 16 campos da seção "Resumo das Horas Apuradas no Mês" do SIGRH ao JSON exportado por mês. O scraper Python parseia a seção de resumo via text-label matching, persiste no campo `resumo` (schema_version 2). O dashboard TypeScript usa os valores diretamente quando disponíveis, com fallback para cálculo aproximado.

## Technical Context

**Language/Version**: Python 3.12+ (scraper) + TypeScript/Astro 4.x (dashboard)  
**Primary Dependencies**: `html.parser` stdlib (já usado); sem novas dependências Python  
**Storage**: JSON files em `data/runs/servidores/<slug>/espelho-<periodo>.json`  
**Testing**: pytest TDD (Python) + Vitest TDD (TypeScript)  
**Target Platform**: macOS/Linux local  
**Project Type**: CLI + static dashboard  
**Performance Goals**: parsing do resumo < 10ms por espelho  
**Constraints**: retro-compatibilidade com JSON v1 sem `resumo`  
**Scale/Scope**: ~5–20 servidores × ~24 meses por servidor

## Constitution Check

### Test-First Delivery ✅
- Cada user story tem testes falhando escritos antes da implementação.
- US1: `test_parser_captura_resumo_do_html` → falha → implementa `_ResumoHTMLParser` → verde.
- US2: `test_dashboard_usa_resumo_quando_disponivel` → falha → atualiza `aggregation.ts` → verde.

### Python Runtime ✅
- Todo código novo é Python 3.12+ (modelos + parser) ou TypeScript no dashboard existente.
- Nenhuma nova dependência fora da stdlib.

### Object-Oriented Domain Design ✅
- `ResumoHorasApuradas`: dataclass frozen representando o domínio "resumo mensal".
- `_ResumoHTMLParser`: classe de infraestrutura que encapsula o parsing HTML.
- `EspelhoPontoParser`: orquestra `_EspelhoHTMLParser` (existente) + `_ResumoHTMLParser` (novo).

### Intentional Design Patterns ✅
- **Adapter**: `_ResumoHTMLParser` adapta HTML → `ResumoHorasApuradas`, isolando parsing.
- **Null Object**: `resumo: None` mantém retro-compatibilidade sem condicionar toda a lógica.

### Quality Gates ✅
```bash
python -m pytest tests/ -x -q          # Python unit + integration
cd dashboard && npm test                 # Vitest (27+ testes)
ruff check src/ && ruff format --check src/
```

## Project Structure

### Documentation (this feature)

```text
specs/009-resumo-horas-json/
├── plan.md              ← este arquivo
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── json-schema-v2.md
└── tasks.md             (gerado por /speckit-tasks)
```

### Source Code

```text
src/homologacao_ponto/
├── models/
│   ├── __init__.py                  # exportar ResumoHorasApuradas
│   └── espelho_ponto_export.py      # + ResumoHorasApuradas, atualizar EspelhoPontoExport
├── infrastructure/
│   └── espelho_ponto_parser.py      # + _ResumoHTMLParser, integrar no EspelhoPontoParser

tests/
├── fixtures/
│   └── sigrh_espelho_export_pages.py  # + VALID_ESPELHO_WITH_RESUMO_HTML
└── unit/
    ├── test_resumo_horas_apuradas.py   # NOVO — testes do modelo
    └── test_espelho_ponto_parser.py    # + testes de captura do resumo

dashboard/src/
├── types/dashboard.ts               # + ResumoHorasApuradas, campo resumo em RawEspelho
├── lib/aggregation.ts               # usar resumo quando disponível
└── pages/servidor/[slug]/[periodo].astro  # usar agg.resumo nos stats
```

## Fases de Implementação

### Fase A — Modelo Python (US1, parte 1)

**A1** — Teste falhando: `ResumoHorasApuradas.to_dict()` retorna 16 campos  
**A2** — Implementar `ResumoHorasApuradas` em `espelho_ponto_export.py`  
**A3** — Exportar de `models/__init__.py`  
**A4** — Teste falhando: `EspelhoPontoExport.to_dict()` contém `resumo` e `schema_version=2`  
**A5** — Atualizar `EspelhoPontoExport`: campo `resumo`, `to_dict()`, `with_output_path()`

### Fase B — Parser HTML (US1, parte 2)

**B1** — Adicionar `VALID_ESPELHO_WITH_RESUMO_HTML` ao fixture com seção resumo simulada  
**B2** — Teste falhando: `EspelhoPontoParser.parse()` retorna `export.resumo` com valores corretos  
**B3** — Implementar `_ResumoHTMLParser`:
  - Estado: `_in_resumo_section`, `_resumo_cells`, buffer de pares label→valor
  - Matching: normalizar texto → mapear para campo via `_RESUMO_LABEL_MAP`
  - `build_resumo()` → `ResumoHorasApuradas | None`
**B4** — Integrar em `EspelhoPontoParser.parse()`: instanciar `_ResumoHTMLParser`, passar HTML, atribuir resultado  
**B5** — Teste negativo: HTML sem seção resumo → `export.resumo is None`  
**B6** — Teste: valores negativos (`"-09:10"`) preservados com sinal

### Fase C — Dashboard TypeScript (US2)

**C1** — Atualizar `dashboard/src/types/dashboard.ts`: interface `ResumoHorasApuradas`, campo `resumo?: ResumoHorasApuradas | null` em `RawEspelho`  
**C2** — Teste Vitest falhando: quando `espelho.resumo` não nulo, `aggregateMonth` usa seus valores  
**C3** — Atualizar `aggregation.ts`:
  - Aceitar `resumo` opcional em `aggregateMonth` ou ler de `espelho` na página
  - `somaHrMin` ← `parseSignedHHMM(resumo.total_horas_registradas)` quando disponível
  - `somaCreditoMin` ← `parseSignedHHMM(resumo.total_horas_homologadas)` quando disponível
  - `cargaEsperadaMin` ← `parseSignedHHMM(resumo.carga_horaria_esperada_mes)` quando disponível
  - `balanceMin` ← `parseSignedHHMM(resumo.saldo_horas_mes)` quando disponível
**C4** — Atualizar `[periodo].astro`: passar `espelho.resumo` para `aggregateMonth`  
**C5** — Teste retro-compat: JSON sem `resumo` → fallback sem erro

## Complexity Tracking

Nenhuma violação da Constitution. Sem exceções necessárias.
