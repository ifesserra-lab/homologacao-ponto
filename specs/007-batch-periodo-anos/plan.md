# Implementation Plan: Período por Anos no Batch YAML

**Branch**: `007-batch-periodo-anos` | **Date**: 2026-05-23 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/007-batch-periodo-anos/spec.md`

## Summary

Adicionar campo `anos` ao `BatchConfig` para expandir o batch para múltiplos períodos. `anos: [2025, 2026]` processa todos os 12 meses de cada ano; `anos: All` detecta o histórico completo do servidor via probe regressivo no SIGRH. Sem `anos`, comportamento idêntico à feature 006. Modifica `BatchConfig`, `BatchEntryResult`, `BatchConfigLoader`, `BatchService` e cria `PeriodoExpander` e `AdmissaoDetector`.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: `pyyaml>=6.0` (já presente), `playwright>=1.44` (já presente)  
**Storage**: arquivos JSON por período em `data/runs/servidores/{slug}/espelho-{periodo}.json`  
**Testing**: pytest TDD red/green/refactor — `pytest tests/`  
**Target Platform**: macOS/Linux CLI  
**Project Type**: CLI tool  
**Performance Goals**: batch de 24 períodos (2 anos × 1 servidor) em menos de 5 minutos  
**Constraints**: SIGRH não tem endpoint multi-período; cada mês = 1 requisição sequencial  
**Scale/Scope**: N servidores × M períodos onde M pode chegar a ~300 meses (25 anos × 12)

## Constitution Check

### I. Test-First Delivery ✓
Cada fase tem testes que falham antes da implementação:
- `test_periodo_expander.py` (RED) → `periodo_expander.py` (GREEN)
- `test_admissao_detector.py` (RED) → `admissao_detector.py` (GREEN)
- `test_batch_config_007.py` (RED) → modificação `batch_config.py` (GREEN)
- `test_batch_service_007.py` (RED) → modificação `batch_service.py` (GREEN)

### II. Python 3.12+ ✓
Sem exceções — todo código em Python 3.12+.

### III. Object-Oriented Domain Design ✓
- `PeriodoExpander`: classe com método estático `expand()`, sem I/O
- `AdmissaoDetector`: classe com método `detect()`, recebe `app` por DI
- `BatchConfig` / `BatchEntryResult`: frozen dataclasses
- `BatchConfigLoader`: classe loader na fronteira de I/O

### IV. Intentional Design Patterns ✓
- **Strategy (implicit)**: `PeriodoExpander.expand()` escolhe estratégia baseada em `config.anos` (lista vs "All" vs None)
- **Adapter**: `AdmissaoDetector` adapta a interface de `_run_single_espelho` para detecção de período

### V. Quality Gates ✓
- `pytest tests/` — todos os testes passam
- `.venv/bin/ruff check src tests` — sem erros de lint
- `.venv/bin/ruff format --check src` — formatação correta
- US1 validável independentemente: `anos: [2025]` + 1 servidor → 12 entradas no relatório

## Project Structure

### Documentation (this feature)

```text
specs/007-batch-periodo-anos/
├── plan.md              # Este arquivo
├── research.md          # Decisões técnicas
├── data-model.md        # Entidades e relacionamentos
├── contracts/
│   ├── batch-config.schema.yaml   # Schema YAML de entrada (atualizado)
│   └── batch-result.schema.json   # Schema JSON de saída (atualizado)
└── tasks.md             # Gerado por /speckit-tasks
```

### Source Code (modificações e adições)

```text
src/homologacao_ponto/
├── models/
│   ├── batch_config.py          # MODIFY: adicionar anos ao BatchConfig + loader
│   └── batch_result.py          # MODIFY: adicionar mes/ano ao BatchEntryResult
├── services/
│   ├── batch_service.py         # MODIFY: expandir períodos por entry
│   └── periodo_expander.py      # NEW: PeriodoExpander.expand()
└── infrastructure/
    └── admissao_detector.py     # NEW: AdmissaoDetector.detect() + AdmissaoNaoDetectadaError

tests/
├── unit/
│   ├── test_batch_config_007.py   # NEW: testes de batch_config para anos
│   ├── test_periodo_expander.py   # NEW: testes de PeriodoExpander
│   ├── test_admissao_detector.py  # NEW: testes de AdmissaoDetector
│   └── test_batch_service_007.py  # NEW: testes de BatchService com expansão
├── integration/
│   └── test_batch_end_to_end_007.py  # NEW: end-to-end com anos
└── contract/
    └── test_batch_result_schema_007.py  # NEW: schema com mes/ano
```

**Structure Decision**: Single project, modifica código existente em `models/` e `services/`; adiciona `periodo_expander.py` em `services/` e `admissao_detector.py` em `infrastructure/`.

## Complexity Tracking

Sem violações de constituição.

---

## Phase 0: Research ✓ Completo

Ver [research.md](research.md) — todas as decisões resolvidas:
1. `anos` como `list[int] | str | None` — sem enum
2. `PeriodoExpander` com injeção de `today: date`
3. `AdmissaoDetector` via probe regressivo, 3 falhas consecutivas = parar
4. `BatchEntryResult` com `mes`/`ano` opcionais — backward-compatible
5. Precedência: `anos` > `mes`/`ano`; warning logado quando coexistem
6. Validação de `anos` no loader

---

## Phase 1: Design & Contracts ✓ Completo

### data-model.md ✓
Ver [data-model.md](data-model.md).

### Contratos ✓
- [contracts/batch-config.schema.yaml](contracts/batch-config.schema.yaml) — `anos` como `oneOf: [array, "All"]`
- [contracts/batch-result.schema.json](contracts/batch-result.schema.json) — `mes`/`ano` opcionais por entry

### Mudanças de Schema (backward-compat)

`BatchEntryResult.to_dict()` — campos `mes` e `ano` são omitidos quando `None`. Relatórios legados (006) não incluem esses campos → sem quebra de schema.

`BatchConfig` — campo `anos` é novo e opcional. YAMLs legados sem `anos` continuam funcionando.

---

## Implementation Notes

### BatchConfig (modificação)

```python
@dataclass(frozen=True)
class BatchConfig:
    servidores: list[BatchEntry]
    mes: int | None = None
    ano: int | None = None
    anos: list[int] | str | None = None  # NOVO
```

Loader: após ler `servidores`, lê `data.get("anos")`. Se `isinstance(anos_raw, list)` → valida itens int + range + deduplica + ordena. Se `isinstance(anos_raw, str)` → aceita somente `"All"` (case-insensitive). Vazio → `BatchConfigError`.

### PeriodoExpander

```python
class PeriodoExpander:
    @staticmethod
    def expand(
        config: BatchConfig,
        entry: BatchEntry,
        today: date,
    ) -> list[tuple[int, int]]:
        # retorna lista de (mes, ano) em ordem cronológica
        if config.anos is None:
            mes = entry.mes or config.mes or today.month
            ano = entry.ano or config.ano or today.year
            return [(mes, ano)]
        if isinstance(config.anos, str):  # "All" — delega para caller
            return []  # sinaliza para BatchService usar AdmissaoDetector
        periodos = []
        for ano in sorted(set(config.anos)):
            for mes in range(1, 13):
                if (ano, mes) > (today.year, today.month):
                    break
                periodos.append((mes, ano))
        return periodos
```

### AdmissaoDetector

```python
class AdmissaoNaoDetectadaError(Exception):
    pass

class AdmissaoDetector:
    MAX_ANOS_RETROATIVOS = 30

    def detect(
        self,
        app,
        session,
        entry: BatchEntry,
        today: date,
    ) -> list[tuple[int, int]]:
        # probe regressivo: recua 1 mês por vez até 3 falhas consecutivas
        # retorna lista (mes, ano) dos períodos bem-sucedidos em ordem crescente
```

### BatchService (modificação)

Loop interno muda de `for entry in config.servidores` para:

```python
for entry in config.servidores:
    if isinstance(config.anos, str):  # "All"
        try:
            periodos = AdmissaoDetector().detect(app, session, entry, today)
        except AdmissaoNaoDetectadaError as exc:
            entries.append(BatchEntryResult(..., status="failed", error=str(exc)))
            continue
    else:
        periodos = PeriodoExpander.expand(config, entry, today)
    for (mes, ano) in periodos:
        # lógica existente de _run_single_espelho + retry
        entries.append(BatchEntryResult(..., mes=mes, ano=ano))
```
