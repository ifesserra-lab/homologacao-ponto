# Data Model: Período por Anos no Batch YAML

**Feature**: 007-batch-periodo-anos  
**Date**: 2026-05-23

---

## Entidades Modificadas

### BatchConfig (modificado)

```
BatchConfig
  servidores: list[BatchEntry]     # lista de servidores (obrigatório, ≥1)
  mes:        int | None           # mês padrão; ignorado quando anos presente
  ano:        int | None           # ano único; ignorado quando anos presente
  anos:       list[int] | str | None  # NOVO: lista de anos inteiros ou "All"
```

**Regras de validação** (em `BatchConfigLoader`):
- `anos` como lista → itens devem ser int no intervalo [2000, 2100], sem duplicatas (loader deduplica)
- `anos == "All"` (case-insensitive) → aceito; normalizado para `"All"` uppercase
- `anos == []` → `BatchConfigError("campo 'anos' não pode ser lista vazia")`
- `anos` com string ≠ "All" → `BatchConfigError`
- `anos` presente junto com `mes`/`ano` → aceito; warning logado; `anos` tem precedência

---

### BatchEntry (sem alteração)

```
BatchEntry
  nome:  str           # nome do servidor (obrigatório)
  siape: str           # matrícula SIAPE (obrigatório)
  mes:   int | None    # override de mês por entry (usado somente sem anos)
  ano:   int | None    # override de ano por entry (usado somente sem anos)
```

---

### BatchEntryResult (modificado)

```
BatchEntryResult
  nome:        str           # nome do servidor
  siape:       str           # matrícula SIAPE
  status:      str           # "completed" | "empty" | "failed"
  mes:         int | None    # NOVO: mês do período processado (None = legado)
  ano:         int | None    # NOVO: ano do período processado (None = legado)
  export_path: str | None    # caminho do JSON exportado
  error:       str | None    # mensagem de erro quando status=="failed"
```

**`to_dict()` atualizado**:
```python
{
  "nome": ...,
  "siape": ...,
  "status": ...,
  "mes": ...,      # incluído somente quando não None
  "ano": ...,      # incluído somente quando não None
  "export_path": ...,
  "error": ...,
}
```

---

## Novas Entidades

### Periodo (value object interno)

```
Periodo
  mes: int    # 1–12
  ano: int    # 2000–2100
```

Usado internamente pelo `PeriodoExpander` e `BatchService`; não persistido.

---

## Novos Serviços / Classes

### PeriodoExpander

Responsabilidade: expandir `BatchConfig.anos` + data atual em lista de `Periodo`.

```
PeriodoExpander
  expand(config: BatchConfig, entry: BatchEntry, today: date) -> list[Periodo]
    - se anos ausente:  retorna [Periodo(mes=resolve(entry, config, today), ano=...)]
    - se anos é lista:  retorna [Periodo(m, a) para a em anos para m em 1..12,
                                  excluindo (m, a) > (today.month, today.year)]
    - se anos == "All": delega para AdmissaoDetector
```

---

### AdmissaoDetector

Responsabilidade: detectar o período mais antigo disponível para um servidor via probe regressivo no SIGRH.

```
AdmissaoDetector
  detect(app, session, entry: BatchEntry, today: date) -> list[Periodo]
    - começa em today; recua mês a mês (até limite: 30 anos)
    - chama app._run_single_espelho para cada mês
    - pára ao encontrar 3 falhas consecutivas (exit_code ≠ 0 e ≠ "empty")
    - retorna todos os períodos bem-sucedidos em ordem cronológica crescente
    - lança AdmissaoNaoDetectadaError se nenhum mês bem-sucedido encontrado
```

```
AdmissaoNaoDetectadaError(Exception)
  mensagem de erro padrão: "período de trabalho não detectado"
```

---

## Relacionamentos

```
BatchConfig ──1──< BatchEntry         (lista de servidores)
BatchConfig ────── anos: [2025,2026]  (campo escalar novo)
PeriodoExpander ── lê BatchConfig + BatchEntry → list[Periodo]
AdmissaoDetector ─ usa app + session → list[Periodo]  (só para "All")
BatchService ────── usa PeriodoExpander + AdmissaoDetector
               ──< BatchEntryResult   (um por (entry × periodo))
BatchResult  ────< BatchEntryResult
```
